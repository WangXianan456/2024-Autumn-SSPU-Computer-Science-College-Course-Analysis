from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
import pandas as pd
import plotly.express as px
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re


from plotly import graph_objects as go
from fastapi.responses import HTMLResponse
import plotly.express as px

file_path = 'static/excels/2024-2025秋季学期计信学院上课信息表.xlsx'
df = pd.read_excel(file_path)

app = FastAPI()

# 定义模板目录
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/teacher_workload", response_class=HTMLResponse)
async def teacher_workload():
    # 过滤掉教师名为 "[]" 的记录
    df_filtered = df[df['教师'] != '[]']

    # 统计每位教师的课程数量（即名字出现的次数）
    teacher_count = df_filtered.groupby('教师').size().reset_index(name='课程数量')

    # 使用 Plotly 生成柱状图
    fig = px.bar(teacher_count, x='教师', y='课程数量', title='教师课程数量分析')

    # 将x轴的标签倾斜45度
    fig.update_layout(xaxis=dict(tickangle=-45))

    # 将教师的课程数量按区间分类
    bins = [1, 2, 3, 4, 5, 6, float('inf')]  # 定义区间
    labels = ['1', '2', '3', '4', '5', '6']  # 定义标签
    teacher_count['课程数量分类'] = pd.cut(teacher_count['课程数量'], bins=bins, labels=labels, right=False)

    # 统计每个分类中的教师数量
    workload_distribution = teacher_count['课程数量分类'].value_counts(normalize=False).reset_index()
    workload_distribution.columns = ['课时数量', '教师数量']

    # 计算每个分类的占比
    workload_distribution['教师占比'] = workload_distribution['教师数量'] / workload_distribution['教师数量'].sum()

    # 生成饼图展示课时数量占比
    pie_fig = px.pie(workload_distribution, names='课时数量', values='教师占比', title='教师课时数量占比 - 饼图')

    # 自定义悬停显示模板，显示教师数量和占比
    pie_fig.update_traces(hovertemplate='课时数量: %{label}<br>教师数量: %{customdata[0]}<br>占比: %{percent}')

    # 添加自定义数据用于悬停显示教师数量
    pie_fig.update_traces(customdata=workload_distribution[['教师数量']])

    # 返回图表的 HTML 内容
    response_content = fig.to_html(full_html=False) + pie_fig.to_html(full_html=False)
    return HTMLResponse(content=response_content)

@app.get("/course_category_distribution", response_class=HTMLResponse)
async def course_category_distribution():
    category_count = df['课程类别'].value_counts().reset_index()
    category_count.columns = ['课程类别', '数量']

    # 柱状图
    bar_fig = px.bar(category_count, x='课程类别', y='数量', title='课程类别分布 - 柱状图')

    # 饼图
    pie_fig = px.pie(category_count, names='课程类别', values='数量', title='课程类别分布 - 饼图')

    return HTMLResponse(bar_fig.to_html(full_html=False) + pie_fig.to_html(full_html=False))


@app.get("/foundation_course_comparison", response_class=HTMLResponse)
async def foundation_course_comparison():
    foundation_courses = df[df['课程类别'] == '公共基础课']
    course_count = foundation_courses['课程名称'].value_counts().reset_index()
    course_count.columns = ['课程名称', '数量']

    bar_fig = px.bar(course_count, x='课程名称', y='数量', title='公共基础课的课程数量比较 - 条形图')
    pie_fig = px.pie(course_count, names='课程名称', values='数量', title='公共基础课数量占比 - 扇形图')

    return HTMLResponse(bar_fig.to_html(full_html=False) + pie_fig.to_html(full_html=False))



@app.get("/course_name_wordcloud", response_class=HTMLResponse)
async def course_name_wordcloud():
    # 确保 df['课程名称'] 已正确加载并包含中文课程名称
    course_names = ' '.join(df['课程名称'].unique())

    # 指定中文支持的字体路径
    font_path ='C:\Windows\Fonts\simhei.ttf'

    # 生成词云，这里指定字体路径
    wordcloud = WordCloud(width=800, height=400, font_path=font_path, max_font_size=100, max_words=200).generate(
        course_names)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")

    # 保存图片到静态文件路径
    plt.savefig("static/wordcloud.png")

    # 读取并返回图片内容
    with open("static/wordcloud.png", "rb") as image_file:
        return HTMLResponse(image_file.read(), media_type="image/png")

