#%% Initialisation du code
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import requests
from concurrent.futures import ThreadPoolExecutor


#%% Aller sur Amazon et chercher le mot clés voulu et on récupère le code entier de la page
def scrap(mot_cles):
    # Configurer les options de Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Exécution sans interface graphique
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialiser le driver avec webdriver_manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Naviguer vers Amazon
        driver.get("https://www.amazon.fr/")

        # Accepter les cookies
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sp-cc-accept"]'))).click()

        # Effectuer la recherche
        search_bar = driver.find_element(By.XPATH, '//*[@id="twotabsearchtextbox"]')
        search_bar.send_keys(mot_cles)
        search_bar.send_keys(Keys.RETURN)

        # Attendre le chargement des résultats
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "s-main-slot")))

        # Récupérer le HTML
        page_source = driver.page_source

    finally:
        driver.quit()  # Toujours fermer le driver, même en cas d'erreur

    # Retourner la page analysée avec BeautifulSoup
    return BeautifulSoup(page_source, 'html.parser')

#%% Récupérer les liens qui renvoit vers les produits et stocker dans une liste
def extract_product_links(soup):
    
    product_links = []
    
    h2_tags = soup.find_all("h2", class_="a-size-mini a-spacing-none a-color-base s-line-clamp-4")
    
    for h2 in h2_tags:
        a_tag = h2.find("a", class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")
        if a_tag and "href" in a_tag.attrs:
            full_link = requests.compat.urljoin("https://www.amazon.fr", a_tag["href"])
            product_links.append(full_link)
            
    return product_links


#%% On récupère tous les liens qui renvoit vers la boutique des vendeurs
def extract_seller_profile_links_fast(product_links):
    seller_links = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    
    def fetch_seller_link(link):
        try:
            response = requests.get(link, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Error accessing {link}, status code {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            seller_link_tag = soup.find("a", id="sellerProfileTriggerId")
            if seller_link_tag and seller_link_tag.get("href"):
                return requests.compat.urljoin("https://www.amazon.fr", seller_link_tag["href"])
        except Exception as e:
            print(f"Error fetching seller link for {link}: {e}")
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_seller_link, product_links))
    
    # Filter out None values
    seller_links = [link for link in results if link is not None]  
    return seller_links

#%% Récupérer les informations des vendeurs
def extract_seller_data(seller_links, limit=50):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    all_seller_data = []
    
    for idx, link in enumerate(seller_links):
        if idx >= limit:
            break  # Stop après avoir atteint la limite de vendeurs
        
        data = {}
        try:
            # Effectuer la requête HTTP
            response = requests.get(link, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Erreur lors de l'accès à {link}, code {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver la section contenant les informations du vendeur
            seller_info_section = soup.find("div", id="page-section-detail-seller-info")
            if not seller_info_section:
                print(f"Aucune information vendeur trouvée pour {link}")
                continue

            # Parcourir et extraire les données spécifiques
            rows = seller_info_section.find_all("div", class_="a-row a-spacing-none")
            for row in rows:
                bold_text = row.find("span", class_="a-text-bold")
                if bold_text:
                    key = bold_text.text.strip().rstrip(":")  # Nettoyer la clé
                    value_span = bold_text.find_next_sibling("span")
                    value = value_span.text.strip() if value_span else None
                    data[key] = value
            
            # Extraire l'adresse commerciale si elle existe
            address = seller_info_section.find_all("div", class_="indent-left")
            data["Adresse commerciale"] = " ".join([line.text.strip() for line in address]) if address else None
            
            data["URL vendeur"] = link  # Ajouter l'URL pour référence

        except Exception as e:
            print(f"Erreur lors de l'extraction pour {link}: {e}")
            continue

        all_seller_data.append(data)
    
    return all_seller_data

# %% On créer un dataframe
def create_dataframe(seller_data):
    df = pd.json_normalize(seller_data)
    return df