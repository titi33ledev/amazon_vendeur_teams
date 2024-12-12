import streamlit as st
from test import check_proxies, fetch_search_page, extract_product_links, extract_seller_profile_links_fast_no_proxy, extract_seller_data, create_dataframe, https_proxy

# Déclarez la variable globale avant de l'utiliser
good_proxies = None

# Titre et description de l'application
st.title('Onboarding Carrefour 👀')
st.header("Bienvenue dans l'outil : Prospections Vendeurs Marketplaces")
st.markdown("Vous allez pouvoir ressortir tous les vendeurs en fonction de votre mot clé.")

# Entrée pour le mot-clé
mot_cles = st.text_input('Écris ce que tu veux rechercher', '...')

if mot_cles and mot_cles != '...':
    st.write(f'Le mot clé choisi est : {mot_cles}')

    # Charger les proxys une seule fois
    if good_proxies is None:  # Si les proxys n'ont pas encore été chargés
        st.info("Chargement et vérification des proxys...")
        with st.spinner("Vérification des proxys, cela peut prendre un moment..."):
            try:
                proxy_list = https_proxy["url"].tolist()  # Convertir les proxys en liste
                good_proxies = check_proxies(proxy_list)  # Vérifier les proxys
                if not good_proxies:
                    st.error("Aucun proxy valide trouvé. Impossible de continuer.")
                    st.stop()
            except Exception as e:
                st.error(f"Erreur lors du chargement des proxys : {e}")
                st.stop()
    else:
        st.info("Les proxys ont déjà été chargés. Pas besoin de les recharger.")

    # Processus de scraping et extraction des données
    with st.spinner("Recherche en cours... Cela peut prendre quelques minutes."):
        try:
            # Étape 1 : Construire l'URL de recherche et scraper la page
            st.info("Recherche des résultats pour le mot-clé...")
            base_url = "https://www.amazon.fr"
            search_url = f"{base_url}/s?k={mot_cles.replace(' ', '+')}"
            soup = fetch_search_page(search_url, good_proxies)

            if not soup:
                st.error("Impossible de récupérer les résultats de recherche. Veuillez réessayer.")
                st.stop()

            # Étape 2 : Extraire les liens des produits
            st.info("Extraction des liens des produits...")
            product_links = extract_product_links(soup)
            if not product_links:
                st.warning("Aucun produit trouvé. Veuillez essayer un autre mot-clé.")
                st.stop()

            # Étape 3 : Extraire les liens des boutiques des vendeurs
            st.info("Extraction des liens des boutiques des vendeurs...")
            seller_links = extract_seller_profile_links_fast_no_proxy(product_links)
            if not seller_links:
                st.warning("Aucun vendeur trouvé pour ces produits.")
                st.stop()

            # Étape 4 : Extraire les informations des vendeurs
            st.info("Récupération des informations des vendeurs...")
            seller_data = extract_seller_data(seller_links, limit=50)
            st.write(extract_seller_data(seller_links, limit=50))
            if not seller_data:
                st.warning("Aucune information vendeur trouvée.")
                st.stop()

            # Étape 5 : Créer un DataFrame
            st.info("Création du tableau des résultats...")
            df_sellers = create_dataframe(seller_data)
            if df_sellers.empty:
                st.warning("Aucune donnée disponible pour créer le tableau.")
                st.stop()

            # Afficher les données dans un tableau interactif
            st.success("Données récupérées avec succès !")
            st.dataframe(df_sellers)

            # Bouton pour télécharger les données
            csv = df_sellers.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Télécharger les données",
                csv,
                "vendeurs_marketplace.csv",
                "text/csv",
                key='download-csv'
            )

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")

else:
    st.info("Veuillez entrer un mot-clé pour commencer.")