@app.get("/credits_vs_weeks", response_class=HTMLResponse)
async def credits_vs_weeks():
    # 散点图1: 课程时间 vs 学分
    scatter_fig1 = px.scatter(df, x='周数', y='学分', title='课程时间与学分关系',
                              labels={'周数': '课程时间（周）', '学分': '学分'},
                              trendline="ols")  # 添加趋势线

    # 散点图2: 课程时间 vs 课时
    scatter_fig2 = px.scatter(df, x='周数', y='课时', title='课程时间与课时关系',
                              labels={'周数': '课程时间（周）', '课时': '课时'},
                              trendline="ols")  # 添加趋势线

    # 散点图3: 课时 vs 学分
    scatter_fig3 = px.scatter(df, x='课时', y='学分', title='课时与学分关系',
                              labels={'课时': '课时', '学分': '学分'},
                              trendline="ols")  # 添加趋势线

    # 返回合并的三个图表
    return HTMLResponse(
        scatter_fig1.to_html(full_html=False) + scatter_fig2.to_html(full_html=False) + scatter_fig3.to_html(
            full_html=False))


@app.get("/credits_distribution_3d", response_class=HTMLResponse)
async def credits_distribution_3d():
    # 原有的计算学分与课时、课程数量之间的分布
    grouped = df.groupby('学分').agg(总课时=pd.NamedAgg(column='课时', aggfunc='sum'),
                                   课程数量=pd.NamedAgg(column='课时', aggfunc='count'))

    # 计算平均课时
    grouped['平均课时'] = grouped['总课时'] / grouped['课程数量']

    # 三维图1: 平均课时 vs 学分 vs 课程数量
    fig1 = go.Figure(data=[go.Scatter3d(
        x=grouped.index,  # 学分
        y=grouped['课程数量'],  # 课程数量
        z=grouped['平均课时'],  # 平均课时
        mode='markers',
        marker=dict(size=5, color=grouped.index, colorscale='Viridis', opacity=0.8)
    )])

    fig1.update_layout(title='课程学分、课程数量和平均课时的三维分布', scene=dict(
        xaxis_title='学分',
        yaxis_title='课程数量',
        zaxis_title='平均课时'
    ))

    # 新增：展示每个课程的学分、课时和课程数量的分布
    fig2 = go.Figure(data=[go.Scatter3d(
        x=df['学分'],  # 学分
        y=df['课时'],  # 课时
        z=df.index,  # 每门课程的索引（或者你可以换成其他标识符，比如课程ID）
        mode='markers',
        marker=dict(size=5, color=df['学分'], colorscale='Bluered', opacity=0.8)
    )])

    fig2.update_layout(title='所有课程的学分、课时和索引的三维分布', scene=dict(
        xaxis_title='学分',
        yaxis_title='课时',
        zaxis_title='课程数量'
    ))

    # 返回两个三维图
    return HTMLResponse( fig2.to_html(full_html=False)+fig1.to_html(full_html=False) )



@app.get("/weekly_course_distribution", response_class=HTMLResponse)
async def weekly_course_distribution():
    # 定义要查找的星期几关键词
    week_days = ['星期一', '星期二', '星期三', '星期四', '星期五']

    # 创建一个空的字典来存储每个星期几的课程数量
    week_count = {day: 0 for day in week_days}

    # 遍历每一行并统计每个星期几的课程数量
    for schedule in df['排课安排']:
        for day in week_days:
            week_count[day] += len(re.findall(day, schedule))

    # 将统计结果转换为 DataFrame
    week_count_df = pd.DataFrame(list(week_count.items()), columns=['时间', '课程数量'])

    # 创建柱状图和折线图
    bar_fig = px.bar(week_count_df, x='时间', y='课程数量', title='周几的课最多 - 柱状图')
    line_fig = px.line(week_count_df, x='时间', y='课程数量', title='周几的课最多 - 折线图')

    # 返回合并的图表 HTML
    return HTMLResponse(bar_fig.to_html(full_html=False) + line_fig.to_html(full_html=False))


@app.get("/course_capacity", response_class=HTMLResponse)
async def course_capacity():
    df['差值'] = df['上限'] - df['实际人数']
    full_capacity_count = (df['差值'] == 0).sum()
    non_full_capacity_count = (df['差值'] != 0).sum()

    data = {'状态': ['满员', '未满员'], '数量': [full_capacity_count, non_full_capacity_count]}
    pie_fig = px.pie(pd.DataFrame(data), names='状态', values='数量', title='满员与未满员课程比例')

    return HTMLResponse(pie_fig.to_html(full_html=False))



