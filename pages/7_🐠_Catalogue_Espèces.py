"""
Page Catalogue d'Espèces - Gestion complète de la base de données des espèces marines
"""

import streamlit as st
import species_recognition
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Catalogue d'Espèces",
    page_icon="🐠",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("🐠 Catalogue des Espèces Marines")

# Statistiques globales
stats = species_recognition.get_species_stats()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Espèces cataloguées", stats['total_species'])
with col2:
    st.metric("👁️ Observations totales", stats['total_observations'])
with col3:
    ai_count = stats.get('detection_stats', {}).get('ai', 0)
    st.metric("🤖 Détectées par IA", ai_count)
with col4:
    manual_count = stats.get('detection_stats', {}).get('manual', 0)
    st.metric("✍️ Ajoutées manuellement", manual_count)

st.divider()

# Onglets principaux
tab_list, tab_add, tab_stats = st.tabs(["📋 Liste des espèces", "➕ Ajouter une espèce", "📊 Statistiques"])

# ===== ONGLET LISTE =====
with tab_list:
    st.markdown("### 📋 Toutes les espèces")

    # Filtres
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        search_query = st.text_input(
            "🔍 Rechercher",
            placeholder="Nom scientifique ou commun...",
            key="search_species"
        )

    with col2:
        filter_category = st.selectbox(
            "Catégorie",
            ["Toutes"] + ['poisson', 'corail', 'mollusque', 'crustacé',
                          'échinoderme', 'mammifère', 'reptile', 'autre'],
            key="filter_category"
        )

    with col3:
        items_per_page = st.number_input(
            "Par page",
            min_value=10,
            max_value=100,
            value=20,
            step=10,
            key="items_per_page"
        )

    # Récupérer les espèces
    if search_query and len(search_query) >= 2:
        # Mode recherche
        category_filter = None if filter_category == "Toutes" else filter_category
        all_species = species_recognition.search_species(search_query, category=category_filter, limit=100)
    else:
        # Mode liste complète
        category_filter = None if filter_category == "Toutes" else filter_category
        all_species = species_recognition.get_all_species(limit=1000, category=category_filter)

    if not all_species:
        st.info("📭 Aucune espèce trouvée.")
    else:
        # Pagination
        total_items = len(all_species)
        total_pages = (total_items - 1) // items_per_page + 1

        if 'species_page' not in st.session_state:
            st.session_state.species_page = 1

        st.caption(f"**{total_items} espèce(s) trouvée(s)**")

        # Afficher les espèces de la page actuelle
        start_idx = (st.session_state.species_page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_species = all_species[start_idx:end_idx]

        # Affichage en tableau avec actions
        for species in page_species:
            with st.expander(f"🐠 **{species['common_name_fr'] or species['scientific_name']}** ({species['scientific_name']})"):

                # Informations de l'espèce
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Nom scientifique:** {species['scientific_name']}")
                    st.markdown(f"**Nom français:** {species['common_name_fr'] or 'Non renseigné'}")
                    st.markdown(f"**Nom anglais:** {species['common_name_en'] or 'Non renseigné'}")
                    st.markdown(f"**Catégorie:** {species['category']}")

                with col2:
                    st.markdown(f"**Statut conservation:** {species['conservation_status'] or 'Non renseigné'}")
                    st.markdown(f"**Habitat:** {species['habitat'] or 'Non renseigné'}")
                    st.markdown(f"**Profondeur:** {species['depth_range'] or 'Non renseigné'}")

                if species['description']:
                    st.markdown(f"**Description:**\n{species['description']}")

                st.markdown("---")

                # Boutons d'action
                action_col1, action_col2, action_col3 = st.columns(3)

                with action_col1:
                    if st.button("✏️ Modifier", key=f"edit_{species['id']}", use_container_width=True):
                        st.session_state['editing_species_id'] = species['id']
                        st.rerun()

                with action_col2:
                    # Compter les observations
                    obs_count = sum(1 for sp in stats.get('top_species', [])
                                  if sp['scientific_name'] == species['scientific_name'])
                    st.button(f"👁️ {obs_count} observation(s)",
                            key=f"obs_{species['id']}",
                            disabled=True,
                            use_container_width=True)

                with action_col3:
                    if st.button("🗑️ Supprimer", key=f"del_{species['id']}", type="secondary", use_container_width=True):
                        st.session_state[f'confirm_delete_{species["id"]}'] = True

                # Confirmation de suppression
                if st.session_state.get(f'confirm_delete_{species["id"]}', False):
                    st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer **{species['scientific_name']}** ? "
                             "Toutes les observations associées seront également supprimées.")

                    conf_col1, conf_col2 = st.columns(2)
                    with conf_col1:
                        if st.button("✅ Confirmer la suppression",
                                   key=f"confirm_del_{species['id']}",
                                   type="primary",
                                   use_container_width=True):
                            if species_recognition.delete_species(species['id']):
                                st.success(f"✅ {species['scientific_name']} supprimé !")
                                st.session_state[f'confirm_delete_{species["id"]}'] = False
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la suppression")
                    with conf_col2:
                        if st.button("❌ Annuler",
                                   key=f"cancel_del_{species['id']}",
                                   use_container_width=True):
                            st.session_state[f'confirm_delete_{species["id"]}'] = False
                            st.rerun()

        # Formulaire d'édition (modal)
        if 'editing_species_id' in st.session_state:
            species_id = st.session_state['editing_species_id']
            species_data = species_recognition.get_species_by_id(species_id)

            if species_data:
                st.markdown("---")
                st.markdown(f"### ✏️ Modifier : {species_data['scientific_name']}")

                with st.form(key=f"edit_form_{species_id}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        edit_sci = st.text_input("Nom scientifique *", value=species_data['scientific_name'])
                        edit_fr = st.text_input("Nom français", value=species_data['common_name_fr'] or '')
                        edit_en = st.text_input("Nom anglais", value=species_data['common_name_en'] or '')
                        edit_cat = st.selectbox(
                            "Catégorie *",
                            ['poisson', 'corail', 'mollusque', 'crustacé',
                             'échinoderme', 'mammifère', 'reptile', 'autre'],
                            index=['poisson', 'corail', 'mollusque', 'crustacé',
                                   'échinoderme', 'mammifère', 'reptile', 'autre'].index(species_data['category'])
                        )

                    with col2:
                        edit_cons = st.text_input("Statut conservation",
                                                 value=species_data['conservation_status'] or '',
                                                 placeholder="LC, NT, VU, EN, CR")
                        edit_hab = st.text_input("Habitat", value=species_data['habitat'] or '')
                        edit_depth = st.text_input("Profondeur", value=species_data['depth_range'] or '')
                        edit_url = st.text_input("URL image", value=species_data['image_url'] or '')

                    edit_desc = st.text_area("Description", value=species_data['description'] or '', height=100)

                    submit_col1, submit_col2 = st.columns(2)
                    with submit_col1:
                        submit_edit = st.form_submit_button("💾 Sauvegarder", type="primary", use_container_width=True)
                    with submit_col2:
                        cancel_edit = st.form_submit_button("❌ Annuler", use_container_width=True)

                    if submit_edit:
                        if species_recognition.update_species(
                            species_id=species_id,
                            scientific_name=edit_sci,
                            common_name_fr=edit_fr,
                            common_name_en=edit_en,
                            category=edit_cat,
                            description=edit_desc,
                            conservation_status=edit_cons,
                            habitat=edit_hab,
                            depth_range=edit_depth,
                            image_url=edit_url
                        ):
                            st.success("✅ Espèce mise à jour !")
                            del st.session_state['editing_species_id']
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la mise à jour")

                    if cancel_edit:
                        del st.session_state['editing_species_id']
                        st.rerun()

        # Pagination
        st.divider()
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("⬅️ Précédent", disabled=st.session_state.species_page == 1):
                st.session_state.species_page -= 1
                st.rerun()
        with pcol2:
            st.markdown(f"<center>Page {st.session_state.species_page} / {total_pages}</center>",
                       unsafe_allow_html=True)
        with pcol3:
            if st.button("Suivant ➡️", disabled=st.session_state.species_page == total_pages):
                st.session_state.species_page += 1
                st.rerun()


# ===== ONGLET AJOUT =====
with tab_add:
    st.markdown("### ➕ Ajouter une nouvelle espèce")

    with st.form("add_new_species_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_sci = st.text_input("Nom scientifique *", key="add_sci")
            new_fr = st.text_input("Nom français", key="add_fr")
            new_en = st.text_input("Nom anglais", key="add_en")
            new_cat = st.selectbox(
                "Catégorie *",
                ['poisson', 'corail', 'mollusque', 'crustacé',
                 'échinoderme', 'mammifère', 'reptile', 'autre'],
                key="add_cat"
            )

        with col2:
            new_cons = st.text_input("Statut conservation",
                                    placeholder="ex: LC, NT, VU, EN, CR",
                                    key="add_cons")
            new_hab = st.text_input("Habitat", key="add_hab")
            new_depth = st.text_input("Plage de profondeur",
                                     placeholder="ex: 0-30m",
                                     key="add_depth")
            new_url = st.text_input("URL image (optionnel)", key="add_url")

        new_desc = st.text_area("Description", key="add_desc", height=100)

        submitted = st.form_submit_button("➕ Ajouter l'espèce", type="primary", use_container_width=True)

        if submitted:
            if not new_sci:
                st.error("❌ Le nom scientifique est obligatoire")
            else:
                species_id = species_recognition.add_species(
                    scientific_name=new_sci,
                    common_name_fr=new_fr,
                    common_name_en=new_en,
                    category=new_cat,
                    description=new_desc,
                    conservation_status=new_cons,
                    habitat=new_hab,
                    depth_range=new_depth,
                    image_url=new_url
                )

                if species_id:
                    st.success(f"✅ Espèce **{new_sci}** ajoutée avec succès ! (ID: {species_id})")
                    logger.info(f"Nouvelle espèce ajoutée : {new_sci} (ID={species_id})")
                else:
                    st.error("❌ Erreur : cette espèce existe peut-être déjà dans le catalogue")


# ===== ONGLET STATISTIQUES =====
with tab_stats:
    st.markdown("### 📊 Statistiques du catalogue")

    # Statistiques par catégorie
    if stats['category_stats']:
        st.markdown("#### 📂 Répartition par catégorie")

        import pandas as pd
        df_categories = pd.DataFrame([
            {'Catégorie': cat.capitalize(), 'Nombre': count}
            for cat, count in stats['category_stats'].items()
        ])

        col1, col2 = st.columns([2, 1])
        with col1:
            st.bar_chart(df_categories.set_index('Catégorie'))
        with col2:
            st.dataframe(df_categories, use_container_width=True, hide_index=True)

    st.divider()

    # Top espèces observées
    if stats['top_species']:
        st.markdown("#### 🏆 Espèces les plus observées")

        for idx, species in enumerate(stats['top_species'][:10], 1):
            if species['observation_count'] > 0:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"{idx}. **{species['common_name_fr'] or species['scientific_name']}** "
                            f"({species['scientific_name']})")
                with col2:
                    st.metric("Observations", species['observation_count'])

    st.divider()

    # Statistiques de détection
    st.markdown("#### 🔍 Méthodes de détection")

    detection_data = []
    for method, count in stats.get('detection_stats', {}).items():
        icon = {'ai': '🤖 IA', 'manual': '✍️ Manuel', 'verified': '✅ Vérifié'}.get(method, '❓ Autre')
        detection_data.append({'Méthode': icon, 'Observations': count})

    if detection_data:
        df_detection = pd.DataFrame(detection_data)
        st.dataframe(df_detection, use_container_width=True, hide_index=True)
