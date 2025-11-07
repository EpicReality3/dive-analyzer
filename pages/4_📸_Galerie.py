"""
Page Galerie - Gestion et visualisation des photos et vidéos de plongée
"""

import streamlit as st
import database
import media_manager
import species_recognition
from pathlib import Path
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Galerie Média",
    page_icon="📸",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("📸 Galerie Média")

# Initialiser les répertoires média
media_manager.init_media_directories()

# Onglets principaux
tab_gallery, tab_upload, tab_species = st.tabs(["🖼️ Galerie", "⬆️ Upload", "🐠 Espèces"])

# ===== ONGLET GALERIE =====
with tab_gallery:
    st.markdown("### 🖼️ Toutes les photos et vidéos")

    # Statistiques
    stats = media_manager.get_media_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total médias", stats['total_media'])
    with col2:
        st.metric("📷 Photos", stats['total_photos'])
    with col3:
        st.metric("🎥 Vidéos", stats['total_videos'])
    with col4:
        st.metric("💾 Taille totale", f"{stats['total_size_mb']:.1f} MB")

    st.divider()

    # Filtres
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_type = st.selectbox(
            "Filtrer par type",
            ["Tous", "Photos", "Vidéos"],
            key="filter_type"
        )
    with col2:
        items_per_page = st.number_input(
            "Médias par page",
            min_value=6,
            max_value=50,
            value=12,
            step=6,
            key="items_per_page"
        )

    # Récupérer les médias
    all_media = media_manager.get_all_media(limit=100)

    # Appliquer les filtres
    if filter_type == "Photos":
        filtered_media = [m for m in all_media if m['type'] == 'photo']
    elif filter_type == "Vidéos":
        filtered_media = [m for m in all_media if m['type'] == 'video']
    else:
        filtered_media = all_media

    if not filtered_media:
        st.info("📭 Aucun média trouvé. Uploadez vos premières photos ou vidéos !")
    else:
        # Pagination
        total_items = len(filtered_media)
        total_pages = (total_items - 1) // items_per_page + 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        # Afficher les médias
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_media = filtered_media[start_idx:end_idx]

        # Grille de médias (3 colonnes)
        cols_per_row = 3
        for i in range(0, len(page_media), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(page_media):
                    media = page_media[idx]
                    with cols[j]:
                        # Afficher le média
                        if media['type'] == 'photo':
                            if media['thumbnail_path'] and Path(media['thumbnail_path']).exists():
                                st.image(media['thumbnail_path'], use_container_width=True)
                            elif Path(media['filepath']).exists():
                                st.image(media['filepath'], use_container_width=True)
                            else:
                                st.warning("Image non disponible")
                        else:  # video
                            if Path(media['filepath']).exists():
                                st.video(media['filepath'])
                            else:
                                st.warning("Vidéo non disponible")

                        # Informations
                        st.caption(f"📍 {media['site_nom']}")
                        st.caption(f"📅 {media['dive_date']}")

                        if media['description']:
                            st.caption(f"💬 {media['description']}")

                        # Bouton pour voir les détails
                        if st.button(f"ℹ️ Détails", key=f"details_{media['id']}"):
                            st.session_state.selected_media_id = media['id']

        # Pagination
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Précédent", disabled=st.session_state.current_page == 1):
                st.session_state.current_page -= 1
                st.rerun()
        with col2:
            st.markdown(f"<center>Page {st.session_state.current_page} / {total_pages}</center>",
                       unsafe_allow_html=True)
        with col3:
            if st.button("Suivant ➡️", disabled=st.session_state.current_page == total_pages):
                st.session_state.current_page += 1
                st.rerun()


# ===== ONGLET UPLOAD =====
with tab_upload:
    st.markdown("### ⬆️ Ajouter des photos ou vidéos")

    # Sélectionner une plongée
    df_dives = database.get_all_dives()

    if df_dives.empty:
        st.warning("⚠️ Aucune plongée enregistrée. Veuillez d'abord analyser une plongée.")
        if st.button("📤 Analyser une plongée"):
            st.switch_page("pages/1_📤_Analyse.py")
    else:
        # Créer une liste de choix avec date et site
        dive_choices = {}
        for _, dive in df_dives.iterrows():
            label = f"{dive['date']} - {dive['site']} ({dive['profondeur_max']:.1f}m)"
            dive_choices[label] = dive['id']

        selected_dive_label = st.selectbox(
            "🤿 Sélectionner une plongée",
            options=list(dive_choices.keys()),
            key="upload_dive_select"
        )

        selected_dive_id = dive_choices[selected_dive_label]

        # Upload de fichiers
        uploaded_files = st.file_uploader(
            "Choisir des photos ou vidéos",
            type=['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'],
            accept_multiple_files=True,
            key="media_uploader"
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} fichier(s) sélectionné(s)**")

            # Description et tags communs
            common_description = st.text_area(
                "Description (optionnelle)",
                key="common_description"
            )

            common_tags = st.text_input(
                "Tags (séparés par des virgules)",
                placeholder="ex: requin, tortue, corail",
                key="common_tags"
            )

            # Analyse IA
            enable_ai_analysis = st.checkbox(
                "🤖 Activer la reconnaissance d'espèces par IA (si disponible)",
                value=True,
                key="enable_ai"
            )

            if st.button("📤 Uploader les fichiers", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                uploaded_count = 0
                ai_detections = []

                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Upload de {uploaded_file.name}...")

                    # Sauvegarder temporairement le fichier
                    temp_path = Path(f"/tmp/{uploaded_file.name}")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    file_size = temp_path.stat().st_size

                    # Ajouter le média
                    media_id = media_manager.add_media_to_dive(
                        dive_id=selected_dive_id,
                        file_path=temp_path,
                        file_size=file_size,
                        description=common_description,
                        tags=common_tags
                    )

                    if media_id:
                        uploaded_count += 1

                        # Analyse IA si activée et c'est une photo
                        if enable_ai_analysis and temp_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                            status_text.text(f"🤖 Analyse IA de {uploaded_file.name}...")
                            detections = species_recognition.process_image_and_add_species(
                                image_path=temp_path,
                                dive_id=selected_dive_id,
                                media_id=media_id,
                                auto_add=True,
                                confidence_threshold=0.7
                            )
                            ai_detections.extend(detections)

                    # Nettoyer le fichier temporaire
                    if temp_path.exists():
                        temp_path.unlink()

                    progress_bar.progress((idx + 1) / len(uploaded_files))

                status_text.empty()
                progress_bar.empty()

                st.success(f"✅ {uploaded_count} fichier(s) uploadé(s) avec succès !")

                if ai_detections:
                    st.markdown("### 🤖 Espèces détectées par l'IA")
                    for detection in ai_detections:
                        if detection['added']:
                            st.info(f"✓ **{detection['common_name_fr']}** "
                                   f"({detection['scientific_name']}) - "
                                   f"Confiance: {detection['confidence']:.0%}")
                        else:
                            st.warning(f"⚠️ **{detection['common_name_fr']}** détecté "
                                      f"(confiance: {detection['confidence']:.0%}) "
                                      f"mais non ajouté automatiquement")


# ===== ONGLET ESPÈCES =====
with tab_species:
    st.markdown("### 🐠 Espèces observées")

    species_stats = species_recognition.get_species_stats()

    # Statistiques
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Espèces dans le catalogue", species_stats['total_species'])
    with col2:
        st.metric("👁️ Total observations", species_stats['total_observations'])

    st.divider()

    # Top espèces observées
    if species_stats['top_species']:
        st.markdown("### 🏆 Espèces les plus observées")

        for species in species_stats['top_species'][:5]:
            if species['observation_count'] > 0:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{species['common_name_fr']}** "
                            f"({species['scientific_name']})")
                with col2:
                    st.write(f"{species['observation_count']} observation(s)")

    st.divider()

    # Recherche d'espèces
    st.markdown("### 🔍 Rechercher une espèce")

    search_query = st.text_input(
        "Nom scientifique ou commun",
        placeholder="ex: requin, Amphiprion, tortue...",
        key="species_search"
    )

    if search_query:
        results = species_recognition.search_species(search_query, limit=10)

        if results:
            st.markdown(f"**{len(results)} espèce(s) trouvée(s)**")
            for species in results:
                with st.expander(f"{species['common_name_fr']} ({species['scientific_name']})"):
                    st.write(f"**Catégorie:** {species['category']}")
                    if species['conservation_status']:
                        st.write(f"**Statut de conservation:** {species['conservation_status']}")
                    if species['description']:
                        st.write(f"**Description:** {species['description']}")
                    if species['habitat']:
                        st.write(f"**Habitat:** {species['habitat']}")
                    if species['depth_range']:
                        st.write(f"**Profondeur:** {species['depth_range']}")
        else:
            st.info("Aucune espèce trouvée")

    st.divider()

    # Ajouter manuellement une espèce
    with st.expander("➕ Ajouter une nouvelle espèce au catalogue"):
        with st.form("add_species_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_scientific = st.text_input("Nom scientifique *", key="new_sci")
                new_common_fr = st.text_input("Nom commun (français)", key="new_fr")
                new_category = st.selectbox(
                    "Catégorie *",
                    ['poisson', 'corail', 'mollusque', 'crustacé',
                     'échinoderme', 'mammifère', 'reptile', 'autre'],
                    key="new_cat"
                )

            with col2:
                new_common_en = st.text_input("Nom commun (anglais)", key="new_en")
                new_conservation = st.text_input(
                    "Statut conservation",
                    placeholder="ex: LC, NT, VU, EN, CR",
                    key="new_cons"
                )
                new_habitat = st.text_input("Habitat", key="new_hab")

            new_description = st.text_area("Description", key="new_desc")
            new_depth = st.text_input("Plage de profondeur", placeholder="ex: 0-30m", key="new_depth")

            submitted = st.form_submit_button("Ajouter l'espèce", type="primary")

            if submitted:
                if not new_scientific:
                    st.error("Le nom scientifique est obligatoire")
                else:
                    species_id = species_recognition.add_species(
                        scientific_name=new_scientific,
                        common_name_fr=new_common_fr,
                        common_name_en=new_common_en,
                        category=new_category,
                        description=new_description,
                        conservation_status=new_conservation,
                        habitat=new_habitat,
                        depth_range=new_depth
                    )

                    if species_id:
                        st.success(f"✅ Espèce ajoutée avec succès ! (ID: {species_id})")
                    else:
                        st.error("❌ Erreur : cette espèce existe peut-être déjà")
