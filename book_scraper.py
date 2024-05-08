import os, time, requests, pandas as pd
from bs4 import BeautifulSoup as bs
from rich.table import Table
from rich.console import Console


class BookScraper:
    def __init__(self, base_url='https://books.toscrape.com/'):
        """Initialisation de la classe BookScraper.

        Args:
            base_url (str): URL de base du site à scraper. Par défaut, 'https://books.toscrape.com/'.
        """
        self.base_url = base_url
        self._soup = None
        self.session = requests.Session() # j'essaye en  remplacant requests.get par requests.Session() pour tester la persistance de la session pour les performances
        
    def get_soup(self, url):
        """Récupère et analyse le contenu d'une page we.

        Args:
            url (str): URL de la page web à scraper.
        
        Raises:
            requests.RequestException: Si une erreur se produit lors de la requête HTTP.
            
        Sets:
            self._soup (BeautifulSoup): Contenu de la page web analysé
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            self._soup = bs(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f'❌ Error fetching URL {url}: {e}')
            self._soup = None

    def _validate_soup(self):
        """Vérifie si l'objet BeautifulSoup est défini et que la requête a réussi.

        Returns:
            bool: True si self._soup est défini, False sinon.
        """
        if self._soup is None:
            print('Soup not set or request failed.')
            return False
        return True

    def normalize_data(self, data):
        """Normalise les données extraites en type de données que j'ai défini.

        Args:
            data (dict): Dictionnaire contenant les données extraites du livre.
        
        Normalises:
            - review_rating: Convertit la note en nombre entier
            - price_including_tax: Convertit le prix en nombre flottant et retire le symbole '£'
            - price_excluding_tax: Convertit le prix en nombre flottant et retire le symbole '£'
            - number_available: Convertit le nombre d'articles disponibles en nombre entier et retire les textes inutiles
            - universal_product_code: Renomme la clé 'universal_product_code (upc)' en 'universal_product_code'
        
        Returns:
            dict: Dictionnaire de données normalisées du livre.
        """
        rating_dict = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        data['review_rating'] = rating_dict.get(data['review_rating'], 'No rating found')
        data['price_including_tax'] = float(data['price_including_tax'].replace('£', ''))
        data['price_excluding_tax'] = float(data['price_excluding_tax'].replace('£', ''))
        data['number_available'] = int(data['number_available'].replace('In stock (', '').replace(' available)', ''))
        data['universal_product_code'] = data.pop('universal_product_code (upc)')
    
    
    def get_all_categories_urls(self):
        """Récupère les URL de toutes les catégories du site.

        Returns:
            dict: Dictionnaire des noms de catégories et de leurs URL.
        """
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
        """Récupère les URL de tous les livres d'une catégorie donnée, avec pagination.

        Args:
            category_url (str): URL de la catégorie à scraper.
            books_urls (lsit): Liste contenant les URL des livres. Par défaut, None car initialisé à une liste vide.

        Returns:
            list: Liste contenant les URL de tous les livres de la catégorie.
        """
        if books_urls is None:
            books_urls = []

        self.get_soup(category_url)
        if not self._validate_soup():
            return books_urls

        books = self._soup.find_all('article', class_='product_pod')
        for book in books:
            book_url = book.find('h3').find('a').get('href').replace('../../..', self.base_url + 'catalogue/')
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
        """Extrait le titre du livre.

        Returns:
            str: Titre du livre.
        """
        if self._validate_soup():
            product_main = self._soup.find('div', class_='product_main')
            return product_main.h1.text if product_main else 'No title found'
        return 'Soup not set'

    @property
    def category(self):
        """Extrait la catégorie du livre.

        Returns:
            str: Catégorie du livre.
        """
        if self._validate_soup():
            breadcrumb = self._soup.find('ul', class_='breadcrumb')
            return breadcrumb.findAll('a')[2].text if breadcrumb else 'No category found'
        return 'Soup not set'

    @property
    def product_description(self):
        """Extrait la description du livre.

        Returns:
            str: Description du livre.
        """
        if self._validate_soup():
            product_description_header = self._soup.find('div', id='product_description')
            if product_description_header:
                return product_description_header.find_next_sibling('p').text
        return 'No description found'

    @property
    def review_rating(self):
        """Extrait la note du livre.

        Returns:
            str: Note du livre.
        """
        if self._validate_soup():
            product_main = self._soup.find('div', class_='product_main')
            return product_main.find('p', class_='star-rating')['class'][1] if product_main else 'No review rating found'
        return 'Soup not set'

    
    @property
    def image_url(self):
        """Extrait l'URL de l'image du livre.

        Returns:
            str: URL de l'image du livre reconstruit avec l'URL de base.
        """
        if self._validate_soup():
            product_main = self._soup.find('div', class_='item active')
            if product_main and product_main.img:
                product_image = product_main.img.get('src')
                return self.base_url + product_image.split('../')[-1]
        return 'No image found'
    
    @property
    def table(self):
        """Extrait les données du tableau de détails du livre.

        Returns:
            dict: Dictionnaire contenant les données du tableau de détails du livre.
        """
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

    def download_image(self, image_url, save_path):
        """Télécharge et sauvegarde l'image du livre.

        Args:
            image_url (str): URL de l'image à télécharger.
            save_path (str): Chemin complet où sauvegarder l'image localement.
        
        Raises:
            requests.RequestException: Si une erreur se produit lors de la requête HTTP.
        """
        try:
            response = self.session.get(image_url)
            response.raise_for_status()
            with open(save_path, 'wb') as image_file:
                image_file.write(response.content)
            print(f"Image saved to {save_path}")
        except requests.RequestException as e:
            print(f"❌ Failed to download image: {e}")


    # Méthode pour initier le scraping d'un livre
    def scrape_and_save_books(self, urls, category_name):
        """Scrape et sauvegarde les données de tous les livres d'une catégorie donnée.

        Args:
            urls (list): Liste contenant les URL de tous les livres de la catégorie.
            category_name (str): Nom de la catégorie.
        
        Saves:
            - Fichier CSV contenant les données de tous les livres de la catégorie.
            - Images des livres dans un dossier spécifique.
        """
        books_data = []
        image_folder = f'images/{category_name}'
        os.makedirs(image_folder, exist_ok=True)

        for url in urls:
            self.get_soup(url)
            if not self._validate_soup():
                print(f"❌ Failed to retrieve book data from {url}")
                continue
            try:

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
                # On applique la normalisation des données
                self.normalize_data(book_data)
                
                image_filename = f"{book_data['universal_product_code']}_{book_data['title'].replace(' ', '_').replace('/', '_')}.jpg"
                image_path = os.path.join(image_folder, image_filename)
                self.download_image(book_data['image_url'], image_path)
                
                book_data['image_path'] = image_path
                books_data.append(book_data)
            
            except KeyError as e:
                print(f"❌ Missing data field: {e} for book at {url}")
                continue

        if books_data:
            os.makedirs('datas', exist_ok=True)
            category_folder = f'datas/{category_name}'
            os.makedirs(category_folder, exist_ok=True)
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{category_folder}/{category_name.lower().replace(" ", "_")}_books_data_{timestamp}.csv'
            df = pd.DataFrame(books_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Data saved to {filename}")
        else:
            print("❌ No books data to save.")



def main():
    """Fonction principale pour lancer le scraping du site web et sauvegarder les données des livres et les images.
    """
    scraper = BookScraper()
    category_urls = scraper.get_all_categories_urls()

    if not category_urls:
        print('❌ No category URLs found. Exiting.')
        return
    else:
        print(f'🔎 Number of categories found: {len(category_urls)}')
        print(f'🏁 Starting scraping process\n')

    console = Console()
    summary_table = Table(title='Summary of Scraping', show_header=True, header_style='bold magenta', show_footer=True, footer_style='bold green')
    summary_table.add_column('Category Name', style='dim', width=25)
    summary_table.add_column('Number of Books', justify='right')
    summary_table.add_column('Time Taken (s)', justify='right')
    total_books = 0
    total_time = 0
    

    for category_name, category_url in category_urls.items():
        start_time = time.time()
        print(f'🎣 Scraping category: {category_name}')
        books_urls = scraper.get_category_books_urls(category_url)
        num_books = len(books_urls)
        total_books += num_books
        print(f'📚 Number of books found: {num_books}')
        
        if books_urls:
            scraper.scrape_and_save_books(books_urls, category_name)
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            print(f'📚 {category_name} category processing done in {elapsed_time:.2f} seconds\n')
            summary_table.add_row(category_name, str(num_books), f'{elapsed_time:.2f}')
        else:
            print(f'❗ No books found for {category_name}. Skipping...\n')
    
    summary_table.columns[1].footer = str(total_books)
    summary_table.columns[2].footer = f'{total_time:.2f}'
    console.print(summary_table)

if __name__ == '__main__':
    main()