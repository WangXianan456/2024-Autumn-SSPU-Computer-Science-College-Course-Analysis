import pandas as pd

# 读取 Excel 文件
file_path = 'static/excels/2025courses_schedule.xlsx'  # 请确保使用正确的文件路径
df = pd.read_excel(file_path)

# 删除课程名称为“研究生系统接口占用课程”的行
df_filtered = df[df['课程名称'] != '研究生系统接口占用课程']

# 定义计信学院专业列表
cs_department_majors = [

        '计算机科学与技术', '网络工程', '软件工程', '数字媒体技术',
        '智能科学与技术', '数据科学与大数据技术', '电子信息工程', '通信工程'

]

# 筛选出属于计信学院的专业数据
filtered_df = df[df['教学班'].isin(cs_department_majors)]

# 保存筛选后的数据到新的 Excel 文计信学院上课信息表件
output_file_path = 'static/excels/2024-2025秋季学期计信学院上课信息表.xlsx'  # 输出文件路径
filtered_df.to_excel(output_file_path, index=False)

print(f"数据已保存到 {output_file_path}")