@app.get("/profession_comparison", response_class=HTMLResponse)
async def profession_comparison():
    # 定义专业关键词列表
    professions = [
        '计算机科学与技术', '网络工程', '软件工程', '数字媒体技术',
        '智能科学与技术', '数据科学与大数据技术', '电子信息工程', '通信工程'
    ]

    # 定义提取专业的函数
    def extract_profession(text):
        for profession in professions:
            if profession in text:
                return profession
        return '未知'

    # 提取每个教学班中的专业
    df['专业'] = df['教学班'].apply(lambda x: extract_profession(str(x)))

    # 过滤掉无法识别的专业
    df_filtered = df[df['专业'] != '未知']

    # 计算每个专业的总学分和总课时
    profession_data = df_filtered.groupby('专业').agg({'学分': 'sum', '课时': 'sum'}).reset_index()

    # 对学分数据从小到大排序
    profession_data_sorted_credits = profession_data.sort_values(by='学分', ascending=True)

    # 创建玫瑰图，用于显示各专业的总学分比例
    rose_fig_credits = go.Figure(go.Pie(
        labels=profession_data_sorted_credits['专业'],  # 专业名称
        values=profession_data_sorted_credits['学分'],  # 学分数
        hole=0.4,  # 中心空洞大小，类似环形图效果
        sort=False,  # 不排序
        direction='clockwise',  # 顺时针排列
        marker=dict(
            colors=px.colors.qualitative.Pastel,  # 使用柔和的颜色
            line=dict(color='#FFFFFF', width=2)  # 扇形之间的分隔线
        ),
        textinfo='label+value',  # 显示标签和学分数
        pull=[0.1 if x == max(profession_data_sorted_credits['学分']) else 0 for x in profession_data_sorted_credits['学分']],  # 突出显示最大值
    ))

    # 设置布局
    rose_fig_credits.update_layout(
        title='各专业学分比例 - 玫瑰图',
        annotations=[dict(text='学分', x=0.5, y=0.5, font_size=20, showarrow=False)],  # 中心文字
        showlegend=True,  # 显示图例
        legend=dict(orientation='h', x=0.5, y=-0.1, xanchor='center')  # 图例位置
    )

    # 对课时数据从小到大排序
    profession_data_sorted_hours = profession_data.sort_values(by='课时', ascending=True)

    # 创建玫瑰图，用于显示各专业的总课时比例
    rose_fig_hours = go.Figure(go.Pie(
        labels=profession_data_sorted_hours['专业'],  # 专业名称
        values=profession_data_sorted_hours['课时'],  # 课时数
        hole=0.4,  # 中心空洞大小
        sort=False,  # 不排序
        direction='clockwise',  # 顺时针排列
        marker=dict(
            colors=px.colors.qualitative.Set3,  # 使用不同颜色
            line=dict(color='#FFFFFF', width=2)  # 分隔线
        ),
        textinfo='label+value',  # 显示标签和课时数
        pull=[0.1 if x == max(profession_data_sorted_hours['课时']) else 0 for x in profession_data_sorted_hours['课时']],  # 突出最大值
    ))

    # 设置布局
    rose_fig_hours.update_layout(
        title='各专业课时比例 - 玫瑰图',
        annotations=[dict(text='课时', x=0.5, y=0.5, font_size=20, showarrow=False)],  # 中心文字
        showlegend=True,  # 显示图例
        legend=dict(orientation='h', x=0.5, y=-0.1, xanchor='center')  # 图例位置
    )

    # 返回合并后的图表
    return HTMLResponse(rose_fig_credits.to_html(full_html=False) + rose_fig_hours.to_html(full_html=False))

@app.get("/profession_course_distribution", response_class=HTMLResponse)
async def profession_course_distribution():
    # 定义专业关键词列表
    professions = [
        '计算机科学与技术', '网络工程', '软件工程', '数字媒体技术',
        '智能科学与技术', '数据科学与大数据技术', '电子信息工程', '通信工程'
    ]

    # 定义提取专业的函数
    def extract_professions(text, professions):
        found = []
        for profession in professions:
            if re.search(profession, text):
                found.append(profession)
        return found

    # 提取每个教学班中的专业
    df['专业'] = df['教学班'].apply(lambda x: extract_professions(str(x), professions))

    # 将提取的专业展平，并统计每个专业的课程数量
    profession_count = df.explode('专业')['专业'].value_counts().reset_index()
    profession_count.columns = ['专业', '数量']

    # 创建柱状图和玫瑰图
    bar_fig = px.bar(profession_count, x='专业', y='数量', title='专业课程数量比较 - 柱状图')
    rose_fig = px.pie(profession_count, names='专业', values='数量', title='专业课程数量占比 - 饼图')

    # 返回 HTML 格式的图表
    return HTMLResponse(bar_fig.to_html(full_html=False) + rose_fig.to_html(full_html=False))


