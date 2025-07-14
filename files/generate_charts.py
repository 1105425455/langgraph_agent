import pandas as pd
import matplotlib.pyplot as plt
import os

# 读取CSV文件
file_path = './files/sales_data.csv'
data = pd.read_csv(file_path)

def plot_trend(data, column, title, ylabel, figure_name):
    plt.figure(figsize=(10, 6))
    plt.plot(data['Month'], data[column], marker='o', linestyle='-')
    plt.title(title, fontsize=16)
    plt.xlabel('Month', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(figure_name)
    plt.close()

# 确保figures目录存在
output_dir = './files/figures'
os.makedirs(output_dir, exist_ok=True)

# 生成销售额随时间变化图
plot_trend(data, 'Revenue(万元)', 'Sales Trend Over Time', 'Revenue (万元)', f'{output_dir}/sales_trend.png')

# 生成访问量随时间变化图
plot_trend(data, 'Visits(人次)', 'Website Visits Over Time', 'Visits (人次)', f'{output_dir}/visits_trend.png')

# 生成转化率随时间变化图
plot_trend(data, 'Conversion_Rate(%)', 'Conversion Rate Over Time', 'Conversion Rate (%)', f'{output_dir}/conversion_rate_trend.png')