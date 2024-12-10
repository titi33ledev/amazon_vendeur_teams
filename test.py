#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
import lxml
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

#%%Scraper les proxys
response = requests.get("https://free-proxy-list.net/")
html_data = response.text
html_buffer = StringIO(html_data)

# Lire les données dans un DataFrame
proxy_list = pd.read_html(html_buffer)[0]
proxy_list["url"] = "http://" + proxy_list["IP Address"] + ":" + proxy_list["Port"].astype(str)

# Filtrer les proxys HTTPS
https_proxy = proxy_list[proxy_list["Https"] == "yes"]


#%% Vérifier les proxys
def check_proxies(proxy_list):
    good_proxies = set()
    url_test = "https://httpbin.org/ip"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    for proxy_url in proxy_list:
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        try:
            response = requests.get(url_test, headers=headers, proxies=proxies, timeout=2)
            if response.status_code == 200:
                good_proxies.add(proxy_url)
                print(f"Proxy {proxy_url} OK")
        except Exception:
            pass

    print(f"{len(good_proxies)} proxies fonctionnels trouvés.")
    return list(good_proxies)

#%%Utiliser un proxy aléatoire
def use_proxy_for_amazon(good_proxies, search_url, headers):
    while good_proxies:
        random_proxy = random.choice(good_proxies)
        proxies = {
            "http": random_proxy,
            "https": random_proxy,
        }
        try:
            response = requests.get(search_url, headers=headers, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print("Requête réussie avec le proxy :", random_proxy)
                return response.text  # Retourne le contenu HTML
            else:
                print(f"Proxy {random_proxy} rejeté avec code {response.status_code}")
        except Exception as e:
            print(f"Erreur avec le proxy {random_proxy}: {e}")

        # Retirer le proxy de la liste après échec
        good_proxies.remove(random_proxy)

    print("Aucun proxy valide n'est disponible.")
    return None


# %% Construire l'URL de recherche sur Amazon
def construct_search_url(base_url, mot_cles):
    mot_cles_encoded = mot_cles.replace(" ", "+")
    return f"{base_url}/s?k={mot_cles_encoded}"


# %% Récupérer le contenu de la page pour une recherche donnée
def fetch_search_page(url, good_proxies=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    # Si des proxys sont fournis
    if good_proxies:
        while good_proxies:
            random_proxy = random.choice(list(good_proxies))
            proxies = {
                "http": random_proxy,
                "https": random_proxy,
            }
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                print(f"Requête envoyée avec le proxy {random_proxy}. Code statut : {response.status_code}")
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                else:
                    print(f"Erreur avec le proxy {random_proxy}, code {response.status_code}")
                    good_proxies.remove(random_proxy)
            except Exception as e:
                print(f"Erreur avec le proxy {random_proxy}: {e}")
                good_proxies.remove(random_proxy)
        print("Aucun proxy valide disponible.")

    # Tentative sans proxy si aucun proxy ne fonctionne
    print("Tentative de récupération de la page sans proxy...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Requête envoyée sans proxy. Code statut : {response.status_code}")
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"Erreur lors de la requête sans proxy, code {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de la requête sans proxy : {e}")

    return None



# %% Extraire les liens vers les produits
def extract_product_links(soup):
    product_links = []
    # Sélectionner toutes les balises <a> avec la classe spécifique
    a_tags = soup.find_all("a", class_="a-link-normal s-no-outline")
    print(f"Nombre de balises <a> trouvées : {len(a_tags)}")

    for a_tag in a_tags:
        if "href" in a_tag.attrs:
            href = a_tag["href"]
            if "/dp/" in href:  # Vérifier que le lien correspond à un produit (contient '/dp/')
                full_link = requests.compat.urljoin("https://www.amazon.fr", href)
                product_links.append(full_link)
                print(f"Lien de produit trouvé : {full_link}")
    return product_links

#%% Récupérer les liens des profils vendeurs

def extract_seller_profile_links_fast_no_proxy(product_links):
    seller_links = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    def fetch_seller_link(link):
        try:
            response = requests.get(link, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                seller_link_tag = soup.find("a", id="sellerProfileTriggerId")
                if seller_link_tag and seller_link_tag.get("href"):
                    return requests.compat.urljoin("https://www.amazon.fr", seller_link_tag["href"])
            else:
                print(f"Erreur avec la requête, code {response.status_code}")
        except Exception as e:
            print(f"Erreur lors de la requête pour {link}: {e}")
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_seller_link, product_links))
    seller_links = [link for link in results if link is not None]
    print(f"Nombre total de liens vendeurs extraits : {len(seller_links)}")
    return seller_links

# %% Extraire les informations des vendeurs
def extract_seller_data(seller_links, limit=50):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    all_seller_data = []

    # Ajouter une barre de progression pour les vendeurs
    with tqdm(total=min(len(seller_links), limit), desc="Extraction des données vendeurs", unit="vendeur") as progress:
        for idx, link in enumerate(seller_links):
            if idx >= limit:
                break

            try:
                # Faire une requête directe sans proxy
                response = requests.get(link, headers=headers, timeout=10)
                print(f"Requête envoyée pour le lien vendeur : {link}. Code statut : {response.status_code}")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Rechercher la section avec les informations du vendeur
                    seller_info_section = soup.find("div", id="page-section-detail-seller-info")
                    if not seller_info_section:
                        print(f"Aucune information vendeur trouvée pour {link}")
                        progress.update(1)
                        continue

                    # Extraire les données
                    data = {}
                    rows = seller_info_section.find_all("div", class_="a-row a-spacing-none")
                    for row in rows:
                        bold_text = row.find("span", class_="a-text-bold")
                        if bold_text:
                            key = bold_text.text.strip().rstrip(":")
                            value_span = bold_text.find_next_sibling("span")
                            value = value_span.text.strip() if value_span else None
                            data[key] = value
                    
                    # Extraire l'adresse commerciale si disponible
                    address = seller_info_section.find_all("div", class_="indent-left")
                    data["Adresse commerciale"] = " ".join([line.text.strip() for line in address]) if address else None
                    
                    # Ajouter l'URL du vendeur
                    data["URL vendeur"] = link
                    all_seller_data.append(data)

                else:
                    print(f"Erreur lors de la requête pour {link}, code {response.status_code}")
            except Exception as e:
                print(f"Erreur lors de la requête pour {link}: {e}")
            
            # Mettre à jour la barre de progression
            progress.update(1)

    print(f"Extraction terminée : {len(all_seller_data)} vendeurs extraits.")
    return all_seller_data


    return all_seller_data

#%%
def create_dataframe(seller_data):
    if not seller_data:
        print("Aucune donnée de vendeur disponible pour créer un DataFrame.")
        return pd.DataFrame()  # Retourne un DataFrame vide si aucune donnée n'est disponible

    df = pd.json_normalize(seller_data)
    print("DataFrame créé avec succès.")
    return df