@app.get("/digital_media_course_analysis", response_class=HTMLResponse)
async def big_data_profession_analysis(profession: str = '数字媒体技术'):
    # 过滤出该专业的课程数据科学与大数据技术
    profession_courses = df[df['教学班'].str.contains(profession)]

    # 1. 课程类别分布分析
    category_count = profession_courses['课程类别'].value_counts().reset_index()
    category_count.columns = ['课程类别', '数量']

    # 生成柱状图和饼图
    category_bar_fig = px.bar(category_count, x='课程类别', y='数量', title=f'{profession} 专业课程类别分布 - 柱状图')
    category_pie_fig = px.pie(category_count, names='课程类别', values='数量', title=f'{profession} 专业课程类别分布 - 饼图')

    # 2. 课程的每周分布分析
    # 定义要查找的星期几关键词
    week_days = ['星期一', '星期二', '星期三', '星期四', '星期五']

    # 创建一个空的字典来存储每个星期几的课程数量
    week_count = {day: 0 for day in week_days}

    # 遍历每一行并统计每个星期几的课程数量
    for schedule in profession_courses['排课安排']:
        for day in week_days:
            week_count[day] += len(re.findall(day, schedule))

    # 将统计结果转换为 DataFrame
    week_count_df = pd.DataFrame(list(week_count.items()), columns=['周几', '课程数量'])

    # 生成柱状图和折线图
    week_bar_fig = px.bar(week_count_df, x='周几', y='课程数量', title=f'{profession} 专业课程每周分布 - 柱状图')
    week_line_fig = px.line(week_count_df, x='周几', y='课程数量', title=f'{profession} 专业课程每周分布 - 折线图')

    # 返回所有图表
    return HTMLResponse(
        category_bar_fig.to_html(full_html=False) +
        category_pie_fig.to_html(full_html=False) +
        week_bar_fig.to_html(full_html=False) +
        week_line_fig.to_html(full_html=False)
    )

@app.get("/class_size_comparison", response_class=HTMLResponse)
async def class_size_comparison():
    military_course = df[df['课程名称'] == '军事技能']
    class_sizes = military_course.groupby('教学班')['上限'].sum().reset_index()

    bar_fig = px.bar(class_sizes, x='教学班', y='上限', title='2024级各班人数比较 - 柱状图')
    pie_fig = px.pie(class_sizes, names='教学班', values='上限', title='2024级各班人数占比 - 扇形图')

    return HTMLResponse(bar_fig.to_html(full_html=False) + pie_fig.to_html(full_html=False))



@app.get("/big_data_profession_analysis", response_class=HTMLResponse)
async def big_data_profession_analysis(profession: str = '数据科学与大数据技术'):
    # 过滤出该专业的课程
    profession_courses = df[df['教学班'].str.contains(profession)]

    # 1. 课程类别分布分析
    category_count = profession_courses['课程类别'].value_counts().reset_index()
    category_count.columns = ['课程类别', '数量']

    # 生成柱状图和饼图
    category_bar_fig = px.bar(category_count, x='课程类别', y='数量', title=f'{profession} 专业课程类别分布 - 柱状图')
    category_pie_fig = px.pie(category_count, names='课程类别', values='数量', title=f'{profession} 专业课程类别分布 - 饼图')

    # 2. 课程的每周分布分析
    # 定义要查找的星期几关键词
    week_days = ['星期一', '星期二', '星期三', '星期四', '星期五']

    # 创建一个空的字典来存储每个星期几的课程数量
    week_count = {day: 0 for day in week_days}

    # 遍历每一行并统计每个星期几的课程数量
    for schedule in profession_courses['排课安排']:
        for day in week_days:
            week_count[day] += len(re.findall(day, schedule))

    # 将统计结果转换为 DataFrame
    week_count_df = pd.DataFrame(list(week_count.items()), columns=['周几', '课程数量'])

    # 生成柱状图和折线图
    week_bar_fig = px.bar(week_count_df, x='周几', y='课程数量', title=f'{profession} 专业课程每周分布 - 柱状图')
    week_line_fig = px.line(week_count_df, x='周几', y='课程数量', title=f'{profession} 专业课程每周分布 - 折线图')

    # 返回所有图表
    return HTMLResponse(
        category_bar_fig.to_html(full_html=False) +
        category_pie_fig.to_html(full_html=False) +
        week_bar_fig.to_html(full_html=False) +
        week_line_fig.to_html(full_html=False)
    )