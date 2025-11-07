import streamlit as st
import database
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Paramètres",
    page_icon="⚙️",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("⚙️ Paramètres")

# === CONFIGURATION API CLAUDE ===
st.markdown("### 🤖 Configuration de l'API Claude")

st.info("""
💡 **À quoi sert la clé API Claude ?**

La clé API Claude est nécessaire pour la fonctionnalité de **reconnaissance automatique d'espèces marines**
à partir de vos photos de plongée. Sans cette clé, vous pourrez toujours ajouter manuellement les espèces
observées, mais la reconnaissance IA ne sera pas disponible.

**Comment obtenir une clé API ?**
1. Créez un compte sur [console.anthropic.com](https://console.anthropic.com)
2. Allez dans la section **API Keys**
3. Cliquez sur **Create Key**
4. Copiez votre clé et collez-la ci-dessous
""")

# Récupérer la clé actuelle
current_api_key = database.get_setting("anthropic_api_key", "")
key_configured = bool(current_api_key)

# Afficher l'état de configuration
if key_configured:
    st.success("✅ Clé API configurée - La reconnaissance d'espèces IA est active")
    # Masquer la clé pour la sécurité
    masked_key = current_api_key[:8] + "..." + current_api_key[-4:] if len(current_api_key) > 12 else "***"
    st.code(masked_key, language=None)
else:
    st.warning("⚠️ Clé API non configurée - La reconnaissance d'espèces IA est désactivée")

st.markdown("---")

# Formulaire de configuration
with st.form("api_key_form"):
    st.markdown("#### 🔑 Entrez votre clé API Claude")

    api_key_input = st.text_input(
        "Clé API Anthropic",
        type="password",
        placeholder="sk-ant-...",
        help="Votre clé API restera confidentielle et sera stockée de manière sécurisée dans votre base de données locale.",
        value=""
    )

    col1, col2 = st.columns([1, 5])

    with col1:
        submit_button = st.form_submit_button("💾 Enregistrer", type="primary", use_container_width=True)

    with col2:
        if key_configured:
            delete_button = st.form_submit_button("🗑️ Supprimer la clé", use_container_width=True)
        else:
            delete_button = False

    if submit_button:
        if api_key_input:
            # Valider le format de la clé
            if api_key_input.startswith("sk-ant-"):
                # Sauvegarder la clé
                database.save_setting("anthropic_api_key", api_key_input)
                st.success("✅ Clé API sauvegardée avec succès !")
                logger.info("Clé API Claude configurée")
                st.rerun()
            else:
                st.error("❌ Format de clé invalide. Les clés Anthropic commencent par 'sk-ant-'")
        else:
            st.warning("⚠️ Veuillez entrer une clé API")

    if delete_button:
        database.delete_setting("anthropic_api_key")
        st.success("✅ Clé API supprimée")
        logger.info("Clé API Claude supprimée")
        st.rerun()

st.markdown("---")

# === CONFIGURATION DU MODÈLE IA ===
st.markdown("### 🎯 Configuration du modèle IA")

# Récupérer le modèle actuel
current_model = database.get_setting("ai_model", "claude-3-5-haiku-20241022")

# Liste des modèles disponibles
MODEL_OPTIONS = {
    "claude-3-5-haiku-20241022": "Haiku 4.5 (Rapide et économique) ⚡ - Recommandé",
    "claude-3-5-sonnet-20241022": "Sonnet 4.5 (Équilibré) ⚖️",
    "claude-3-opus-20240229": "Opus 3 (Plus précis mais lent) 🎯"
}

st.info("""
💡 **Quel modèle choisir ?**

- **Haiku 4.5** (Recommandé) : Rapide, économique et performant pour la reconnaissance d'espèces
- **Sonnet 4.5** : Plus de détails et meilleure précision, mais plus coûteux
- **Opus 3** : Maximum de précision, mais très coûteux et plus lent
""")

# Sélection du modèle
selected_model_key = st.selectbox(
    "Modèle Claude",
    options=list(MODEL_OPTIONS.keys()),
    format_func=lambda x: MODEL_OPTIONS[x],
    index=list(MODEL_OPTIONS.keys()).index(current_model) if current_model in MODEL_OPTIONS else 0,
    help="Choisissez le modèle Claude à utiliser pour l'analyse d'images"
)

if selected_model_key != current_model:
    if st.button("💾 Sauvegarder le modèle", type="primary"):
        database.save_setting("ai_model", selected_model_key)
        st.success(f"✅ Modèle changé vers : {MODEL_OPTIONS[selected_model_key]}")
        logger.info(f"Modèle IA changé vers : {selected_model_key}")
        st.rerun()
else:
    st.success(f"✅ Modèle actuel : {MODEL_OPTIONS[current_model]}")

# Informations sur les coûts
with st.expander("💰 Informations sur les coûts"):
    st.markdown("""
    **Tarifs approximatifs par 1000 images analysées :**

    | Modèle | Prix estimé | Vitesse |
    |--------|-------------|---------|
    | Haiku 4.5 | ~$0.40 | ⚡⚡⚡ Rapide |
    | Sonnet 4.5 | ~$3.00 | ⚡⚡ Moyen |
    | Opus 3 | ~$15.00 | ⚡ Lent |

    **Recommandation** : Haiku 4.5 offre le meilleur rapport qualité/prix pour la reconnaissance d'espèces marines.
    """)

st.markdown("---")

# === AUTRES PARAMÈTRES ===
st.markdown("### 📊 Autres paramètres")

with st.expander("ℹ️ Informations sur l'application"):
    st.markdown("""
    **DIVE ANALYZER**
    Version: 2.0

    **Fonctionnalités:**
    - 📤 Analyse de fichiers de plongée (.fit, .uddf, .xml, .dl7)
    - 📖 Journal de plongées avec statistiques
    - 🗺️ Carte interactive des sites de plongée
    - 📸 Galerie de photos et vidéos
    - 🐠 Reconnaissance d'espèces marines avec IA

    **Base de données:**
    `~/dive-analyzer/dive_log.db`
    """)

with st.expander("🔒 Sécurité et confidentialité"):
    st.markdown("""
    **Vos données sont en sécurité:**

    - ✅ Toutes les données sont stockées **localement** sur votre ordinateur
    - ✅ Votre clé API est **chiffrée** dans la base de données
    - ✅ Aucune donnée n'est envoyée à des serveurs tiers (sauf lors de l'utilisation de l'API Claude)
    - ✅ L'API Claude est utilisée uniquement pour l'analyse d'images que vous choisissez

    **Utilisation de l'API Claude:**
    - Les images envoyées à Claude sont utilisées uniquement pour l'identification d'espèces
    - Anthropic ne stocke pas vos images
    - Vous pouvez supprimer votre clé API à tout moment
    """)

with st.expander("🛠️ Maintenance"):
    st.markdown("""
    **Réinitialiser les paramètres:**

    Si vous rencontrez des problèmes avec l'application, vous pouvez réinitialiser les paramètres.
    """)

    if st.button("🔄 Réinitialiser tous les paramètres", type="secondary"):
        if st.session_state.get('confirm_reset'):
            database.delete_setting("anthropic_api_key")
            st.success("✅ Paramètres réinitialisés")
            st.session_state.confirm_reset = False
            st.rerun()
        else:
            st.session_state.confirm_reset = True
            st.warning("⚠️ Êtes-vous sûr ? Cliquez à nouveau pour confirmer.")

st.markdown("---")
st.caption("💡 Besoin d'aide ? Consultez la documentation ou contactez le support.")
