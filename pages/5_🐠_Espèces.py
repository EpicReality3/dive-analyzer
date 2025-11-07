"""
Page Espèces Marines - Catalogue et observations d'espèces
"""

import streamlit as st
import database
import species_recognition
import pandas as pd
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Espèces Marines",
    page_icon="🐠",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("🐠 Espèces Marines")

# Onglets
tab_catalogue, tab_observations, tab_stats = st.tabs(
    ["📚 Catalogue", "👁️ Observations", "📊 Statistiques"]
)

# ===== ONGLET CATALOGUE =====
with tab_catalogue:
    st.markdown("### 📚 Catalogue des espèces")

    # Barre de recherche et filtres
    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "🔍 Rechercher une espèce",
            placeholder="Nom scientifique ou commun (ex: requin, Amphiprion, tortue...)",
            key="catalogue_search"
        )

    with col2:
        category_filter = st.selectbox(
            "Catégorie",
            ['Toutes', 'poisson', 'corail', 'mollusque', 'crustacé',
             'échinoderme', 'mammifère', 'reptile', 'autre'],
            key="catalogue_category"
        )

    # Recherche
    if search_query:
        cat = None if category_filter == 'Toutes' else category_filter
        results = species_recognition.search_species(search_query, category=cat, limit=50)

        if results:
            st.markdown(f"**{len(results)} espèce(s) trouvée(s)**")

            # Afficher les résultats en grille
            for species in results:
                with st.expander(
                    f"{'🐟' if species['category'] == 'poisson' else '🪸' if species['category'] == 'corail' else '🐚'} "
                    f"{species['common_name_fr'] or species['scientific_name']} "
                    f"({species['scientific_name']})"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.write(f"**Nom scientifique:** {species['scientific_name']}")
                        if species['common_name_fr']:
                            st.write(f"**Nom français:** {species['common_name_fr']}")
                        if species['common_name_en']:
                            st.write(f"**Nom anglais:** {species['common_name_en']}")

                        if species['description']:
                            st.write(f"**Description:** {species['description']}")

                    with col2:
                        st.write(f"**Catégorie:** {species['category']}")
                        if species['conservation_status']:
                            # Emoji selon le statut
                            status_emoji = {
                                'LC': '🟢',  # Préoccupation mineure
                                'NT': '🟡',  # Quasi menacé
                                'VU': '🟠',  # Vulnérable
                                'EN': '🔴',  # En danger
                                'CR': '🔴'   # En danger critique
                            }
                            emoji = status_emoji.get(species['conservation_status'], '⚪')
                            st.write(f"**Conservation:** {emoji} {species['conservation_status']}")

                        if species['habitat']:
                            st.write(f"**Habitat:** {species['habitat']}")
                        if species['depth_range']:
                            st.write(f"**Profondeur:** {species['depth_range']}")

        else:
            st.info("Aucune espèce trouvée avec ces critères")

    else:
        st.info("👆 Utilisez la barre de recherche ci-dessus pour trouver une espèce")

    st.divider()

    # Formulaire d'ajout
    with st.expander("➕ Ajouter une nouvelle espèce au catalogue"):
        with st.form("add_species_catalogue"):
            st.markdown("##### Informations principales")

            col1, col2 = st.columns(2)

            with col1:
                new_scientific = st.text_input(
                    "Nom scientifique *",
                    help="Nom scientifique en latin (ex: Amphiprion ocellaris)",
                    key="cat_new_sci"
                )
                new_common_fr = st.text_input(
                    "Nom commun français",
                    help="Nom usuel en français (ex: Poisson-clown)",
                    key="cat_new_fr"
                )
                new_common_en = st.text_input(
                    "Nom commun anglais",
                    help="Nom usuel en anglais (ex: Clownfish)",
                    key="cat_new_en"
                )

            with col2:
                new_category = st.selectbox(
                    "Catégorie *",
                    ['poisson', 'corail', 'mollusque', 'crustacé',
                     'échinoderme', 'mammifère', 'reptile', 'autre'],
                    key="cat_new_cat"
                )
                new_conservation = st.selectbox(
                    "Statut de conservation",
                    ['', 'LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX'],
                    format_func=lambda x: {
                        '': 'Non évalué',
                        'LC': 'LC - Préoccupation mineure',
                        'NT': 'NT - Quasi menacé',
                        'VU': 'VU - Vulnérable',
                        'EN': 'EN - En danger',
                        'CR': 'CR - En danger critique',
                        'EW': 'EW - Éteint à l\'état sauvage',
                        'EX': 'EX - Éteint'
                    }.get(x, x),
                    key="cat_new_cons"
                )
                new_depth = st.text_input(
                    "Plage de profondeur",
                    placeholder="ex: 0-30m",
                    key="cat_new_depth"
                )

            st.markdown("##### Informations complémentaires")

            new_description = st.text_area(
                "Description",
                help="Description générale de l'espèce",
                key="cat_new_desc"
            )
            new_habitat = st.text_input(
                "Habitat",
                placeholder="ex: Récifs coralliens, herbiers marins",
                key="cat_new_hab"
            )
            new_image_url = st.text_input(
                "URL image de référence (optionnel)",
                placeholder="https://...",
                key="cat_new_img"
            )

            submitted = st.form_submit_button("➕ Ajouter l'espèce", type="primary")

            if submitted:
                if not new_scientific:
                    st.error("❌ Le nom scientifique est obligatoire")
                else:
                    species_id = species_recognition.add_species(
                        scientific_name=new_scientific,
                        common_name_fr=new_common_fr,
                        common_name_en=new_common_en,
                        category=new_category,
                        description=new_description,
                        conservation_status=new_conservation,
                        habitat=new_habitat,
                        depth_range=new_depth,
                        image_url=new_image_url
                    )

                    if species_id:
                        st.success(f"✅ Espèce **{new_scientific}** ajoutée avec succès ! (ID: {species_id})")
                        st.balloons()
                    else:
                        st.error("❌ Erreur : cette espèce existe peut-être déjà dans le catalogue")


# ===== ONGLET OBSERVATIONS =====
with tab_observations:
    st.markdown("### 👁️ Observations par plongée")

    # Récupérer toutes les plongées
    df_dives = database.get_all_dives()

    if df_dives.empty:
        st.info("📭 Aucune plongée enregistrée")
    else:
        # Sélecteur de plongée
        dive_choices = {}
        for _, dive in df_dives.iterrows():
            label = f"{dive['date']} - {dive['site']} ({dive['profondeur_max']:.1f}m)"
            dive_choices[label] = dive['id']

        selected_dive_label = st.selectbox(
            "🤿 Sélectionner une plongée",
            options=list(dive_choices.keys()),
            key="obs_dive_select"
        )

        selected_dive_id = dive_choices[selected_dive_label]

        # Récupérer les espèces de cette plongée
        dive_species = species_recognition.get_dive_species(selected_dive_id)

        if dive_species:
            st.markdown(f"**{len(dive_species)} espèce(s) observée(s)**")

            # Afficher les espèces
            for obs in dive_species:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    # Emoji selon la catégorie
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
                    emoji = emoji_map.get(obs['category'], '🌊')

                    st.write(f"{emoji} **{obs['common_name_fr'] or obs['scientific_name']}** "
                            f"({obs['scientific_name']})")

                    if obs['notes']:
                        st.caption(f"💬 {obs['notes']}")

                with col2:
                    if obs['quantity'] > 1:
                        st.write(f"Quantité: {obs['quantity']}")

                    # Badge de détection
                    if obs['detected_by'] == 'ai':
                        st.caption("🤖 IA")
                    elif obs['detected_by'] == 'verified':
                        st.caption("✓ Vérifié")
                    else:
                        st.caption("👤 Manuel")

                with col3:
                    if obs['confidence_score']:
                        confidence_pct = obs['confidence_score'] * 100
                        st.write(f"Confiance: {confidence_pct:.0f}%")

                    # Statut de conservation
                    if obs['conservation_status']:
                        status_colors = {
                            'LC': '🟢',
                            'NT': '🟡',
                            'VU': '🟠',
                            'EN': '🔴',
                            'CR': '🔴'
                        }
                        color = status_colors.get(obs['conservation_status'], '⚪')
                        st.caption(f"{color} {obs['conservation_status']}")

            st.divider()

        else:
            st.info("Aucune espèce enregistrée pour cette plongée")

        # Formulaire d'ajout manuel
        with st.expander("➕ Ajouter une observation d'espèce"):
            st.markdown("Ajouter manuellement une espèce observée lors de cette plongée")

            # Recherche d'espèce
            species_search = st.text_input(
                "Rechercher une espèce",
                placeholder="Nom scientifique ou commun",
                key="obs_species_search"
            )

            if species_search:
                search_results = species_recognition.search_species(species_search, limit=10)

                if search_results:
                    species_options = {}
                    for sp in search_results:
                        label = f"{sp['common_name_fr'] or sp['scientific_name']} ({sp['scientific_name']})"
                        species_options[label] = sp['id']

                    selected_species_label = st.selectbox(
                        "Sélectionner l'espèce",
                        options=list(species_options.keys()),
                        key="obs_species_select"
                    )

                    selected_species_id = species_options[selected_species_label]

                    col1, col2 = st.columns(2)
                    with col1:
                        obs_quantity = st.number_input(
                            "Quantité observée",
                            min_value=1,
                            value=1,
                            key="obs_quantity"
                        )
                    with col2:
                        obs_notes = st.text_area(
                            "Notes (optionnel)",
                            key="obs_notes"
                        )

                    if st.button("➕ Ajouter l'observation", type="primary"):
                        result_id = species_recognition.add_species_to_dive(
                            dive_id=selected_dive_id,
                            species_id=selected_species_id,
                            quantity=obs_quantity,
                            notes=obs_notes,
                            detected_by='manual'
                        )

                        if result_id:
                            st.success("✅ Observation ajoutée avec succès !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur : cette espèce est peut-être déjà enregistrée pour cette plongée")
                else:
                    st.info("Aucune espèce trouvée. Ajoutez-la d'abord au catalogue.")


# ===== ONGLET STATISTIQUES =====
with tab_stats:
    st.markdown("### 📊 Statistiques des espèces")

    stats = species_recognition.get_species_stats()

    # Métriques générales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Espèces au catalogue", stats['total_species'])
    with col2:
        st.metric("👁️ Observations totales", stats['total_observations'])
    with col3:
        avg_per_dive = stats['total_observations'] / len(df_dives) if not df_dives.empty else 0
        st.metric("📊 Moyenne par plongée", f"{avg_per_dive:.1f}")

    st.divider()

    # Répartition par catégorie
    if stats['category_stats']:
        st.markdown("### 📊 Répartition par catégorie")

        category_df = pd.DataFrame(
            list(stats['category_stats'].items()),
            columns=['Catégorie', 'Nombre']
        ).sort_values('Nombre', ascending=False)

        # Graphique
        st.bar_chart(category_df.set_index('Catégorie'))

        # Tableau
        st.dataframe(
            category_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # Top espèces observées
    if stats['top_species']:
        st.markdown("### 🏆 Top 10 des espèces les plus observées")

        for idx, species in enumerate(stats['top_species'], 1):
            if species['observation_count'] > 0:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{idx}. {species['common_name_fr'] or species['scientific_name']}** "
                            f"({species['scientific_name']})")
                with col2:
                    st.write(f"**{species['observation_count']}** observation(s)")

    st.divider()

    # Statistiques par source de détection
    if stats['detection_stats']:
        st.markdown("### 🔍 Source des détections")

        detection_labels = {
            'ai': '🤖 Détection IA',
            'manual': '👤 Ajout manuel',
            'verified': '✓ Vérifié'
        }

        for source, count in stats['detection_stats'].items():
            label = detection_labels.get(source, source)
            st.write(f"{label}: **{count}** observation(s)")
