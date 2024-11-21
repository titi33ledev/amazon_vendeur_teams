import streamlit as st
import pandas as pd
from scrap_module import scrap, extract_product_links, extract_seller_profile_links_fast, extract_seller_data, create_dataframe

# Titre et description de l'application
st.title('Onboarding Carrefour 👀')
st.header("Bienvenue dans l'outil : Prospections Vendeurs Marketplaces")
st.markdown("Vous allez pouvoir ressortir tous les vendeurs en fonction de votre mot clé.")

# Entrée pour le mot-clé
mot_cles = st.text_input('Écris ce que tu veux rechercher', '...')

if mot_cles and mot_cles != '...':
    st.write(f'Le mot clé choisi est : {mot_cles}')

    # Processus de scraping et extraction des données
    with st.spinner("Recherche en cours... Cela peut prendre quelques minutes."):
        try:
            # Étape 1 : Rechercher un mot-clé
            st.info("Recherche des résultats pour le mot-clé...")
            soup = scrap(mot_cles)

            # Étape 2 : Extraire les liens des produits
            st.info("Extraction des liens des produits...")
            product_links = extract_product_links(soup)

            # Étape 3 : Extraire les liens des boutiques des vendeurs
            st.info("Extraction des liens des boutiques des vendeurs...")
            seller_links = extract_seller_profile_links_fast(product_links)

            # Étape 4 : Extraire les informations des vendeurs
            st.info("Récupération des informations des vendeurs...")
            seller_data = extract_seller_data(seller_links, limit=50)

            # Étape 5 : Créer un DataFrame
            st.info("Création du tableau des résultats...")
            df_sellers = create_dataframe(seller_data)

            # Afficher les données dans un tableau interactif
            st.success("Données récupérées avec succès !")
            st.dataframe(df_sellers)

            # Bouton pour télécharger les données
            try:
                csv = df_sellers.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Télécharger les données",
                    csv,
                    "vendeurs_marketplace.csv",
                    "text/csv",
                    key='download-csv'
                )
            except Exception as e:
                st.error(f"Une erreur s'est produite pendant le téléchargement : {e}")

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")

else:
    st.info("Veuillez entrer un mot-clé pour commencer.")
