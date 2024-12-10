#%%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import time

#%% Fonction pour chercher des produits en fonction du mot-clé
def recherche_mots_clé(mot_clé):
    # Encoder le mot-clé pour l'utiliser dans l'URL
    url = f"https://www.e.leclerc/recherche?q={mot_clé}"

    # Headers pour simuler un navigateur
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        # Faire une requête GET
        response = requests.get(url, headers=headers)
        
        # Utiliser BeautifulSoup pour parser le HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête : {e}")
        return None

#%% Fonction pour initialiser Selenium
def init_selenium():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Mode sans interface graphique
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

#%%
# Fonction pour récupérer les données vendeur
def extraire_infos_vendeur(driver, vendeur_link):
    driver.get(vendeur_link)
    time.sleep(2)  # Temps d'attente pour charger la page
    page_source = driver.page_source

    # Parser avec BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Récupérer les informations vendeur
    details = {}
    vendeur_info = soup.find('div', class_='contract ng-star-inserted')
    if vendeur_info:
        for b in vendeur_info.find_all('b'):
            key = b.text.strip()
            value = b.next_sibling.strip() if b.next_sibling else ''
            details[key] = value

    # Extraire les données spécifiques
    infos_vendeur = {
        "Partenaire": details.get("Partenaire :", ""),
        "Nom de la Société": details.get("Nom de la Société :", ""),
        "Adresse": details.get("Adresse :", ""),
        "Tel": details.get("Tel :", ""),
        "N° RCS": details.get("N° RCS :", ""),
        "Pays de livraison": details.get("Pays de livraison :", ""),
        "Délais de livraison": details.get("Délais de livraison :", ""),
    }
    return infos_vendeur

#%% Fonction principale pour scrapper
def scrapper(mot_clé):
    # Étape 1 : Recherche du mot-clé
    soup = recherche_mots_clé(mot_clé)
    if not soup:
        print("Erreur lors de la recherche du mot-clé.")
        return

    # Étape 2 : Initialisation du driver Selenium
    driver = init_selenium()

    # Trouver les produits sur la page
    produits = soup.find_all('p', class_='seller mb-0 display-block')
    vendeur_donnees = []

    for produit in produits:
        vendeur_span = produit.find('span', class_='seller-link fake-link ng-star-inserted')
        if vendeur_span and "E.Leclerc" not in vendeur_span.text:
            try:
                # Étape 3 : Cliquer sur le vendeur pour accéder à la fiche produit
                vendeur_nom = vendeur_span.text.strip()
                print(f"Traitement du vendeur : {vendeur_nom}")

                # Trouver le lien vers la page du vendeur
                action = ActionChains(driver)
                action.click(vendeur_span).perform()
                time.sleep(2)  # Laisser le temps au chargement

                # Étape 4 : Naviguer vers la page d'information vendeur
                vendeur_infos = extraire_infos_vendeur(driver, driver.current_url)
                vendeur_donnees.append(vendeur_infos)

            except Exception as e:
                print(f"Erreur lors du traitement du vendeur {vendeur_nom} : {e}")

    driver.quit()
    return vendeur_donnees

#%%
mot_clé = "ordinateur"
x = scrapper(mot_clé)

# Afficher les résultats
for vendeur in resultats:
    print(vendeur)
# %%
