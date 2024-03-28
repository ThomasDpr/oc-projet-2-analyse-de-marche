import os
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd


class BookScraper:
    def __init__(self, base_url='https://books.toscrape.com/'):
        # Initialisation des attributs de la classe
        self.base_url = base_url
        self._soup = None
        
    # Méthodes utilitaires pour récupérer et valider le contenu de la page
    def get_soup(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            self._soup = bs(response.content, 'html.parser')
            # print(f'✅ Response {response.status_code}')
        except requests.RequestException as e:
            print(f'❌ Error: {e}')
            self._soup = None

    def _validate_soup(self):
        # On vérifie si self._soup est défini et si la requête a réussi
        if self._soup is None:
            print('Soup not set or request failed.')
            return False
        return True

    def normalize_data(self, data):
        # Convertion des ratings en nombres
        rating_dict = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        data['review_rating'] = rating_dict.get(data['review_rating'], 'No rating found')
        
        # Convertion des prix en nombres flottants
        data['price_including_tax'] = float(data['price_including_tax'].replace('£', ''))
        data['price_excluding_tax'] = float(data['price_excluding_tax'].replace('£', ''))
        
        # Convertion du nombre d'articles disponibles en nombre entier
        data['number_available'] = int(data['number_available'].replace('In stock (', '').replace(' available)', ''))
        
        # Convertion d'UPC en universal_code_product (upc)
        data['universal_product_code'] = data.pop('universal_product_code (upc)')
    
    
    # Méthodes pour récupérer les données
    def get_all_categories_urls(self):
        self.get_soup(self.base_url)
        if not self._validate_soup():
            return {}

        category_urls = {}
        categories_section = self._soup.find('div', class_='side_categories')
        categories_links = categories_section.find_all('a')[1:]
        for link in categories_links:
            category_name = link.text.strip()
            category_url = self.base_url + link.get('href')
            category_urls[category_name] = category_url
        return category_urls
    
    def get_category_books_urls(self, category_url, books_urls=None):
        if books_urls is None:
            books_urls = []
        
        self.get_soup(category_url)
        if not self._validate_soup():
            return books_urls
        
        books = self._soup.find_all('article', class_='product_pod')
        for book in books:
            book_url = book.find('h3').find('a').get('href').replace('../../..', self.base_url + 'catalogue')
            books_urls.append(book_url)
            
        next_page = self._soup.find('li', class_='next')
        if next_page:
            next_page_url = next_page.a.get('href')

            if next_page_url.startswith('/'):
                next_page_full_url = self.base_url + next_page_url
            else:
                next_page_full_url = category_url.rsplit('/', 1)[0] + '/' + next_page_url
            return self.get_category_books_urls(next_page_full_url, books_urls)
        else:
            return books_urls
            
    @property
    def title(self):
        if self._validate_soup():
            product_main = self._soup.find('div', class_='product_main')
            title = product_main.h1.text if product_main else 'No title found'
            print(f'TITLE: {title}')
            return title
        return 'Soup not set'

    @property
    def category(self):
        if self._validate_soup():
            breadcrumb = self._soup.find('ul', class_='breadcrumb')
            category = breadcrumb.findAll('a')[2].text if breadcrumb else 'No category found'
            if category:
                print(f'CATEGORY: 🟢')
            return category
        return 'Soup not set'

    @property
    def product_description(self):
        if self._validate_soup():
            product_description_header = self._soup.find('div', id='product_description')
            if product_description_header:
                description = product_description_header.find_next_sibling('p').text
                if description:
                    print(f'DESCRIPTION: 🟢')
                return description
        return 'No description found'

    @property
    def review_rating(self):
        if self._validate_soup():
            product_main = self._soup.find('div', class_='product_main')
            rating_class = product_main.find('p', class_='star-rating')['class'][1]  # Ex. : "Three"
            if rating_class:
                print(f'RATING: 🟢')
            return rating_class
        return 'Soup not set'

    
    @property
    def image_url(self):
        if self._validate_soup():
            product_main = self._soup.find('div', class_='item active')
            if product_main and product_main.img:
                product_image = product_main.img.get('src')
                if product_image:
                    image_url = self.base_url + product_image.split('../')[-1]
                    if image_url:
                        print(f'IMAGE URL: 🟢')
                    return image_url
        return 'No image found'
    
    @property
    def table(self):
        if self._validate_soup():
            table = self._soup.find('table', class_='table table-striped')
            data_dict = {}
            if table:
                for row in table.find_all('tr'):
                    th = row.find('th').text
                    td = row.find('td').text
                    data_dict[th] = td  
            return data_dict
        return 'Soup not set'

    # Méthode pour initier le scraping d'un livre
    def scrape_and_save_books(self, urls, category_name):
        books_data = []

        for url in urls:
            self.get_soup(url)
            if not self._validate_soup():
                print(f"Failed to retrieve book data from {url}")
                continue
            
            book_data = { 
                'title': self.title,
                'category': self.category,
                'product_description': self.product_description,
                'review_rating': self.review_rating,
                'image_url': self.image_url,
                'price_including_tax': self.table['Price (incl. tax)'],
                'price_excluding_tax': self.table['Price (excl. tax)'],
                'number_available': self.table['Availability'],
                'universal_product_code (upc)': self.table['UPC'],
            }
            # On applique la normalisation
            self.normalize_data(book_data)
            # On ajoute les données du livre à la liste
            books_data.append(book_data)

        if books_data:
            if not os.path.exists('datas'):
                os.makedirs('datas')
                
            # DataFrame à partir des données des livres et sauvegarder en CSV'
            formatted_category_name = category_name.lower().replace(' ', '_')
            filename = f'datas/{formatted_category_name}_books_data.csv'
            df = pd.DataFrame(books_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Data saved to {filename}")
        else:
            print("No books data to save.")



def main():
    scraper = BookScraper()
    category_urls = scraper.get_all_categories_urls()

    if not category_urls:
        print('No category URLs found. Exiting.')
        return
    else:
        print(f'\t🔎 Number of categories found: {len(category_urls)}')
        print(f'\t🏁 Starting scraping process\n')


    for category_name, category_url in category_urls.items():
        print(f'\t🎣 Scraping category: {category_name}')
        books_urls = scraper.get_category_books_urls(category_url)
        print(f'\t📚 Number of books found: {len(books_urls)}')
        print(f'\t📚 Scraping books data...')
        print(f'\t📚 Saving books data to CSV...')
        print(f'\t📚 {category_name} done\n')
        
        if books_urls:
            print(f'\t📚 Number of books found: {len(books_urls)}')
            scraper.scrape_and_save_books(books_urls, category_name)
            print(f'\t📚 {category_name} category processing done\n')
        else:
            print(f'\t❗No books found for {category_name}. Skipping...\n')
if __name__ == '__main__':
    main()