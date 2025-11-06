import streamlit as st
import folium
from streamlit_folium import st_folium
import database
from logger import get_logger

logger = get_logger(__name__)

# Configuration page
st.set_page_config(
    page_title="Carte des Sites de Plongée",
    page_icon="🗺️",
    layout="wide"
)

# Bouton retour accueil dans sidebar
if st.sidebar.button("🏠 Accueil", use_container_width=True):
    st.switch_page("app.py")
st.sidebar.divider()

st.title("🗺️ Carte des Sites de Plongée")

# Récupérer tous les sites avec leurs statistiques
sites = database.get_all_sites_with_stats()

if not sites:
    st.info("""
    📭 **Aucun site de plongée enregistré**

    Commencez par analyser une plongée pour créer votre premier site !
    """)

    if st.button("📤 Analyser une plongée", type="primary"):
        st.switch_page("pages/1_📤_Analyse.py")
else:
    # Statistiques globales
    st.markdown("### 📊 Statistiques Globales")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📍 Sites", len(sites))

    with col2:
        total_plongees = sum(site['nombre_plongees'] for site in sites)
        st.metric("🤿 Plongées Totales", total_plongees)

    with col3:
        sites_avec_coords = sum(1 for site in sites if site['coordonnees_gps'])
        st.metric("🌐 Sites Géolocalisés", sites_avec_coords)

    with col4:
        pays_uniques = set(site['pays'] for site in sites if site['pays'])
        st.metric("🌍 Pays Visités", len(pays_uniques))

    st.divider()

    # === CARTE INTERACTIVE ===
    st.markdown("### 🗺️ Carte Interactive")

    # Calculer le centre de la carte
    sites_avec_coordonnees = [site for site in sites if site['coordonnees_gps']]

    if sites_avec_coordonnees:
        # Extraire toutes les coordonnées
        latitudes = []
        longitudes = []

        for site in sites_avec_coordonnees:
            coords = site['coordonnees_gps'].split(',')
            if len(coords) == 2:
                try:
                    lat = float(coords[0].strip())
                    lon = float(coords[1].strip())
                    latitudes.append(lat)
                    longitudes.append(lon)
                except ValueError:
                    logger.warning(f"Coordonnées invalides pour le site {site['nom']}: {site['coordonnees_gps']}")

        if latitudes and longitudes:
            # Calculer le centre et le zoom approprié
            center_lat = sum(latitudes) / len(latitudes)
            center_lon = sum(longitudes) / len(longitudes)

            # Créer la carte Folium
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=6,
                tiles='OpenStreetMap'
            )

            # Ajouter un marqueur pour chaque site
            for site in sites_avec_coordonnees:
                coords = site['coordonnees_gps'].split(',')
                if len(coords) == 2:
                    try:
                        lat = float(coords[0].strip())
                        lon = float(coords[1].strip())

                        # Créer le contenu du popup
                        popup_html = f"""
                        <div style="width: 300px; font-family: Arial, sans-serif;">
                            <h3 style="margin: 0 0 10px 0; color: #1f77b4;">{site['nom']}</h3>
                            {f"<p style='margin: 5px 0;'><b>📍 Pays:</b> {site['pays']}</p>" if site['pays'] else ""}
                            <hr style="margin: 10px 0;">
                            <p style="margin: 5px 0;"><b>🤿 Plongées:</b> {site['nombre_plongees']}</p>
                            {f"<p style='margin: 5px 0;'><b>⬇️ Prof. Max:</b> {site['profondeur_max']:.1f} m</p>" if site['profondeur_max'] else ""}
                            {f"<p style='margin: 5px 0;'><b>📊 Prof. Moyenne:</b> {site['profondeur_moyenne']:.1f} m</p>" if site['profondeur_moyenne'] else ""}
                            {f"<p style='margin: 5px 0;'><b>⏱️ Durée Moyenne:</b> {site['duree_moyenne']:.0f} min</p>" if site['duree_moyenne'] else ""}
                            {f"<p style='margin: 5px 0;'><b>🌡️ Temp. Moyenne:</b> {site['temperature_moyenne']:.1f} °C</p>" if site['temperature_moyenne'] else ""}
                            {f"<p style='margin: 5px 0;'><b>🫁 SAC Moyen:</b> {site['sac_moyen']:.1f} L/min</p>" if site['sac_moyen'] else ""}
                            {f"<p style='margin: 5px 0;'><b>⭐ Note Moyenne:</b> {site['note_moyenne']:.1f}/5</p>" if site['note_moyenne'] else ""}
                            <hr style="margin: 10px 0;">
                            <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
                                <b>Première plongée:</b> {site['premiere_plongee'][:10] if site['premiere_plongee'] else 'N/A'}<br>
                                <b>Dernière plongée:</b> {site['derniere_plongee'][:10] if site['derniere_plongee'] else 'N/A'}
                            </p>
                        </div>
                        """

                        # Déterminer la couleur du marqueur selon le nombre de plongées
                        if site['nombre_plongees'] >= 10:
                            icon_color = 'red'
                        elif site['nombre_plongees'] >= 5:
                            icon_color = 'orange'
                        else:
                            icon_color = 'blue'

                        # Ajouter le marqueur
                        folium.Marker(
                            location=[lat, lon],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{site['nom']} ({site['nombre_plongees']} plongées)",
                            icon=folium.Icon(color=icon_color, icon='info-sign')
                        ).add_to(m)

                    except ValueError:
                        continue

            # Afficher la carte
            st_folium(m, width=None, height=600, returned_objects=[])

            # Légende
            st.markdown("""
            **Légende des marqueurs:**
            - 🔵 Bleu: 1-4 plongées
            - 🟠 Orange: 5-9 plongées
            - 🔴 Rouge: 10+ plongées
            """)
        else:
            st.warning("⚠️ Aucune coordonnée GPS valide trouvée dans la base de données.")
    else:
        st.warning("""
        ⚠️ **Aucun site n'a de coordonnées GPS**

        Utilisez la section ci-dessous pour ajouter des coordonnées GPS à vos sites.
        """)

    st.divider()

    # === GESTION DES COORDONNÉES GPS ===
    st.markdown("### ✏️ Gérer les Coordonnées GPS")

    # Afficher un tableau avec tous les sites
    st.markdown("#### 📍 Liste des Sites")

    # Créer un tableau pour affichage
    import pandas as pd

    sites_df = pd.DataFrame([
        {
            'Site': site['nom'],
            'Pays': site['pays'] or 'Non renseigné',
            'Plongées': site['nombre_plongees'],
            'Coordonnées GPS': site['coordonnees_gps'] or '❌ Non renseignées',
        }
        for site in sites
    ])

    st.dataframe(
        sites_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # === ÉDITER LES COORDONNÉES ===
    st.markdown("#### ✏️ Modifier les Coordonnées GPS")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Sélectionner un site
        sites_noms = [site['nom'] for site in sites]
        site_selectionne = st.selectbox(
            "Sélectionner un site",
            options=sites_noms,
            key="site_select"
        )

        # Récupérer les infos du site sélectionné
        site_info = next(site for site in sites if site['nom'] == site_selectionne)

        # Champ pour les coordonnées
        coords_actuelles = site_info['coordonnees_gps'] or ""
        nouvelles_coords = st.text_input(
            "Coordonnées GPS (format: latitude,longitude)",
            value=coords_actuelles,
            placeholder="43.0242,5.5485",
            help="Format: latitude,longitude (ex: 43.0242,5.5485 pour Port-Cros, France)"
        )

        # Bouton pour mettre à jour
        if st.button("💾 Enregistrer les coordonnées", type="primary"):
            if nouvelles_coords:
                # Valider le format
                coords = nouvelles_coords.split(',')
                if len(coords) == 2:
                    try:
                        lat = float(coords[0].strip())
                        lon = float(coords[1].strip())

                        # Vérifier que les coordonnées sont dans les limites valides
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            # Mettre à jour dans la base de données
                            success = database.update_site_coordinates(site_info['id'], nouvelles_coords)

                            if success:
                                st.success(f"✅ Coordonnées GPS mises à jour pour **{site_selectionne}** !")
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la mise à jour des coordonnées.")
                        else:
                            st.error("❌ Coordonnées invalides. Latitude: [-90, 90], Longitude: [-180, 180]")
                    except ValueError:
                        st.error("❌ Format invalide. Utilisez le format: latitude,longitude (ex: 43.0242,5.5485)")
                else:
                    st.error("❌ Format invalide. Utilisez le format: latitude,longitude (ex: 43.0242,5.5485)")
            else:
                st.warning("⚠️ Veuillez entrer des coordonnées GPS.")

    with col2:
        st.markdown("""
        **💡 Comment trouver les coordonnées GPS ?**

        1. Ouvrez Google Maps
        2. Recherchez le site de plongée
        3. Clic droit sur le lieu → Coordonnées
        4. Copiez-collez les coordonnées

        **Exemples:**
        - Port-Cros, France: `43.0242,5.5485`
        - Bora Bora, Polynésie: `-16.5004,-151.7414`
        - Great Barrier Reef: `-18.2871,147.6992`
        """)
