import streamlit as st

# Configuration page
st.set_page_config(
    page_title="DIVE ANALYZER",
    page_icon="🤿",
    layout="wide"
)

st.title("🤿 DIVE ANALYZER")
st.markdown("### Analyseur de Plongées Sous-Marines")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📤 Analyser une Plongée

    Uploadez un fichier de plongée (.fit, .uddf, .xml, .dl7) pour :
    - 📊 Visualiser le profil de plongée
    - 🔬 Analyser la physique (SAC, saturation N₂)
    - ⚠️ Détecter les alertes de sécurité
    - 💾 Sauvegarder dans votre journal

    **[👉 Aller à l'analyse](#)**
    """)

    if st.button("📤 Analyser une Plongée", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📤_Analyse.py")

with col2:
    st.markdown("""
    ### 📖 Consulter le Journal

    Accédez à votre journal de plongées pour :
    - 📋 Voir l'historique complet
    - 🔍 Filtrer par site, date, profondeur
    - 📊 Statistiques agrégées
    - 🎯 Suivi progression Niveau 3

    **[👉 Voir le journal](#)**
    """)

    if st.button("📖 Consulter le Journal", use_container_width=True):
        st.switch_page("pages/2_📖_Journal.py")

st.divider()

st.info("""
💡 **Première utilisation ?**
Commencez par analyser une plongée pour la sauvegarder dans votre journal !
""")
