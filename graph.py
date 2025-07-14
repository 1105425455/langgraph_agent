from dotenv import load_dotenv
import os

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import State
import json
import logging
from typing import Annotated, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from state import State
from prompts import *
from tools import *


llm = ChatOpenAI(
model_name="qwen-max",
api_key=os.getenv("api_key"),
base_url=os.getenv("base_url"),
temperature=1
#top_p=0.9
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
hander = logging.StreamHandler()
hander.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
hander.setFormatter(formatter)
logger.addHandler(hander)
process = {}


def extract_json(text):
    if '```json' not in text:
        return text
    text = text.split('```json')[1].split('```')[0].strip()
    return text

def extract_answer(text):
    if '</think>' in text:
        answer = text.split("</think>")[-1]
        return answer.strip()
    
    return text

def create_planner_node(state: State):
    logger.info("***正在运行Create Planner node***")
    messages = [SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(content=PLAN_CREATE_PROMPT.format(user_message = state['user_message']))]
    response = llm.invoke(messages)
    plan = json.loads(extract_json(response.content))
    process['Create Planner node plan'] = plan
    state['messages'] += [AIMessage(content=json.dumps(plan, ensure_ascii=False))]
    return Command(goto="execute", update={"plan": plan})

def update_planner_node(state: State):
    logger.info("***正在运行Update Planner node***")
    plan = state['plan']
    goal = plan['goal']
    state['messages'].extend([SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(content=UPDATE_PLAN_PROMPT.format(plan = plan, goal=goal))])
    messages = state['messages']
    while True:
        try:
            response = llm.invoke(messages)
            plan = json.loads(extract_json(response.content))
            state['messages']+=[AIMessage(content=json.dumps(plan, ensure_ascii=False))]
            return Command(goto="execute", update={"plan": plan})
        except Exception as e:
            messages += [HumanMessage(content=f"json格式错误:{e}")]
            
def execute_node(state: State):
    logger.info("***正在运行execute_node***")
  
    plan = state['plan']
    steps = plan['steps']
    current_step = None
    current_step_index = 0
    
    for i, step in enumerate(steps):
        if step['status'] == 'pending':
            current_step = step
            current_step_index = i
            break
        
    logger.info(f"当前执行STEP:{current_step}")
    
    if current_step is None or current_step_index == len(steps) - 1:
        return Command(goto='report')
    
    # 准备本次执行的初始消息
    messages = state.get('observations', []) + [
        SystemMessage(content=EXECUTE_SYSTEM_PROMPT),
        HumanMessage(content=EXECUTION_PROMPT.format(user_message=state['user_message'], step=current_step['description']))
    ]
    
    # 记录本次执行产生的消息，以便后续更新到 state
    newly_generated_messages = []
    process[f'execute result {current_step_index}'] = []
    llm_with_tools = llm.bind_tools([create_file, str_replace, shell_exec])
    while True:
        # 1. 调用 LLM
        response_msg = llm_with_tools.invoke(messages)
        process[f'execute result {current_step_index}'].append(response_msg)
        # 2. 立刻将 LLM 的回复加入消息历史
        messages.append(response_msg)
        newly_generated_messages.append(response_msg)
        # 3. 如果没有工具调用，则退出循环
        if not response_msg.tool_calls:
            break
        
        # 4. 如果有工具调用，则执行
        tools = {"create_file": create_file, "str_replace": str_replace, "shell_exec": shell_exec}
        for tool_call in response_msg.tool_calls:
            tool_result = tools[tool_call['name']].invoke(tool_call['args'])
            logger.info(f"tool_name:{tool_call['name']},tool_args:{tool_call['args']}\ntool_result:{tool_result}")
            
            # 5. 将工具结果作为 ToolMessage 加入消息历史
            tool_message = ToolMessage(content=str(tool_result), tool_call_id=tool_call['id'])
            messages.append(tool_message)
            newly_generated_messages.append(tool_message)
    summary = extract_answer(messages[-1].content)
    logger.info(f"当前STEP执行总结:{summary}")
    # 将本次执行产生的所有新消息（包括AI回复和工具结果）加入 state
    state['messages'].extend(newly_generated_messages)
    state['observations'].extend(newly_generated_messages)
    
    return Command(goto='update_planner', update={'plan': plan})
    

    
def report_node(state: State):
    logger.info("***正在运行report_node***")
    observations = state.get("observations", [])
    messages = observations + [SystemMessage(content=REPORT_SYSTEM_PROMPT)]
    newly_generated_messages = []
    tools = {"create_file": create_file, "shell_exec": shell_exec}
    llm_with_tools = llm.bind_tools([create_file, shell_exec])

    while True:
        # 1. LLM 回复
        response_msg = llm_with_tools.invoke(messages)
        messages.append(response_msg)
        newly_generated_messages.append(response_msg)
        # 2. 没有 tool_calls 就退出
        if not response_msg.tool_calls:
            break
        # 3. 有 tool_calls 就执行
        for tool_call in response_msg.tool_calls:
            try:
                tool_result = tools[tool_call['name']].invoke(tool_call['args'])
            except Exception as e:
                tool_result = f"工具调用出错: {e}"
            logger.info(f"tool_name:{tool_call['name']},tool_args:{tool_call['args']}\ntool_result:{tool_result}")
            tool_message = ToolMessage(content=str(tool_result), tool_call_id=tool_call['id'])
            messages.append(tool_message)
            newly_generated_messages.append(tool_message)

    # 取最后一条 AI 回复内容作为报告
    final_report = messages[-1].content
    process['report'] = final_report
    try:
        with open('process.json','w',encoding='utf-8') as f:
            json.dump(process, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(e)
    return {"final_report": final_report}



def build_graph():
    memory = MemorySaver()
    builder = StateGraph(State)
    builder.add_edge(START, "create_planner")
    builder.add_node("create_planner", create_planner_node)
    builder.add_node("update_planner", update_planner_node)
    builder.add_node("execute", execute_node)
    builder.add_node("report", report_node)
    builder.add_edge("report", END)
    return builder.compile(checkpointer=memory)

if __name__ == "__main__":
    graph = build_graph()
    inputs = {"user_message": "对所给文档进行简单分析，生成简单分析报告，文档路径./yonbin/agent/计算机视觉.docx", 
            "plan": None,
            "observations": [], 
            "final_report": ""}

    graph.invoke(inputs, {"recursion_limit":100,
                          "thread_id": "test-thread-001"})