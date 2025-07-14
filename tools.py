from langchain_core.tools import tool
import os
import subprocess

@tool
def create_file(file_name, file_contents):
    """
    在指定的工作区路径下创建一个新的文件，并填入提供的内容。
    
    args:
        file_name (str): 文件名
        file_contents (str): 文件内容
    """
    try:

        file_path = os.path.join(os.getcwd(), file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w') as file:
            file.write(file_contents)

        return {
            "message": f"Successfully created file at {file_path}"
        }

    except Exception as e:
        return {
            "error": str(e)
        }

@tool
def str_replace(file_name, old_str, new_str):
    """
    在指定的工作区路径下，将文件中的指定文本替换为新的文本。
    
    args:
        file_name (str): 目标文件名
        old_str (str): 要替换的文本
        new_str (str): 新的文本
    """
    try:
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "r") as file:
            content = file.read()

        new_content = content.replace(old_str, new_str, 1)
        
        with open(file_path, "w") as file:
            file.write(new_content)

        return {"message": f"Successfully replaced '{old_str}' with '{new_str}' in {file_path}"}
    except Exception as e:
        return {"error": f"Error replacing '{old_str}' with '{new_str}' in {file_path}: {str(e)}"}

@tool
def send_message(message: str):
    """
    向用户发送消息。
    
    args:
        message: the message to send to the user
    """
    
    return message

@tool
def shell_exec(command: str) -> dict:
    """
    在指定的 shell 会话中执行命令。

    参数:
        command (str): 要执行的 shell 命令

    返回:
        dict: 包含以下字段：
            - stdout: 命令的标准输出
            - stderr: 命令的标准错误
    """
  
    try:
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,          
            cwd=os.getcwd(),        
            capture_output=True,
            text=True,    
            check=False
        )

        # 返回结果
        return {"message":{"stdout": result.stdout,"stderr": result.stderr}}

    except Exception as e:
        return {"error":{"stderr": str(e)}}