from __future__ import annotations

import requests
import time
import re
import pandas as pd
from urllib import parse
from datetime import datetime, timedelta
from typing import List, Union
from pprint import pprint
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

@dataclass
class NaverNewsRun():
    
    # CSS_SELECTOR
    #[TODO] separate css_selector class for management
    news_selector:str='div.group_news > ul > li'
    tit_selector:str='.news_tit'
    dsc_selector:str='.news_dsc > .dsc_wrap'
    press_selector:str='div.info_group > a.info.press'
    created_at_selector:str='div.info_group > span'
    
    # initial variables
    max_num_news:int = 2000
    wait_until:Union[int, float] = 10
    
    # crawled news list
    news_collections:List[Tag] = field(default_factory=list)
    
    def __post_init__(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        
        self.started_at = datetime.now()
    
    @property
    def _base_url(self):
        base_url = "https://search.naver.com/search.naver"
        news_param = "ssc=tab.news.all&where=news&sm=tab_jum"
        return f"{base_url}?{news_param}"
    
    @staticmethod
    def parse_timespan(span:str):
        # skip week(주), month(월), year(년)
        m_pat = re.compile(r'(\d+)분 전')
        h_pat = re.compile(r'(\d+)시간 전')
        d_pat = re.compile(r'(\d+)일 전')

        # Check if the span matches any of the patterns
        if m_pat.match(span):
            time_digit = int(''.join(re.findall(r'\d+', span)))
            return timedelta(minutes=time_digit)
        elif h_pat.match(span):
            time_digit = int(''.join(re.findall(r'\d+', span)))
            return timedelta(hours=time_digit)
        elif d_pat.match(span):
            time_digit = int(''.join(re.findall(r'\d+', span)))
            return timedelta(days=time_digit)
        else:
            return "unknown"
    
    def _encode_url(self, query):
        query = [('query', query)]
        enc_query = parse.urlencode(query, doseq=True)
        return f"{self._base_url}&{enc_query}"
    
    def _click_sort_btn(self) -> NaverNewsRun:
        # wait until the <a> tag with 'onclick' containing 'newcls' is present
        # click the btn to sort the news as decending order
        WebDriverWait(self.driver, self.wait_until).until(
            EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@onclick, 'newcls')]")
            )
        ).click()    
        return self
    
    def _scroll_down(self) -> NaverNewsRun:
        while True:
            # scroll down until the number of news reach the `max_num_news`
            soup = BeautifulSoup(self.driver.page_source, "lxml")
            self.news_collections = soup.select(self.news_selector)
            
            if self.max_num_news <= len(self.news_collections):
                break
            
            # infinitely scroll down to get more news
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        print(f"Finish scrolling - Number of scraped news: {len(self.news_collections)}")
        return self
    
    def extract_contents(self) -> List[dict]:
        contents = []
        for news in self.news_collections:
            try:
                # get press info
                press = news.select_one(self.press_selector).text
                
                # get created_at
                spans = [span.text for span in news.select(self.created_at_selector)]
                timediffs = [self.parse_timespan(span) for span in spans]
                timediffs = list(filter(lambda x: isinstance(x, timedelta), timediffs))
                
                # if there is no any time information, skip the news
                if not len(timediffs):
                    print(f"No time information detected. Candidates: {spans}")
                    continue
                created_at = newsrun.started_at - timediffs[0]
                
                # # drop out the news which are outdated (not today)
                # if created_at.date() != newsrun.started_at.date():
                #     continue
                
                title_box = news.select_one(self.tit_selector)
                title = title_box["title"]
                href = title_box["href"]
                dsc = news.select_one(self.dsc_selector)
                contents += [
                    {
                        "press": press.strip(),
                        "created_at": created_at.strftime('%Y-%m-%dT%H:%M:%S'),
                        "title": title.strip(),
                        "href": href.strip(),
                        "dsc": dsc.text.strip()
                    }
                ]
            except Exception as e:
                print(f"Unexpected error occurs during information parsing. Message: {e}")
        return contents
        
    def run(self, query:str):
        url = self._encode_url(query=query)
        
        # tap into the browser
        self.driver.get(url)
        self.driver.implicitly_wait(5)

        # sort news list as descending order
        # & scroll down to get more news 
        self._click_sort_btn()._scroll_down()

        return self.extract_contents()
        
        
if __name__ == "__main__":
    newsrun = NaverNewsRun()
    contents = newsrun.run(query="M&A")
    contents = pd.DataFrame(contents)
    contents.to_excel("./data/contents.xlsx", index=None)