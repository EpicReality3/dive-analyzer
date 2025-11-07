import streamlit as st
import database
import media_manager
import species_recognition
import pandas as pd
from pathlib import Path
from config import config
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Journal de Plongée",
    page_icon="📖",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("📖 Journal de Plongée")

# Récupérer toutes les plongées
df_dives = database.get_all_dives()

if df_dives.empty:
    st.info("""
    📭 **Votre journal est vide**

    Commencez par analyser une plongée pour la sauvegarder !
    """)

    if st.button("📤 Analyser une plongée", type="primary"):
        st.switch_page("pages/1_📤_Analyse.py")
else:
    # === STATISTIQUES GLOBALES ===
    st.markdown("### 📊 Statistiques Globales")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🤿 Plongées", len(df_dives))

    with col2:
        prof_max_globale = df_dives['profondeur_max'].max()
        st.metric("⬇️ Prof. Max", f"{prof_max_globale:.1f} m")

    with col3:
        temps_total = df_dives['duree_minutes'].sum()
        heures_total = int(temps_total // 60)
        minutes_total = int(temps_total % 60)
        st.metric("⏱️ Temps Total", f"{heures_total}h{minutes_total:02d}min")

    with col4:
        sac_median = df_dives['sac'].median()
        if pd.notna(sac_median):
            st.metric("🫁 SAC Médian", f"{sac_median:.1f} L/min")
        else:
            st.metric("🫁 SAC Médian", "N/A")

    with col5:
        rating_moyen = df_dives['rating'].mean()
        if pd.notna(rating_moyen):
            st.metric("⭐ Note Moyenne", f"{rating_moyen:.1f}/5")
        else:
            st.metric("⭐ Note Moyenne", "N/A")

    st.divider()

    # === FILTRES ===
    st.markdown("### 🔍 Filtres")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Liste des sites uniques
        sites_uniques = sorted(df_dives['site'].dropna().unique())
        site_filtre = st.multiselect(
            "📍 Site",
            options=["Tous"] + sites_uniques,
            default=["Tous"]
        )

    with col2:
        date_debut = st.date_input("📅 Date début", value=None)

    with col3:
        date_fin = st.date_input("📅 Date fin", value=None)

    # Appliquer filtres
    df_filtered = df_dives.copy()

    if "Tous" not in site_filtre and site_filtre:
        df_filtered = df_filtered[df_filtered['site'].isin(site_filtre)]

    if date_debut:
        df_filtered = df_filtered[pd.to_datetime(df_filtered['date']).dt.date >= date_debut]

    if date_fin:
        df_filtered = df_filtered[pd.to_datetime(df_filtered['date']).dt.date <= date_fin]

    st.divider()

    # === TABLEAU PLONGÉES ===
    st.markdown(f"### 📋 Plongées ({len(df_filtered)} résultats)")

    # Formater le DataFrame pour affichage
    df_display = df_filtered.copy()
    df_display['date'] = pd.to_datetime(df_display['date']).dt.strftime('%d/%m/%Y %H:%M')
    df_display['profondeur_max'] = df_display['profondeur_max'].round(1)
    df_display['duree_minutes'] = df_display['duree_minutes'].round(0)

    if 'sac' in df_display.columns:
        df_display['sac'] = df_display['sac'].round(1)

    # Colonnes à afficher
    colonnes_affichage = ['date', 'site', 'buddy', 'dive_type', 'profondeur_max', 'duree_minutes', 'rating']
    if 'sac' in df_display.columns:
        colonnes_affichage.append('sac')

    # Renommer pour affichage
    df_display = df_display[colonnes_affichage].rename(columns={
        'date': 'Date',
        'site': 'Site',
        'buddy': 'Buddy',
        'dive_type': 'Type',
        'profondeur_max': 'Prof Max (m)',
        'duree_minutes': 'Durée (min)',
        'rating': 'Note',
        'sac': 'SAC (L/min)'
    })

    # Afficher avec sélection de ligne
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # === DÉTAIL PLONGÉE SÉLECTIONNÉE ===
    st.markdown("### 🔎 Détail d'une Plongée")

    # Sélecteur de plongée
    plongee_ids = df_filtered['id'].tolist()
    plongee_labels = [f"{row['date']} - {row['site']}" for _, row in df_filtered.iterrows()]

    plongee_selectionnee = st.selectbox(
        "Sélectionnez une plongée",
        options=plongee_ids,
        format_func=lambda x: plongee_labels[plongee_ids.index(x)]
    )

    if plongee_selectionnee:
        # Charger les données complètes
        plongee_complete = database.get_dive_by_id(plongee_selectionnee)

        if plongee_complete:
            # Tabs pour séparer Vue / Profil / Édition
            tab_vue, tab_profil, tab_edit = st.tabs(["📋 Informations", "📊 Profil Graphique", "✏️ Éditer"])

            # === TAB VUE ===
            with tab_vue:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### 📍 Informations Générales")
                    st.markdown(f"""
                    **Date :** {plongee_complete['date']}
                    **Site :** {plongee_complete['site_nom']}
                    **Buddy :** {plongee_complete['buddy_nom'] if plongee_complete['buddy_nom'] else 'Solo'}
                    **Type :** {plongee_complete['dive_type']}
                    **Note :** {'⭐' * int(plongee_complete['rating'])} ({plongee_complete['rating']}/5)
                    """)

                    st.markdown("#### 🌊 Conditions")
                    visibilite_str = f"{plongee_complete['visibilite_metres']} m" if plongee_complete['visibilite_metres'] else 'N/A'
                    st.markdown(f"""
                    **Houle :** {plongee_complete['houle'] if plongee_complete['houle'] else 'N/A'}
                    **Visibilité :** {visibilite_str}
                    **Courant :** {plongee_complete['courant'] if plongee_complete['courant'] else 'N/A'}
                    """)

                with col2:
                    st.markdown("#### 📊 Données Techniques")
                    sac_str = f"{plongee_complete['sac']:.1f} L/min" if plongee_complete['sac'] else 'N/A'
                    temp_str = f"{plongee_complete['temperature_min']:.1f} °C" if plongee_complete['temperature_min'] else 'N/A'
                    temps_fond_str = f"{plongee_complete['temps_fond_minutes']:.1f} min" if plongee_complete.get('temps_fond_minutes') else 'N/A'
                    vitesse_str = f"{plongee_complete['vitesse_remontee_max']:.1f} m/min" if plongee_complete.get('vitesse_remontee_max') else 'N/A'
                    st.markdown(f"""
                    **Profondeur max :** {plongee_complete['profondeur_max']:.1f} m
                    **Durée totale :** {plongee_complete['duree_minutes']:.0f} min
                    **Temps de fond :** {temps_fond_str}
                    **SAC :** {sac_str}
                    **Temp min :** {temp_str}
                    **Vitesse remontée max :** {vitesse_str}
                    """)

                if plongee_complete['tags']:
                    st.markdown("#### 🏷️ Tags")
                    st.markdown(" • ".join(plongee_complete['tags']))

                if plongee_complete['notes']:
                    st.markdown("#### 📝 Notes")
                    st.markdown(plongee_complete['notes'])

                # === BOUTON EXPORT PDF ===
                st.divider()
                if st.button("📄 Exporter en PDF", type="primary", key=f"export_pdf_{plongee_selectionnee}", use_container_width=True):
                    import pdf_export

                    with st.spinner("⏳ Génération du PDF en cours..."):
                        pdf_path = pdf_export.generate_dive_pdf(plongee_selectionnee)

                        if pdf_path:
                            # Lire le fichier PDF généré
                            with open(pdf_path, 'rb') as pdf_file:
                                pdf_bytes = pdf_file.read()

                            # Proposer le téléchargement
                            st.download_button(
                                label="💾 Télécharger le PDF",
                                data=pdf_bytes,
                                file_name=pdf_path.name,
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success(f"✅ PDF généré avec succès : {pdf_path.name}")
                        else:
                            st.error("❌ Erreur lors de la génération du PDF")

                # === MÉDIAS ASSOCIÉS ===
                st.divider()
                dive_media = media_manager.get_dive_media(plongee_selectionnee)

                if dive_media:
                    st.markdown(f"#### 📸 Médias ({len(dive_media)})")

                    # Afficher les médias en grille
                    cols_per_row = 3
                    for i in range(0, len(dive_media), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j in range(cols_per_row):
                            idx = i + j
                            if idx < len(dive_media):
                                media = dive_media[idx]
                                with cols[j]:
                                    if media['type'] == 'photo':
                                        if media['thumbnail_path'] and Path(media['thumbnail_path']).exists():
                                            st.image(media['thumbnail_path'], use_container_width=True)
                                        elif Path(media['filepath']).exists():
                                            st.image(media['filepath'], use_container_width=True)
                                    else:  # video
                                        if Path(media['filepath']).exists():
                                            st.video(media['filepath'])

                                    if media['description']:
                                        st.caption(media['description'])
                else:
                    st.info("📷 Aucun média pour cette plongée. Ajoutez des photos/vidéos depuis la page Galerie !")

                # === ESPÈCES OBSERVÉES ===
                st.divider()
                dive_species = species_recognition.get_dive_species(plongee_selectionnee)

                if dive_species:
                    st.markdown(f"#### 🐠 Espèces Observées ({len(dive_species)})")

                    for species in dive_species:
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            emoji_map = {
                                'poisson': '🐟',
                                'corail': '🪸',
                                'mollusque': '🐚',
                                'crustacé': '🦀',
                                'échinoderme': '⭐',
                                'mammifère': '🐋',
                                'reptile': '🐢',
                                'autre': '🌊'
                            }
                            emoji = emoji_map.get(species['category'], '🌊')
                            st.write(f"{emoji} {species['common_name_fr'] or species['scientific_name']}")

                        with col2:
                            if species['quantity'] > 1:
                                st.caption(f"Qté: {species['quantity']}")

                        with col3:
                            if species['detected_by'] == 'ai':
                                st.caption("🤖 IA")
                            elif species['detected_by'] == 'verified':
                                st.caption("✓ Vérifié")
                else:
                    st.info("🐠 Aucune espèce enregistrée. Utilisez la page Espèces pour ajouter vos observations !")

            # === TAB PROFIL GRAPHIQUE ===
            with tab_profil:
                # Vérifier si le fichier existe
                file_path = Path(plongee_complete['fichier_original_path'])

                if file_path.exists():
                    st.markdown("#### 📊 Profil de Plongée Complet")

                    try:
                        # Importer les modules nécessaires
                        import parser as dive_parser
                        import visualizer
                        import analyzer

                        # === PHASE 2 : Essayer de charger depuis le cache d'abord ===
                        df = database.get_dive_cache(plongee_selectionnee)

                        if df is None:
                            # Cache miss : parser le fichier
                            logger.info(f"Cache miss pour plongée {plongee_selectionnee}, parsing du fichier...")

                            # Créer un objet fichier simulé pour le parser
                            class FakeUploadedFile:
                                def __init__(self, path):
                                    self.name = path.name
                                    self._content = None
                                    self._path = path

                                def read(self):
                                    if self._content is None:
                                        with open(self._path, 'rb') as f:
                                            self._content = f.read()
                                    return self._content

                                def seek(self, pos):
                                    pass

                            fake_file = FakeUploadedFile(file_path)

                            # Parser le fichier
                            df = dive_parser.parse_dive_file(fake_file)

                            # Sauvegarder en cache pour la prochaine fois
                            if not df.empty:
                                database.save_dive_cache(plongee_selectionnee, df)
                                logger.info(f"DataFrame mis en cache pour plongée {plongee_selectionnee}")
                        else:
                            # Cache hit : afficher un message de succès
                            st.success("⚡ Données chargées depuis le cache (rapide!)")
                            logger.info(f"Cache hit pour plongée {plongee_selectionnee}")

                        if not df.empty:
                            # Afficher le graphique
                            fig = visualizer.plot_depth_profile(df)
                            st.plotly_chart(fig, use_container_width=True)

                            # Bandeau sécurité
                            speeds = visualizer.calculate_ascent_speed(df)
                            max_speed = speeds.max()
                            if max_speed < 10.0:
                                st.success(f"🟢 **Plongée sécuritaire** — Vitesse remontée max : {max_speed:.1f} m/min")
                            else:
                                st.error(f"🔴 **Alerte** — Vitesse remontée max : {max_speed:.1f} m/min (> 10 m/min)")

                            # Stats rapides
                            st.divider()
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                paliers = visualizer.detect_safety_stops(df)
                                st.metric("🛑 Paliers Détectés", len(paliers))

                            with col2:
                                bottom_time = analyzer.calculate_bottom_time(df)
                                st.metric("⏱️ Temps de Fond", f"{bottom_time['temps_fond_minutes']:.1f} min")

                            with col3:
                                avg_depth = df['profondeur_metres'].mean()
                                st.metric("📊 Prof. Moyenne", f"{avg_depth:.1f} m")

                        else:
                            st.error("❌ Impossible de parser le fichier")

                    except Exception as e:
                        st.error(f"❌ Erreur lors du chargement du profil : {str(e)}")

                else:
                    st.warning(f"""
                    ⚠️ **Fichier original introuvable**

                    Chemin attendu : `{plongee_complete['fichier_original_path']}`

                    Le fichier a peut-être été déplacé ou supprimé.
                    """)

            # === TAB ÉDITION ===
            with tab_edit:
                st.markdown("#### ✏️ Modifier les Annotations")

                with st.form("edit_dive_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        site_nom = st.text_input(
                            "📍 Site de plongée",
                            value=plongee_complete['site_nom']
                        )

                        buddy_nom = st.text_input(
                            "👥 Buddy/Palanquée",
                            value=plongee_complete['buddy_nom'] if plongee_complete['buddy_nom'] else ""
                        )

                        dive_type_idx = ["exploration", "formation", "technique"].index(plongee_complete['dive_type']) if plongee_complete['dive_type'] in ["exploration", "formation", "technique"] else 0
                        dive_type = st.selectbox(
                            "🤿 Type de plongée",
                            options=["exploration", "formation", "technique"],
                            index=dive_type_idx
                        )

                    with col2:
                        houle_options = ["aucune", "faible", "moyenne", "forte"]
                        houle_idx = houle_options.index(plongee_complete['houle']) if plongee_complete['houle'] in houle_options else 1
                        houle = st.selectbox(
                            "🌊 Houle",
                            options=houle_options,
                            index=houle_idx
                        )

                        visibilite = st.number_input(
                            "👁️ Visibilité (mètres)",
                            min_value=0,
                            max_value=50,
                            value=int(plongee_complete['visibilite_metres']) if plongee_complete['visibilite_metres'] else 10,
                            step=1
                        )

                        courant_options = ["aucun", "faible", "moyen", "fort"]
                        courant_idx = courant_options.index(plongee_complete['courant']) if plongee_complete['courant'] in courant_options else 0
                        courant = st.selectbox(
                            "💨 Courant",
                            options=courant_options,
                            index=courant_idx
                        )

                    rating = st.slider(
                        "⭐ Évaluation",
                        min_value=1,
                        max_value=5,
                        value=int(plongee_complete['rating']) if plongee_complete['rating'] else 3
                    )

                    # Tags : combiner tags standards + tags existants en DB
                    existing_tags = database.get_all_tags()
                    all_tags = sorted(set(config.STANDARD_TAGS + existing_tags))

                    tags = st.multiselect(
                        "🏷️ Tags",
                        options=all_tags,
                        default=plongee_complete['tags'] if plongee_complete['tags'] else []
                    )

                    notes = st.text_area(
                        "📝 Notes personnelles",
                        value=plongee_complete['notes'] if plongee_complete['notes'] else "",
                        height=150
                    )

                    col_save, col_delete = st.columns([3, 1])

                    with col_save:
                        submitted = st.form_submit_button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True,
                            type="primary"
                        )

                    with col_delete:
                        delete_btn = st.form_submit_button(
                            "🗑️ Supprimer",
                            use_container_width=True,
                            type="secondary"
                        )

                    if submitted:
                        # Mettre à jour
                        update_data = {
                            'site_nom': site_nom,
                            'buddy_nom': buddy_nom if buddy_nom else None,
                            'dive_type': dive_type,
                            'rating': rating,
                            'notes': notes,
                            'houle': houle,
                            'visibilite_metres': visibilite,
                            'courant': courant,
                            'tags': tags
                        }

                        if database.update_dive(plongee_selectionnee, update_data):
                            st.success("✅ Plongée mise à jour avec succès !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la mise à jour")

                    if delete_btn:
                        # Supprimer
                        if database.delete_dive(plongee_selectionnee):
                            # Supprimer aussi le fichier physique
                            try:
                                file_path = Path(plongee_complete['fichier_original_path'])
                                if file_path.exists():
                                    file_path.unlink()
                            except:
                                pass

                            st.success("✅ Plongée supprimée")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")

        else:
            st.error("❌ Impossible de charger les détails de la plongée")

st.divider()

# Bouton retour
if st.button("📤 Analyser une nouvelle plongée", type="primary", use_container_width=True):
    st.switch_page("pages/1_📤_Analyse.py")
