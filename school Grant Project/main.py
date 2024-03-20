import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import time
import random

user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
]

def get_custom_headers():
    return {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'da, en-gb;q=0.8, en;q=0.7, *;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

visited_urls = set()

def get_product_info(url):
    custom_headers = get_custom_headers()
    for _ in range(5):
        response = requests.get(url, headers=custom_headers)
        if response.status_code == 200:
            break
        elif response.status_code == 503:
            print("503 error, retrying after delay...")
            time.sleep(random.uniform(1, 3))
        else:
            print(f"Error in getting webpage: {url}")
            return None
    else:
        print("Failed to fetch webpage after multiple attempts.")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    title_element = soup.select_one("#productTitle")
    title = title_element.text.strip() if title_element else None

    price_element = soup.select_one('span.a-offscreen')
    price = price_element.text if price_element else None

    rating_element = soup.select_one("#acrPopover")
    rating_text = rating_element.attrs.get("title") if rating_element else None
    rating = rating_text.replace("out of 5 stars", "") if rating_text else None

    image_element = soup.select_one("#landingImage")
    image = image_element.attrs.get("src") if image_element else None

    description_element = soup.select_one("#productDescription")
    description = description_element.text.strip() if description_element else None

    return {
        "title": title,
        "price": price,
        "rating": rating,
        "image": image,
        "description": description,
        "url": url
    }

def parse_listing(listing_url):
    custom_headers = get_custom_headers()
    for _ in range(5):
        response = requests.get(listing_url, headers=custom_headers)

    soup_search = BeautifulSoup(response.text, "lxml")
    link_elements = soup_search.select("[data-asin] h2 a")
    page_data = []

    for link in link_elements:
        full_url = urljoin(listing_url, link.attrs.get("href"))
        if full_url not in visited_urls:
            visited_urls.add(full_url)
            print(f"Scraping product from {full_url[:100]}", flush=True)
            product_info = get_product_info(full_url)
            if product_info:
                page_data.append(product_info)


    next_page_el = soup_search.select_one('a.s-pagination-next')
    if next_page_el:
        next_page_url = next_page_el.attrs.get('href')
        next_page_url = urljoin(listing_url, next_page_url)
        print(f'Scraping next page: {next_page_url}', flush=True)
        page_data += parse_listing(next_page_url)

    return page_data

def main():
    data = []
    search_url = "https://www.amazon.com/s?k=candy&crid=1CD9QQYL8F4AN&sprefix=candy%2Caps%2C102&ref=nb_sb_noss_1"
    data = parse_listing(search_url)
    df = pd.DataFrame(data)
    df.to_csv("candy.csv")

if __name__ == '__main__':
    main()
