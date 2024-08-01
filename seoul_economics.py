import requests
import json
import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag
from itertools import islice

def parse(url:str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text)

    # retrieve script tag in the header
    script_tag = soup.find('script', type='application/ld+json')
    script_tag = json.loads(script_tag.string)

    # get reporter, published_at, keywords information
    reporter = script_tag.pop('author')['name']
    published_at = script_tag.pop('datePublished')
    metadata = json.dumps(script_tag, ensure_ascii=False)

    # get article body
    article_body = ""
    for br in soup.select('div.article_view > br'):
        next_s = br.next_sibling
        if not (next_s and isinstance(next_s, NavigableString)):
            continue
        next2_s = next_s.next_sibling
        if next2_s and isinstance(next2_s,Tag) and next2_s.name == 'br':
            text = next_s.text.strip()
            if text:
                article_body += f"{text}\n"
    
    return {
        "reporter": reporter,
        "published_at": published_at,
        "article_body": article_body,
        "metadata": metadata
    }

data = pd.read_excel("./data/contents.xlsx")
tgt_presses = dict(islice(data["press"].value_counts().to_dict().items(), 10))
data = data[data["press"].isin(tgt_presses.keys())].sort_values("press")
urls = data[data["href"].str.contains("서울경제")]["href"].unique().tolist()
info_bag = []
for url in urls:
    info_bag += [parse(url)]