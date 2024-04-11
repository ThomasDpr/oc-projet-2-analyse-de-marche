import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import sys
import os
# --- source : https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir --- #
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scraper.book_details_scraper.single_book_scraper import scrape_book_data


def get_book_urls_from_page(category_url, book_urls=[]):
    print(f'Starting to scrape category page: {category_url}')
    response = requests.get(category_url)
    soup = bs(response.content, 'html.parser')

    books = soup.select('.product_pod h3 a')
    for book in books:
        book_url = 'http://books.toscrape.com/catalogue/' + book['href'].split('../')[-1]
        book_urls.append(book_url)

    # Check if next page exists
    next_button = soup.find('li', class_='next')
    if next_button:
        next_page_url = next_button.find('a')['href']
        next_page_full_url = category_url.rsplit('/', 1)[0] + '/' + next_page_url
        return get_book_urls_from_page(next_page_full_url, book_urls)
    else:
        return book_urls

if __name__ == '__main__':
    category_url = 'https://books.toscrape.com/catalogue/category/books/mystery_3/index.html'
    book_urls = get_book_urls_from_page(category_url)
    print(f'Book URLs for {category_url.split("/")[-2]}: {book_urls}')
    print(f'Total books found in the category: {len(book_urls)}')
    
    books_data = []
    for url in book_urls:
        book_data = scrape_book_data(url)
        books_data.append(book_data)
    
    
    df = pd.DataFrame(books_data)
        
    save_dir = 'scraper/book_category_scraper/books_data'
    os.makedirs(save_dir, exist_ok=True)
    
    cleaned_title = book_data['category'].replace(' ', '_').lower()
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    csv_file_name = f'{cleaned_title}_data_{timestamp}.csv'        
    csv_path = os.path.join(save_dir, csv_file_name)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f'Data for all books in the category has been saved to {csv_path} - Total books saved: {len(books_data)}')
