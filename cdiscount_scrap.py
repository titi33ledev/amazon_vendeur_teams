#%%
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup



# Demande à l'utilisateur d'entrer un mot-clé pour la recherche
mot_cle = input("Entrez le mot-clé à rechercher : ")

# Configuration de Chrome options pour imiter un navigateur classique
chrome_options = Options()

# Initialisation du WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Accède à la page souhaitée
driver.get("https://www.cdiscount.com")  # Remplace cette URL par celle que tu veux scraper
time.sleep(3)

# Trouve l'élément du champ de recherche par son ID et entre le mot-clé
search_box = driver.find_element(By.ID, "search") 
search_box.send_keys(mot_cle)  

# Soumettre la recherche en appuyant sur Entrée
search_box.send_keys(Keys.RETURN)
time.sleep(5)

# Attendre un peu pour voir le résultat
time.sleep(5)

# N'oublie pas de fermer le driver à la fin
driver.quit()

try:
    # Attente pour s'assurer que les produits se chargent
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "prdtBILDetails"))
    )

    # Récupère le HTML complet de la page chargée par Selenium
    page_source = driver.page_source

    # Parse le HTML avec BeautifulSoup
    soup = BeautifulSoup(page_source, "html.parser")

    # Trouve les éléments contenant les liens des produits
    product_elements = soup.select(".prdtBILDetails a.jsPrdtBILA")

    # Stocke les liens dans une liste
    product_links = []
    for element in product_elements:
        link = element.get("href")
        if link:  # Vérifie que le lien n'est pas vide
            full_link = f"https:{link}" if link.startswith("//") else link
            product_links.append(full_link)

    # Affiche les liens récupérés
    print("Liens des produits récupérés :")
    for link in product_links:
        print(link)

    # Optionnel : Stocker dans un fichier pour réutilisation ultérieure
    with open("product_links.txt", "w") as f:
        for link in product_links:
            f.write(link + "\n")
    print(f"\n{len(product_links)} liens enregistrés dans 'product_links.txt'.")

except Exception as e:
    print("Erreur lors de la récupération des liens :", e)

# Ferme le navigateur
driver.quit()

