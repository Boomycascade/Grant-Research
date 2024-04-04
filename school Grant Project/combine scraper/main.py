import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

# List of user agents to mimic different browsers
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
]

# Set to store visited URLs
visited_urls = set()

# Create a session object
session = requests.Session()

# Function to generate custom headers for requests
def get_custom_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),  # Randomly select a user agent
        'Accept-Language': 'da, en-gb;q=0.8, en;q=0.7, *;q=0.5',  # Define language preferences
        'Accept-Encoding': 'gzip, deflate, br',  # Define encoding preferences
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',  # Define content type preferences
        'Referer': 'https://www.google.com/',  # Define referer
        'DNT': '1',  # Send Do Not Track request
        'Connection': 'keep-alive',  # Keep the connection alive
        'Upgrade-Insecure-Requests': '1'  # Upgrade insecure requests
    }

# Function to send a GET request and return the response
def send_get_request(url):
    custom_headers = get_custom_headers()  # Get custom headers
    for _ in range(10):  # Try 10 times
        response = session.get(url, headers=custom_headers)  # Send GET request using the session object
        if response.status_code == 200:  # If the response status code is 200, break the loop
            break
        elif response.status_code == 503:  # If the response status code is 503, wait and try again
            print("503 error, retrying after delay...")
            time.sleep(random.uniform(3, 8))  # Wait for a random time between 1 and 3 seconds
        else:  # If the response status code is something else, print an error message and return None
            print(f"Error in getting webpage: {url}")
            return None
    else:  # If the loop completes without breaking (i.e., the request failed 5 times), print an error message and return None
        print("Failed to fetch webpage after multiple attempts.")
        return None

    return response

# Function to scrape product information from a given URL
def get_product_info(url):
    response = send_get_request(url)  # Send GET request
    if response is None:  # If the request failed, return None
        return None

    soup = BeautifulSoup(response.text, "lxml")  # Parse the HTML of the page

    # Extract product information
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

    # Return a dictionary with the product information
    return {
        "title": title,
        "price": price,
        "rating": rating,
        "image": image,
        "description": description,
        "url": url
    }

# Function to parse a listing page
def parse_listing(listing_url):
    response = send_get_request(listing_url)  # Send GET request
    if response is None:  # If the request failed, return None
        print(f"Failed to fetch listing page: {listing_url}")
        return []

    soup_search = BeautifulSoup(response.text, "lxml")  # Parse the HTML of the page
    link_elements = soup_search.select("[data-asin] h2 a")  # Select all product links
    page_data = []  # List to store product data

    for link in link_elements:  # For each product link
        full_url = urljoin(listing_url, link.attrs.get("href"))  # Get the full URL
        if full_url not in visited_urls:  # If the URL has not been visited
            visited_urls.add(full_url)  # Add the URL to the set of visited URLs
            print(f"Scraping product from {full_url[:100]}", flush=True)  # Print a message
            product_info = get_product_info(full_url)  # Get the product information
            if product_info:  # If the product information was successfully scraped
                page_data.append(product_info)  # Add the product information to the list

    # Check for a next page link
    next_page_el = soup_search.select_one('a.s-pagination-next')
    if next_page_el:  # If a next page link is found
        next_page_url = next_page_el.attrs.get('href')  # Get the URL of the next page
        next_page_url = urljoin(listing_url, next_page_url)  # Get the full URL of the next page
        print(f'Scraping next page: {next_page_url}', flush=True)  # Print a message
        time.sleep(random.uniform(3, 8))  # Wait for a random time between 3 and 8 seconds before making the next request
        session.headers.update(get_custom_headers())  # Update the headers with a new user agent
        page_data += parse_listing(next_page_url)  # Recursively scrape the next page and add the data to the list

    return page_data  # Return the list of product data


def scrape_ebay(item):
    url = f"https://www.ebay.com/sch/i.html?_nkw={item}"
    data = []

    while url:
        response = send_get_request(url)
        if response is None:  # If the request failed, return None
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.find_all('li', attrs={'class': 's-item'})

        for result in results:
            try:
                product = result.find('div', attrs={'class': 's-item__title'}).get_text()
                price = result.find('span', attrs={'class': 's-item__price'}).get_text()
                image = result.find('img')['src']
                description = result.find('div', attrs={'class': 's-item__subtitle'}).get_text()
                product_url = result.find('a', attrs={'class': 's-item__link'})['href']

                data.append({
                    "title": product,
                    "price": price,
                    "image": image,
                    "description": description,
                    "url": product_url
                })
            except AttributeError:
                continue

        next_page = soup.find('a', attrs={'class': 'pagination__next'})
        next_url = next_page['href'] if next_page else None

        print(f"Next URL: {next_url}")  # Print the next_url for debugging

        if next_url and next_url not in visited_urls:
            visited_urls.add(next_url)
            url = next_url
        else:
            url = None

        # Add a delay before the next request
        time.sleep(random.randint(3, 8))  # Random delay between 3 and 8 seconds

    return data

def main():
    keyword = 'Tea'  # Replace this with your keyword

    # Define the tasks to be run concurrently
    tasks = [
        ('amazon', parse_listing, f"https://www.amazon.com/s?k={keyword}", "amazon_data.csv"),
        ('ebay', scrape_ebay, keyword, "ebay_data.csv")
    ]

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        futures = []
        for platform, scraper_func, url, csv_file in tasks:
            print(f"Starting {platform} scraper...")
            future = executor.submit(scraper_func, url)  # Start the scraper in a separate thread
            futures.append((future, platform, csv_file))

        for future, platform, csv_file in futures:
            try:
                data = future.result()  # Wait for the scraper to finish and get the result
                df = pd.DataFrame(data)
                df.to_csv(csv_file)
                print(f"{platform} scraper finished. Data saved to {csv_file}.")
            except Exception as e:
                print(f"An error occurred in the {platform} scraper: {e}")

if __name__ == '__main__':
    main()
