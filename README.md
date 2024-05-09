# UTILISEZ LES BASES DE PYTHON POUR REALISER UNE ANALYSE DE MARCHE

Ce projet consiste à utiliser les bases de Python pour réaliser une analyse de marché. Il s'agit d'explorer et d'analyser des données de marché afin de tirer des insights et des conclusions utiles. Le code développé dans ce projet permettra de manipuler les données, de les visualiser et d'effectuer des calculs statistiques pour mieux comprendre le marché.

# Book Scraper

## Description

C'est un script fait en Python qui permet de scraper les livres (et leurs datas) du site [Books to Scrape](http://books.toscrape.com/).
Il permet d'étapblir un processus ETL : extraire, transformer et charger les données dans un fichier CSV.

## Prérequis

-   Python 3.7 ou même plus récent
-   pip (gestionnaire de paquets Python)
-   pipenv (facultatif, mais recommandé)

## Installation

### Utilisation de pipenv (recommandé)

`Pipenv` gère à la fois les dépendances du projet et l'environnement virtuel. Il m'a été recommandé pour une meilleure isolation et une gestion simplifiée des dépendances.

```bash
# Cloner le dépôt Git
git clone https://github.com/ThomasDpr/oc-projet-2-analyse-de-marche.git

# Se rendre dans le répertoire du projet
cd oc-projet-2-analyse-de-marche

# Installer pipenv si ce n'est pas déjà fait
pip install pipenv

# Installer les dépendances du projet et créer l'environnement virtuel
pipenv install

# Activer l'environnement virtuel
pipenv shell
```

### Utilisation de pip (classique)

```bash
# Cloner le dépôt Git
git clone https://github.com/ThomasDpr/oc-projet-2-analyse-de-marche.git

# Se rendre dans le répertoire du projet
cd oc-projet-2-analyse-de-marche

# Installer les dépendances du projet
pip install -r requirements.txt
```

## Exécution

```bash
# Pour lancer le script
python book_scraper.py
# ou
python3 book_scraper.py
# ou
py book_scraper.py
```

-   Les images des couvertures des livres seront téléchargées et enregistrées dans un dossier `images` à la racine du projet.
-   Les données des livres seront enregistrées dans dossier `datas` à la racine du projet sous format CSV.
