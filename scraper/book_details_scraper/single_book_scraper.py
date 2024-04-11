from bs4 import BeautifulSoup as bs
import logging
from requests.exceptions import RequestException
import os
import pandas as pd
import requests

log_dir = os.path.join('scraper', 'logs')
os.makedirs(log_dir, exist_ok=True)

# configure the logging
logging.basicConfig(filename=os.path.join(log_dir, 'books_scraper_logs.log'),
                    level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')


def scrape_book_data(url):
    """Scrapes book data from books.toscrape.com.

    Args:
        url (str): The URL of the book page to scrape
        
    Returns:
        dict: A dictionary containing the book data such as: title, category, product_description, review_rating, price (including tax), price (excluding tax), available stock, UPC, and image URL. Returns None if an error occurs during the scraping process.
    
    Logs errors to 'books_scraper_logs.log' if the GET request or HTML parsing fails or if any of the required data is not found/missing on the page.
    """
    
    print(f'Starting to scrape book data from {url}')

    try:
        # Send a GET request
        response = requests.get(url)
        response.raise_for_status()
    except RequestException as e:
        logging.error(f'Error sending GET request: {e}')
        print(f'Failed to get response for {url}')
        return None
    
    try:
        # Parse the HTML content
        soup = bs(response.content, 'html.parser')
    except Exception as e:
        logging.error(f'Error parsing the HTML content: {e}')
        print(f'Failed to parse the HTML content for {url}')
        return None
    
    # Extract the book data
    
    title_element  = soup.find('div', class_='product_main').h1
    if not title_element:
        logging.error('No title found')
        return None
    title = title_element.text
    
    product_description_element = soup.find('div', id='product_description')
    product_description = product_description_element.find_next_sibling('p').text if product_description_element else 'No description found'
    
    category_element = soup.find('ul', class_='breadcrumb').find_all('a')[2]
    if not category_element:
        logging.error('No category found')
        return None
    category = category_element.text
    
    review_rating_element = soup.find('p', class_='star-rating')
    if not review_rating_element:
        logging.error('No review rating found')
        return None
    review_rating = review_rating_element['class'][1]
    
    image_element = soup.find('div', class_='item active').img
    image_url = image_element.get('src') if image_element else 'No image found'
    image_url = 'https://books.toscrape.com/' + image_url.split('../')[-1]
    

    # Extract table data
    table = soup.find('table', class_='table table-striped')
    book_data = {}
    for row in table.find_all('tr'):
        # Extract the key and value from the row
        key = row.find('th').text
        value = row.find('td').text
        book_data[key] = value

    # Normalize data
    review_rating_dict = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    review_rating = review_rating_dict.get(review_rating, 'No rating found')
    
    price_including_tax = float(book_data['Price (incl. tax)'].replace('£', ''))
    price_excluding_tax = float(book_data['Price (excl. tax)'].replace('£', ''))
    number_available = int(book_data['Availability'].replace('In stock (', '').replace(' available)', ''))
    universal_product_code = book_data['UPC']
    
    print(f'Successfully scraped data for {title}')
    
    # Return the book data
    return {
        'product_page_url': url,
        'universal_product_code (upc)': universal_product_code,
        'title': title,
        'price_including_tax': price_including_tax,
        'price_excluding_tax': price_excluding_tax,
        'number_available': number_available,
        'category': category,
        'product_description': product_description,
        'review_rating': review_rating,
        'image_url': image_url,
    }

if __name__ == '__main__':
    product_url = 'https://books.toscrape.com/catalogue/ready-player-one_209/index.html'

    print('Starting the book scraping process...')
    book_data = scrape_book_data(product_url)
    
    if book_data:
        
        print(f'Book data for "{book_data["title"]}" retrieved successfully.')
        
        # Convert the book data to a DataFrame 
        df = pd.DataFrame([book_data])
        
        # Here I define the location where I want to save the file
        save_dir = 'scraper/book_details_scraper/books_data'
        os.makedirs(save_dir, exist_ok=True)

        # Save the DataFrame to a CSV file
        cleaned_title = book_data['title'].replace(' ', '_').lower()
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        csv_file_name = f'{cleaned_title}_data_{timestamp}.csv'
        csv_path = os.path.join(save_dir, csv_file_name)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f'Book data saved to {csv_path}')
    else:
        print('Failed to scrape book data')