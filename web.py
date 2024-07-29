import random
import logging
from typing import Union, Any
from datetime import datetime
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC

# initialize logger
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class ReservationForm():
    wed_date:str
    wed_time:str
    m_name:str
    m_phone:str
    w_name:str
    w_phone:str
    m_email:str
    w_email:str
    extra_info:Union[str, None] = None
    
    def __post_init__(self):
        now = datetime.now()
        web_date = datetime.strptime(self.wed_date, "%Y-%m-%d")
        if web_date < now or web_date.weekday() < 5:
            raise ValueError(f"Wedding date `{web_date}` is earlier than today, or is not the weekend.")
    
def safe_click(
    driver:webdriver.Chrome,
    way:Any,
    selector:str,
    timeout:int=5
) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (way, selector)
        )
    ).click()    

def safe_submit(
    driver:webdriver.Chrome,
    way:Any,
    selector:str,
    value:str,
    timeout:int=5
) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (way, selector)
        )
    ).send_keys(value)

def fill_reservation_form(driver:webdriver.Chrome, form: ReservationForm) -> None:
    safe_submit(driver, By.CSS_SELECTOR, "input#name.frm_ipt.frm_50", form.m_name)
    safe_submit(driver, By.CSS_SELECTOR, "input#phone.frm_ipt.frm_50", form.m_phone)
    safe_click(driver, By.CSS_SELECTOR, "input.sexChk")
    safe_submit(driver, By.CSS_SELECTOR, "input#name_spouse.frm_ipt.frm_50", form.w_name)
    safe_submit(driver, By.CSS_SELECTOR, "input#phone_spouse.frm_ipt.frm_50", form.w_phone)
    safe_submit(driver, By.CSS_SELECTOR, "input#email.frm_ipt.frm_100", form.m_email)
    safe_submit(driver, By.CSS_SELECTOR, "input#email_spouse.frm_ipt.frm_100", form.w_email)
    safe_submit(driver, By.CSS_SELECTOR, "textarea#od_memo.txt_ipt", form.extra_info)
    
# list of User-Agent
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1"
]
user_agent = random.choice(user_agents)
chrome_options = Options()

# avoid CAPTCHA
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)
# turn on secret mode
chrome_options.add_argument('incognito') 
# set user_agent
chrome_options.add_argument(f"--user-agent={user_agent}")

# initialize the webdriver
driver = webdriver.Chrome(options=chrome_options)

# set window_size
driver.maximize_window()

# wedding reservation url
URL = 'https://snufacultyclub.com/page.php?pgid=wedding3'
driver.get(URL)
user_agent = driver.execute_script("return navigator.userAgent")
logging.info(f"User-agent: {user_agent}")

# reservation information
# ****** 반드시 아래 포맷에 맞추어서 입력하기 ******
# wed_date: 결혼식 날짜. 미래 날짜여야하며, 주말만 입력 가능
# wed_time: 결혼식 시간. 반드시 숫자만 입력. (1부: 11:00; 2부: 13:00; 3부: 15:00; 4부: 17:00; 5부: 18:30)
# m_name/w_name: 신랑/신부 이름
# m_phone/w_phone: 신랑/신부 번호
# m_email/w_email: 신랑/신부 이메일
# extra_info: 추가 입력 사항 (ex. 야외진행)
form = ReservationForm(
    wed_date="2025-08-02",
    wed_time="5",
    m_name="로미오",
    m_phone="0101111111",
    m_email="romio@gmail.com",
    w_name="줄리엣",
    w_phone="0101111111",
    w_email="juliet@gmail.com",
    extra_info=""
)

# 개인정보 동의 & 페이지 이동
safe_click(driver, By.NAME, "chk1")
safe_click(driver, By.NAME, "chk2")
safe_click(driver, By.CSS_SELECTOR, "button.fill")

# 개인정보 입력
fill_reservation_form(driver, form)

# 날짜선택
wed_date = datetime.strptime(form.wed_date, "%Y-%m-%d")
year, month, day = str(wed_date.year), str(wed_date.month), str(wed_date.day)
safe_click(driver, By.CSS_SELECTOR, "input#day.frm_ipt.frm_100.snu_chk.hasDatepicker")

Select(driver.find_element(By.CSS_SELECTOR, "select.ui-datepicker-year")).select_by_value(year)
Select(driver.find_element(By.CSS_SELECTOR, "select.ui-datepicker-month")).select_by_value(str(int(month)-1)) # from 0
safe_click(driver, By.XPATH, f"//td/a[text()='{day}']")

# 시간선택
Select(driver.find_element(By.CSS_SELECTOR, "select.frm_select.snu_chk")).select_by_value(form.wed_time)

# 정보 제출
safe_click(driver, By.CSS_SELECTOR, "button.btn_submit")
driver.quit()