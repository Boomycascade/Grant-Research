import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Set to store visited URLs
visited_urls = set()

# Function to send a GET request and return the response
def send_get_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        print(f'Other error occurred: {err}')
        return None
    else:
        return response

# Function to scrape eBay listings
def scrape_ebay(item):
    # Construct the URL for the eBay search page
    url = f"https://www.ebay.com/sch/i.html?_nkw={item}"
    data = []

    # Continue scraping while there's a next page
    while url:
        # Send a GET request to the current page
        response = send_get_request(url)
        if response is None:  # If the request failed, return None
            return None

        # Parse the HTML of the page
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all listings on the page
        results = soup.find_all('li', attrs={'class': 's-item'})

        # For each listing, extract the product information and add it to the data list
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

        # Check for a next page link and update the URL for the next iteration
        next_page = soup.find('a', attrs={'class': 'pagination__next'})
        next_url = next_page['href'] if next_page else None

        # Print the next_url for debugging
        print(f"Next URL: {next_url}")

        # If there's a next page and its URL hasn't been visited yet, update the URL for the next iteration
        if next_url and next_url not in visited_urls:
            visited_urls.add(next_url)
            url = next_url
        else:
            url = None

        # Add a delay before the next request
        time.sleep(random.randint(3, 8))  # Random delay between 3 and 8 seconds

    # Return the scraped data
    return data

def main():
    # Scrape eBay for a specific item
    item = "adidas shoes red men 20"  # Replace this with your keyword
    data = scrape_ebay(item)

    # Save the data to a CSV file
    df = pd.DataFrame(data)
    df.to_csv("ebay_data.csv", index=False)

if __name__ == '__main__':
    main()
