import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
from selenium.common.exceptions import NoSuchElementException

# 使用 requests.Session() 进行登录
session = requests.Session()

# 登录页面的URL和表单数据
login_url = "https://id.sspu.edu.cn/"
login_data = {
    #本人账号与密码
    "username": "保密",
    "password": "保密"
}
# 提交登录请求
session.post(login_url, data=login_data)

# 设置Edge驱动器的路径
edge_driver_path = 'E:\\EdgeDriver\\edgedriver_win64\\msedgedriver.exe'

# 启动 Selenium，并设置使用Edge浏览器
driver = webdriver.Edge(service=Service(edge_driver_path))

# 访问登录页面以确保能够添加 cookies
driver.get("https://id.sspu.edu.cn/")

# 将 requests.Session() 中的 cookies 导入到 Selenium
for cookie in session.cookies:
    driver.add_cookie({
        'name': cookie.name,
        'value': cookie.value,
        'domain': cookie.domain,
        'path': cookie.path
    })

# 手动完成登录过程
username_input = driver.find_element(By.CSS_SELECTOR, 'input.el-input__inner[type="text"]')
username_input.send_keys(login_data['username'])

password_input = driver.find_element(By.CSS_SELECTOR, 'input.el-input__inner[type="password"]')
password_input.send_keys(login_data['password'])

login_button = driver.find_element(By.CSS_SELECTOR, 'button.el-button.login-btn')
login_button.click()

# 确保登录后网页已经加载，可以添加一个等待时间
time.sleep(2)  # 根据实际情况调整时间
driver.get("https://oa.sspu.edu.cn/wui/index.html")

time.sleep(2)
# 跳转到其他网页
driver.get("https://oa.sspu.edu.cn/interface/Entrance.jsp?id=bzkjw")

time.sleep(2)
driver.get("https://oa.sspu.edu.cn/interface/Entrance.jsp?id=bzkjw")


time.sleep(2)
driver.get("https://jx.sspu.edu.cn/eams/home!index.action")

time.sleep(2)
driver.get("https://jx.sspu.edu.cn/eams/scheduleSearch.action")

# 等待页面加载完成
time.sleep(2)


# 1. 使用 title="学年学期" 来找到学年学期输入框
semester_input = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//input[@title='学年学期']"))
)
semester_input.click()

# 2. 等待学年表格可见并选择学年
year_table = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "semesterCalendar_yearTb"))
)
target_year = WebDriverWait(year_table, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//td[text()='2023-2024']"))
)
target_year.click()

# 3. 等待学期表格可见并选择学期
term_table = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.ID, "semesterCalendar_termTb"))
)
target_term = WebDriverWait(term_table, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//td[@val='902']"))  # 选择秋季学期
)
target_term.click()

# 4. 提交表单切换学期
submit_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='切换学期']"))
)
submit_button.click()

# 等待页面加载新的数据
time.sleep(5)

# 继续获取和处理页面数据
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')


# 获取并处理页面数据
all_courses = []

while True:
    # 获取当前页面的源代码并解析
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # 查找课程数据表格
    course_rows = []
    indexpanel = soup.find('table', class_='indexpanel')
    if indexpanel:
        td_element = soup.find('td', class_='index_content')
        if td_element:
            content_div = td_element.find('div', id='contentDiv', class_='_ajax_target')
            if content_div:
                grid_div = content_div.find('div', class_='grid')
                if grid_div:
                    table = grid_div.find('table', class_='gridtable')
                    if table:
                        tbody = table.find('tbody')
                        course_rows = tbody.find_all('tr') if tbody else table.find_all('tr')
                    else:
                        print("Table not found within gridbar div.")
                else:
                    print("Grid div not found.")
            else:
                print("Content div not found.")
        else:
            print("Index content td not found.")
    else:
        print("indexpanel td not found.")

    # 解析并保存每行课程数据
    for row in course_rows:
        cells = row.find_all('td')
        if len(cells) > 13:  # 确保单元格数足够
            schedule_cell = cells[5]  # 排课安排的单元格
            schedules = schedule_cell.get_text(separator='|').split('|')  # 使用'|'作为分隔符来分割每个排课安排
            schedule_details = [schedule.strip() for schedule in schedules if schedule.strip()]  # 清理空格
            course_info = {
                "序号": cells[1].text.strip(),
                "课程代码": cells[2].text.strip(),
                "课程名称": cells[3].find('a').text.strip() if cells[3].find('a') else cells[3].text.strip(),
                "教师": cells[4].text.strip(),
                "排课安排": schedule_details,  # 保存排课安排列表
                "课程类别": cells[6].text.strip(),
                "教学班": cells[7].text.strip(),
                "实际人数": cells[8].text.strip(),
                "上限": cells[9].text.strip(),
                "课时": cells[10].text.strip(),
                "学分": cells[11].text.strip(),
                "起始周": cells[12].text.strip(),
                "周数": cells[13].text.strip()
            }
            all_courses.append(course_info)

    # 查找下一页按钮并点击，如果不可点击则退出循环
    try:
        next_page = driver.find_element(By.LINK_TEXT, '后页 ›')
        if 'disabled' in next_page.get_attribute('class'):
            break
        next_page.click()
        time.sleep(2)  # 等待页面加载
    except:
        break

# 将数据存储到 DataFrame 中
df_courses = pd.DataFrame(all_courses)

df_courses.to_excel('2025courses_schedule.xlsx',index=False, sheet_name='课程表')

# 关闭浏览器
driver.quit()