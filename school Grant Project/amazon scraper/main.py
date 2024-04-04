import requests  # For making HTTP requests
from bs4 import BeautifulSoup  # For HTML parsing
from urllib.parse import urljoin  # For resolving relative URLs
import pandas as pd  # For data manipulation and analysis
import time  # For time-related tasks
import random  # For generating random numbers

# List of user agents to mimic different browsers
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
]

# Function to generate custom headers for requests
def get_custom_headers():
    return {
        'User-Agent': random.choice(user_agents),  # Randomly select a user agent
        'Accept-Language': 'da, en-gb;q=0.8, en;q=0.7, *;q=0.5',  # Define language preferences
        'Accept-Encoding': 'gzip, deflate, br',  # Define encoding preferences
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',  # Define content type preferences
        'Referer': 'https://www.google.com/',  # Define referer
        'DNT': '1',  # Send Do Not Track request
        'Connection': 'keep-alive',  # Keep the connection alive
        'Upgrade-Insecure-Requests': '1'  # Upgrade insecure requests
    }

# Set to store visited URLs
visited_urls = set()

# Function to scrape product information from a given URL
def get_product_info(url):
    custom_headers = get_custom_headers()  # Get custom headers
    for _ in range(5):  # Try 5 times
        response = requests.get(url, headers=custom_headers)  # Send GET request
        if response.status_code == 200:  # If the response status code is 200, break the loop
            break
        elif response.status_code == 503:  # If the response status code is 503, wait and try again
            print("503 error, retrying after delay...")
            time.sleep(random.uniform(1, 3))  # Wait for a random time between 1 and 3 seconds
        else:  # If the response status code is something else, print an error message and return None
            print(f"Error in getting webpage: {url}")
            return None
    else:  # If the loop completes without breaking (i.e., the request failed 5 times), print an error message and return None
        print("Failed to fetch webpage after multiple attempts.")
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
    custom_headers = get_custom_headers()  # Get custom headers
    for _ in range(5):  # Try 5 times
        response = requests.get(listing_url, headers=custom_headers)  # Send GET request

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
        page_data += parse_listing(next_page_url)  # Recursively scrape the next page and add the data to the list

    return page_data  # Return the list of product data

# Main function
def main():
    data = []  # List to store data
    search_url = "https://www.amazon.com/s?k=candy&crid=1CD9QQYL8F4AN&sprefix=candy%2Caps%2C102&ref=nb_sb_noss_1"  # URL of the search page
    data = parse_listing(search_url)  # Scrape the listing page
    df = pd.DataFrame(data)  # Convert the data to a DataFrame
    df.to_csv("candy.csv")  # Save the DataFrame to a CSV file

# If the script is run directly (not imported), call the main function
if __name__ == '__main__':
    main()
