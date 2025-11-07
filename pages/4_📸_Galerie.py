"""
Page Galerie - Gestion et visualisation des photos et vidéos de plongée
"""

import streamlit as st
import database
import media_manager
import species_recognition
import species_api
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

# Lien vers le catalogue d'espèces
if st.button("🐠 Voir le Catalogue des Espèces", use_container_width=True, type="secondary"):
    st.switch_page("pages/7_🐠_Catalogue_Espèces.py")

st.divider()

# Onglets principaux
tab_gallery, tab_upload = st.tabs(["🖼️ Galerie", "⬆️ Upload"])

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

                        # Annotation complète : description + espèces
                        with st.expander("📝 Annotation & Espèces", expanded=bool(media['description'])):

                            # === SECTION 1 : DESCRIPTION ===
                            st.markdown("#### 📄 Description")
                            current_description = media['description'] or ""

                            # Zone de texte pour la description
                            new_description = st.text_area(
                                "Description de l'image",
                                value=current_description,
                                key=f"desc_{media['id']}",
                                height=80,
                                placeholder="Décrivez l'ambiance, le contexte, les éléments visuels..."
                            )

                            # Boutons pour la description
                            desc_col1, desc_col2 = st.columns(2)
                            with desc_col1:
                                if media['type'] == 'photo':
                                    if st.button("🤖 Générer description IA", key=f"gen_desc_{media['id']}", use_container_width=True):
                                        api_key = database.get_setting("anthropic_api_key", "")
                                        if not api_key:
                                            st.error("⚠️ Clé API non configurée")
                                        else:
                                            with st.spinner("Génération..."):
                                                filepath = Path(media['filepath'])
                                                if filepath.exists():
                                                    generated_desc = species_recognition.generate_image_description(filepath)
                                                    if generated_desc:
                                                        if media_manager.update_media_description(media['id'], generated_desc):
                                                            st.success("✅ Description générée !")
                                                            st.rerun()
                            with desc_col2:
                                if st.button("💾 Sauvegarder description", key=f"save_desc_{media['id']}", use_container_width=True):
                                    if media_manager.update_media_description(media['id'], new_description):
                                        st.success("✅ Sauvegardée !")
                                        st.rerun()

                            st.divider()

                            # === SECTION 2 : ESPÈCES IDENTIFIÉES ===
                            st.markdown("#### 🐠 Espèces identifiées sur cette photo")

                            # Récupérer les espèces déjà identifiées sur ce média
                            media_species = species_recognition.get_media_species(media['id'])

                            if media_species:
                                st.markdown(f"**{len(media_species)} espèce(s) identifiée(s) :**")
                                for sp in media_species:
                                    confidence_badge = ""
                                    if sp['confidence_score']:
                                        confidence_badge = f" ({sp['confidence_score']:.0%})"

                                    source_icon = {
                                        'ai': '🤖',
                                        'manual': '✍️',
                                        'verified': '✅'
                                    }.get(sp['detected_by'], '❓')

                                    # Créer une colonne pour l'espèce et le bouton de validation
                                    sp_col1, sp_col2 = st.columns([4, 1])

                                    with sp_col1:
                                        st.write(f"{source_icon} **{sp['common_name_fr'] or sp['scientific_name']}** "
                                                f"({sp['scientific_name']}){confidence_badge}")

                                    with sp_col2:
                                        # Bouton de validation WoRMS
                                        if st.button("🔍", key=f"validate_{sp['id']}_{media['id']}",
                                                   help="Valider avec WoRMS"):
                                            st.session_state[f'show_validation_{sp["id"]}_{media["id"]}'] = True

                                    # Afficher les résultats de validation si demandé
                                    if st.session_state.get(f'show_validation_{sp["id"]}_{media["id"]}', False):
                                        with st.spinner("Validation WoRMS en cours..."):
                                            comparison = species_api.compare_with_ai_detection(
                                                sp['scientific_name'],
                                                sp['confidence_score'] or 0.0
                                            )

                                            # Afficher les résultats
                                            if comparison['worms_found']:
                                                details = comparison['details']

                                                # Badge de qualité
                                                if comparison['match_quality'] == 'perfect':
                                                    st.success("✅ **Validation WoRMS : PARFAITE**")
                                                elif comparison['match_quality'] == 'synonym':
                                                    st.warning(f"⚠️ **Synonyme détecté** - Nom valide : **{comparison['recommended_name']}**")
                                                else:
                                                    st.info(f"ℹ️ **Statut : {comparison['worms_status']}**")

                                                # Informations taxonomiques
                                                st.markdown("**📚 Informations WoRMS**")
                                                st.markdown(f"**AphiaID:** {details['details']['aphia_id']}")
                                                st.markdown(f"**Nom scientifique:** {details['details']['scientific_name']}")
                                                if details['details']['authority']:
                                                    st.markdown(f"**Autorité:** {details['details']['authority']}")

                                                # Taxonomie
                                                tax_parts = []
                                                if details['details'].get('family'):
                                                    tax_parts.append(f"Famille: {details['details']['family']}")
                                                if details['details'].get('order'):
                                                    tax_parts.append(f"Ordre: {details['details']['order']}")
                                                if details['details'].get('class'):
                                                    tax_parts.append(f"Classe: {details['details']['class']}")

                                                if tax_parts:
                                                    st.markdown(" | ".join(tax_parts))

                                                # Noms communs
                                                if details['details'].get('common_names'):
                                                    names_str = ", ".join(details['details']['common_names'])
                                                    st.markdown(f"**Noms communs:** {names_str}")

                                                # Habitat
                                                habitat_tags = []
                                                if details['details'].get('isMarine'):
                                                    habitat_tags.append("🌊 Marin")
                                                if details['details'].get('isBrackish'):
                                                    habitat_tags.append("💧 Saumâtre")
                                                if details['details'].get('isFreshwater'):
                                                    habitat_tags.append("🏞️ Eau douce")

                                                if habitat_tags:
                                                    st.markdown(" ".join(habitat_tags))

                                                # Lien WoRMS
                                                if details['details'].get('url'):
                                                    st.markdown(f"[🔗 Voir sur WoRMS]({details['details']['url']})")

                                                st.markdown("---")

                                                # Recommandation
                                                if comparison['should_verify']:
                                                    st.warning("💡 **Recommandation:** Vérification manuelle conseillée "
                                                             f"(confiance IA: {sp['confidence_score']:.0%})")
                                            else:
                                                st.error("❌ **Espèce non trouvée dans WoRMS**")
                                                st.info("💡 Cette espèce n'est pas référencée dans la base de données "
                                                       "marine mondiale. Vérifiez l'orthographe du nom scientifique.")
                            else:
                                st.info("Aucune espèce identifiée sur cette photo")

                            st.markdown("---")

                            # Boutons d'action pour les espèces
                            sp_col1, sp_col2, sp_col3 = st.columns(3)

                            with sp_col1:
                                # Analyse IA des espèces
                                if media['type'] == 'photo':
                                    if st.button("🤖 Analyser espèces IA", key=f"ai_sp_{media['id']}", use_container_width=True):
                                        api_key = database.get_setting("anthropic_api_key", "")
                                        if not api_key:
                                            st.error("⚠️ Clé API non configurée")
                                        else:
                                            with st.spinner("Analyse IA en cours..."):
                                                filepath = Path(media['filepath'])
                                                if filepath.exists():
                                                    detected_species = species_recognition.analyze_image_with_ai(filepath)

                                                    if detected_species:
                                                        added_count = 0
                                                        for sp in detected_species:
                                                            species_id = species_recognition.add_or_get_species(
                                                                scientific_name=sp.get('scientific_name'),
                                                                common_name_fr=sp.get('common_name_fr'),
                                                                common_name_en=sp.get('common_name_en'),
                                                                category=sp.get('category')
                                                            )

                                                            if species_id:
                                                                if species_recognition.add_species_to_dive(
                                                                    dive_id=media['dive_id'],
                                                                    species_id=species_id,
                                                                    media_id=media['id'],
                                                                    confidence_score=sp.get('confidence', 0.5),
                                                                    detected_by='ai'
                                                                ):
                                                                    added_count += 1

                                                        st.success(f"✅ {added_count} espèce(s) ajoutée(s) !")
                                                        st.rerun()
                                                    else:
                                                        st.warning("Aucune espèce détectée")

                            with sp_col2:
                                # Ajouter manuellement une espèce
                                if st.button("➕ Ajouter espèce", key=f"add_sp_{media['id']}", use_container_width=True):
                                    st.session_state[f'show_add_species_{media["id"]}'] = True

                            with sp_col3:
                                # Accès au catalogue
                                if st.button("📚 Catalogue", key=f"catalogue_{media['id']}", use_container_width=True):
                                    st.session_state[f'show_catalogue_{media["id"]}'] = True

                            # Formulaire d'ajout manuel d'espèce
                            if st.session_state.get(f'show_add_species_{media["id"]}', False):
                                st.markdown("##### Ajouter une espèce")

                                with st.form(key=f"add_species_form_{media['id']}"):
                                    # Recherche d'espèce existante
                                    search_sp = st.text_input("Rechercher une espèce", key=f"search_sp_{media['id']}")

                                    selected_species_id = None
                                    if search_sp and len(search_sp) >= 2:
                                        results = species_recognition.search_species(search_sp, limit=5)
                                        if results:
                                            species_choices = {
                                                f"{sp['common_name_fr']} ({sp['scientific_name']})": sp['id']
                                                for sp in results
                                            }
                                            selected = st.selectbox("Sélectionner", options=list(species_choices.keys()))
                                            if selected:
                                                selected_species_id = species_choices[selected]

                                    quantity = st.number_input("Quantité observée", min_value=1, value=1)
                                    notes = st.text_input("Notes (optionnel)")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        submit = st.form_submit_button("✅ Ajouter", use_container_width=True)
                                    with col2:
                                        cancel = st.form_submit_button("❌ Annuler", use_container_width=True)

                                    if submit and selected_species_id:
                                        if species_recognition.add_species_to_dive(
                                            dive_id=media['dive_id'],
                                            species_id=selected_species_id,
                                            media_id=media['id'],
                                            quantity=quantity,
                                            notes=notes,
                                            detected_by='manual'
                                        ):
                                            st.success("✅ Espèce ajoutée !")
                                            st.session_state[f'show_add_species_{media["id"]}'] = False
                                            st.rerun()

                                    if cancel:
                                        st.session_state[f'show_add_species_{media["id"]}'] = False
                                        st.rerun()

                            # Section Catalogue d'espèces
                            if st.session_state.get(f'show_catalogue_{media["id"]}', False):
                                st.markdown("---")
                                st.markdown("##### 📚 Catalogue des Espèces Marines")

                                # Mini catalogue avec recherche et ajout rapide
                                cat_tab1, cat_tab2, cat_tab3 = st.tabs(["🔍 Rechercher", "➕ Créer nouvelle espèce", "📊 Statistiques"])

                                with cat_tab1:
                                    st.markdown("**Rechercher dans le catalogue**")

                                    # Recherche
                                    search_query = st.text_input(
                                        "Nom scientifique ou commun",
                                        key=f"cat_search_{media['id']}",
                                        placeholder="Ex: Amphiprion, poisson-clown..."
                                    )

                                    if search_query and len(search_query) >= 2:
                                        results = species_recognition.search_species(search_query, limit=10)

                                        if results:
                                            st.markdown(f"**{len(results)} résultat(s) trouvé(s) :**")

                                            for sp in results:
                                                with st.expander(f"{sp['common_name_fr'] or sp['scientific_name']} ({sp['scientific_name']})"):
                                                    st.markdown(f"**Catégorie:** {sp['category']}")
                                                    if sp['description']:
                                                        st.markdown(f"**Description:** {sp['description'][:200]}...")

                                                    # Bouton pour valider avec WoRMS
                                                    if st.button("🔍 Valider avec WoRMS",
                                                               key=f"worms_val_{sp['id']}_{media['id']}"):
                                                        with st.spinner("Recherche WoRMS..."):
                                                            worms_info = species_api.get_species_info_summary(sp['scientific_name'])
                                                            if worms_info:
                                                                st.markdown(worms_info)
                                                            else:
                                                                st.warning("Espèce non trouvée dans WoRMS")

                                                    # Bouton pour ajouter à cette photo
                                                    if st.button("➕ Ajouter à cette photo",
                                                               key=f"add_cat_{sp['id']}_{media['id']}",
                                                               type="primary"):
                                                        if species_recognition.add_species_to_dive(
                                                            dive_id=media['dive_id'],
                                                            species_id=sp['id'],
                                                            media_id=media['id'],
                                                            detected_by='manual'
                                                        ):
                                                            st.success("✅ Espèce ajoutée à cette photo !")
                                                            st.session_state[f'show_catalogue_{media["id"]}'] = False
                                                            st.rerun()
                                        else:
                                            st.info("Aucune espèce trouvée. Essayez de créer une nouvelle espèce.")

                                with cat_tab2:
                                    st.markdown("**Créer une nouvelle espèce dans le catalogue**")

                                    with st.form(key=f"new_species_catalogue_{media['id']}"):
                                        new_sci = st.text_input("Nom scientifique *", key=f"new_sci_{media['id']}")
                                        new_fr = st.text_input("Nom français", key=f"new_fr_{media['id']}")
                                        new_en = st.text_input("Nom anglais", key=f"new_en_{media['id']}")
                                        new_cat = st.selectbox(
                                            "Catégorie *",
                                            ['poisson', 'corail', 'mollusque', 'crustacé',
                                             'échinoderme', 'mammifère', 'reptile', 'autre'],
                                            key=f"new_cat_{media['id']}"
                                        )

                                        # Recherche WoRMS pour aide
                                        if new_sci and len(new_sci) >= 3:
                                            st.info("💡 Validation WoRMS recommandée après création")

                                        submit_new = st.form_submit_button("➕ Créer l'espèce", type="primary")

                                        if submit_new and new_sci:
                                            # Créer l'espèce
                                            species_id = species_recognition.add_species(
                                                scientific_name=new_sci,
                                                common_name_fr=new_fr,
                                                common_name_en=new_en,
                                                category=new_cat
                                            )

                                            if species_id:
                                                st.success(f"✅ Espèce créée ! (ID: {species_id})")

                                                # Proposer de l'ajouter à cette photo
                                                if st.button("➕ Ajouter à cette photo",
                                                           key=f"add_new_{species_id}_{media['id']}"):
                                                    if species_recognition.add_species_to_dive(
                                                        dive_id=media['dive_id'],
                                                        species_id=species_id,
                                                        media_id=media['id'],
                                                        detected_by='manual'
                                                    ):
                                                        st.session_state[f'show_catalogue_{media["id"]}'] = False
                                                        st.rerun()
                                            else:
                                                st.error("❌ Erreur : espèce peut-être déjà existante")

                                with cat_tab3:
                                    st.markdown("**Statistiques du catalogue**")
                                    stats = species_recognition.get_species_stats()

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("📚 Espèces cataloguées", stats['total_species'])
                                    with col2:
                                        st.metric("👁️ Observations totales", stats['total_observations'])

                                # Bouton pour fermer le catalogue
                                if st.button("❌ Fermer le catalogue", key=f"close_cat_{media['id']}"):
                                    st.session_state[f'show_catalogue_{media["id"]}'] = False
                                    st.rerun()

                        # Bouton suppression du média
                        if st.button(f"🗑️ Supprimer ce média", key=f"delete_{media['id']}", type="secondary", use_container_width=True):
                            if media_manager.delete_media(media['id']):
                                st.success(f"✅ Média supprimé !")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression")

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
