import streamlit as st
import requests
import json
from typing import Dict, Any

# Configuration de la page
st.set_page_config(
    page_title="AI Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de l'API Backend - utilise les secrets Streamlit en production
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .translation-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #ffe6e6;
        color: #d32f2f;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #d32f2f;
    }
    .success-message {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #2e7d32;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def get_supported_languages() -> Dict[str, str]:
    """Récupère les langues supportées depuis l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/languages", timeout=10)
        if response.status_code == 200:
            return response.json()["languages"]
        else:
            st.error("Erreur lors du chargement des langues supportées")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Impossible de se connecter au serveur backend: {str(e)}")
        return {}

def translate_text(text: str, source_lang: str, target_lang: str, model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """Envoie une requête de traduction à l'API"""
    try:
        payload = {
            "text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "model": model
        }
        
        response = requests.post(f"{API_BASE_URL}/translate", json=payload, timeout=30)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            error_detail = response.json().get("detail", "Erreur inconnue")
            return {"success": False, "error": error_detail}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Erreur de connexion: {str(e)}"}

def main():
    # Titre principal
    st.markdown('<h1 class="main-header">🌐 AI Translator</h1>', unsafe_allow_html=True)
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Sélection du modèle OpenAI
        model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        selected_model = st.selectbox(
            "Modèle OpenAI",
            model_options,
            help="Choisissez le modèle OpenAI à utiliser pour la traduction"
        )
        
        st.markdown("---")
        
        # Informations sur l'application
        st.markdown("""
        ### 📝 À propos
        Cette application utilise l'API OpenAI pour traduire du texte entre différentes langues.
        
        **Fonctionnalités:**
        - Support de 12+ langues
        - Traduction en temps réel
        - Interface intuitive
        - Multiple modèles OpenAI
        """)
        
        # Statut de connexion à l'API
        try:
            health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health_response.status_code == 200:
                st.success("🟢 Backend connecté")
                st.info(f"URL: {API_BASE_URL}")
            else:
                st.error("🔴 Backend non disponible")
        except Exception as e:
            st.error(f"🔴 Impossible de joindre le backend: {str(e)}")
    
    # Interface principale
    col1, col2 = st.columns(2)
    
    # Récupération des langues supportées
    languages = get_supported_languages()
    
    if not languages:
        st.error("Impossible de charger les langues supportées. Vérifiez la connexion au backend.")
        st.info(f"API URL configurée: {API_BASE_URL}")
        return
    
    # Interface de sélection des langues
    with col1:
        st.subheader("🎯 Langue source")
        source_lang = st.selectbox(
            "Sélectionnez la langue source",
            options=list(languages.keys()),
            format_func=lambda x: f"{languages[x]} ({x})",
            key="source_lang"
        )
    
    with col2:
        st.subheader("🎯 Langue cible")
        target_lang = st.selectbox(
            "Sélectionnez la langue cible",
            options=list(languages.keys()),
            format_func=lambda x: f"{languages[x]} ({x})",
            key="target_lang"
        )
    
    # Bouton d'échange des langues
    col_center = st.columns([1, 1, 1])[1]
    with col_center:
        if st.button("🔄 Échanger les langues", use_container_width=True):
            # Échanger les langues dans le session state
            st.session_state.source_lang, st.session_state.target_lang = st.session_state.target_lang, st.session_state.source_lang
            st.rerun()
    
    st.markdown("---")
    
    # Zone de saisie du texte
    st.subheader("📝 Texte à traduire")
    text_to_translate = st.text_area(
        "Entrez votre texte ici (max 5000 caractères)",
        height=150,
        max_chars=5000,
        placeholder="Tapez ou collez votre texte ici..."
    )
    
    # Compteur de caractères
    char_count = len(text_to_translate)
    st.caption(f"Caractères: {char_count}/5000")
    
    # Bouton de traduction
    col_translate = st.columns([1, 2, 1])[1]
    with col_translate:
        translate_button = st.button(
            "🚀 Traduire",
            use_container_width=True,
            type="primary",
            disabled=not text_to_translate.strip() or source_lang == target_lang
        )
    
    # Validation et traduction
    if translate_button:
        if source_lang == target_lang:
            st.warning("⚠️ Les langues source et cible doivent être différentes")
        elif not text_to_translate.strip():
            st.warning("⚠️ Veuillez entrer du texte à traduire")
        else:
            with st.spinner("🔄 Traduction en cours..."):
                result = translate_text(text_to_translate, source_lang, target_lang, selected_model)
                
                if result["success"]:
                    data = result["data"]
                    
                    # Affichage du résultat
                    st.markdown("### 🎉 Résultat de la traduction")
                    
                    # Texte original
                    st.markdown("**Texte original:**")
                    st.markdown(f'<div class="translation-container">{data["original_text"]}</div>', 
                              unsafe_allow_html=True)
                    
                    # Texte traduit
                    st.markdown("**Traduction:**")
                    st.markdown(f'<div class="translation-container">{data["translated_text"]}</div>', 
                              unsafe_allow_html=True)
                    
                    # Informations sur la traduction
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.info(f"**Langue source:** {languages[data['source_language']]}")
                    with col_info2:
                        st.info(f"**Langue cible:** {languages[data['target_language']]}")
                    
                    # Bouton de copie
                    if st.button("📋 Copier la traduction", use_container_width=True):
                        st.session_state.clipboard = data["translated_text"]
                        st.success("✅ Traduction copiée !")
                        
                else:
                    st.markdown(f'<div class="error-message">❌ Erreur: {result["error"]}</div>', 
                              unsafe_allow_html=True)

if __name__ == "__main__":
    main()