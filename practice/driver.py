import time
from pprint import pprint
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

# -------------------------------
# 1. Initial settings
# -------------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)

# set window size
driver.maximize_window()

# -------------------------------
# 2. Get contents
# -------------------------------
driver.get('https://www.google.co.kr/')

# wait for n seconds until page loading is over; otherwise raise TimeoutError
driver.implicitly_wait(10) 

# get information
print(f"----session_id----\n{driver.session_id}")
print(f"----title----\n{driver.title}")
print(f"----url----\n{driver.current_url}")
print(f"----cookies----\n{driver.get_cookies()}")
print(f"----page_source----\n{driver.page_source}")

# find element by XPATH
search_box = driver.find_element(By.XPATH, '//*[@id="APjFqb"]')
search_box.send_keys('Python')

# send keys (post data to driver)
search_box.send_keys(Keys.RETURN) # search_box.submit()

# save screenshot as .png
driver.save_screenshot("./shot.png")

# quit driver
driver.quit()
del driver

# explicitly sleep 5 seconds to do the next crawling job
time.sleep(5)

# -------------------------------------------
# 3. Crawl prod list from danawa (pagination)
# -------------------------------------------
driver = webdriver.Chrome()
driver.maximize_window()
driver.get('http://prod.danawa.com/list/?cate=112758&15main_11_02')
driver.implicitly_wait(5)
WebDriverWait(driver, 5).until(
    EC.presence_of_element_located(
        (By.XPATH, '//*[@id="danawa_content"]/div[7]/div/div[2]/ul/li[2]/a')
    )
).click()
driver.implicitly_wait(5)

product_names = []

delay = 5
start, end = 1, 5
while start <= end:
    
    print(f"******* Crawl page {start} *******")
    
    # parse page source using soup
    soup = BeautifulSoup(driver.page_source, "lxml")

    # get products
    products = soup.select('div.main_prodlist.main_prodlist_list > ul > li')
    
    _product_names = []
    for product in products:
        # filter items which are advertisements
        if not "prod_ad_item" in product.attrs["class"]:
            _product_names += [
                product.select_one('p.prod_name > a').text.strip()
            ]
    product_names += [{str(start): _product_names}]
    
    # pagination
    start += 1
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, f'//*[@id="productListArea"]/div[3]/div/div/a[{start}]')
        )
    ).click()
    
    # wait until the visibility of all elements located is on
    try:
        product_contents = WebDriverWait(driver, delay).until(
            EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, 'div.main_prodlist.main_prodlist_list > ul > li')
            )
        )
        print (f"Next Page: {start} is ready!")
    except TimeoutException:
        print ("Loading took too much time! Increase the seconds of delay.")
    
pprint(product_names)
driver.quit()

