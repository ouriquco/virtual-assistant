import requests
import os 
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

def DDGS_search_links(query, num_results=5):
    return [result['href'] for result in DDGS().text(query, max_results=num_results)]

def scrape_pages(urls):
    documents = []
    for url in urls:
        try:
            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                print(f"Failed to retrieve {url}: {response.status_code}, skipping this URL.")
                continue
            elif response.text == 'Access Denied':
                print(f"Access Denied for {url}, skipping this URL.")   
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = ' '.join([p.get_text() for p in soup.select('p')])
            documents.append({
                'url': url,
                'content': text,
                'title': soup.title.string if soup.title else ''
            })
        except Exception as e:
            print(f"Failed {url}: {str(e)}")
    return documents

def run_web_scraper(query, num_results=5):
    result_links = DDGS_search_links(query, num_results)
    print(f'Scraping data from the following sites: {result_links}')
    documents = scrape_pages(result_links)
    relative_path = './web_data'

    if not os.path.exists(relative_path):
        print("enter")
        os.makedirs(relative_path)

    for i, doc in enumerate(documents):
        print(f"URL: {doc['url']}")
        print(f"Title: {doc['title']}")
        print(f"Content: {doc['content'][:100]}")
        print("-" * 80)

        with open(f'./web_data/output{i}.txt', 'a', encoding='utf-8') as f:
            f.write(f"Title: {doc['title']}\n")
            f.write(f"Content: {doc['content']}\n")