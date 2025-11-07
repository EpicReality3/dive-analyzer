"""
DIVE ANALYZER - Dashboard Principal
Application d'analyse et de suivi de plongées sous-marines avec interface moderne.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui_components import (
    load_custom_css,
    create_metric_card,
    create_achievement_badge,
    create_progress_bar,
    create_info_card
)
from dashboard_utils import (
    get_dashboard_stats,
    create_evolution_chart,
    create_depth_distribution_chart,
    create_top_sites_chart,
    calculate_achievements,
    get_recent_activity
)

# Configuration de la page
st.set_page_config(
    page_title="DIVE ANALYZER",
    page_icon="🤿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Charger le CSS personnalisé
load_custom_css()

# Titre principal avec animation
st.markdown("""
<div class="animate-fade-in">
    <h1 style="text-align: center; font-size: 3rem; margin-bottom: 0;">
        🤿 DIVE ANALYZER
    </h1>
    <p style="text-align: center; color: #94a3b8; font-size: 1.2rem; margin-top: 0;">
        Analyseur de Plongées Sous-Marines
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Récupérer les statistiques (avec cache)
stats = get_dashboard_stats()

# === TABS NAVIGATION ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "📈 Statistiques",
    "📅 Calendrier",
    "🏆 Achievements",
    "⚡ Actions Rapides"
])

# ============================================================
# TAB 1: DASHBOARD PRINCIPAL
# ============================================================
with tab1:
    if stats['total_dives'] == 0:
        # État vide - Première utilisation
        st.markdown("<br><br>", unsafe_allow_html=True)

        create_info_card(
            "Bienvenue sur Dive Analyzer!",
            """
            Vous n'avez pas encore de plongées enregistrées.<br><br>
            <b>Pour commencer :</b><br>
            1. Allez dans l'onglet <b>Actions Rapides</b><br>
            2. Cliquez sur <b>Analyser une Plongée</b><br>
            3. Uploadez votre fichier de plongée (.fit, .uddf, .xml, .dl7)<br>
            4. Explorez vos statistiques et achievements !
            """,
            "🤿",
            "info"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📤 Analyser ma première plongée", type="primary", use_container_width=True):
                st.switch_page("pages/1_📤_Analyse.py")

    else:
        # Dashboard avec données
        st.markdown("### 📊 Vue d'ensemble")
        st.markdown("<br>", unsafe_allow_html=True)

        # Métriques principales (4 colonnes)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            create_metric_card(
                "🤿",
                str(stats['total_dives']),
                "Plongées Totales",
                f"+{stats['this_month']}" if stats['this_month'] > 0 else None
            )

        with col2:
            create_metric_card(
                "⏱️",
                f"{stats['total_hours']}h",
                "Heures Sous l'Eau"
            )

        with col3:
            create_metric_card(
                "⬇️",
                f"{stats['max_depth']}m",
                "Profondeur Max"
            )

        with col4:
            create_metric_card(
                "📍",
                str(stats['total_sites']),
                "Sites Visités"
            )

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Graphiques (2 colonnes)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📈 Évolution de l'Activité")
            fig_evolution = create_evolution_chart(period="year")
            if fig_evolution:
                st.plotly_chart(fig_evolution, use_container_width=True)
            else:
                st.info("Pas assez de données pour afficher l'évolution")

        with col2:
            st.markdown("### 📊 Distribution des Profondeurs")
            fig_depth = create_depth_distribution_chart()
            if fig_depth:
                st.plotly_chart(fig_depth, use_container_width=True)
            else:
                st.info("Pas assez de données pour afficher la distribution")

        st.markdown("<br>", unsafe_allow_html=True)

        # Activité récente
        st.markdown("### 🕐 Activité Récente")
        recent = get_recent_activity(limit=5)

        if recent:
            for dive in recent:
                cols = st.columns([1, 3, 2, 2, 2])

                with cols[0]:
                    rating_stars = "⭐" * int(dive.get('rating', 0)) if dive.get('rating') else "—"
                    st.markdown(f"**{rating_stars}**")

                with cols[1]:
                    st.markdown(f"**{dive.get('site', 'Site inconnu')}**")

                with cols[2]:
                    st.markdown(f"📅 {dive.get('date_formatted', 'N/A')}")

                with cols[3]:
                    depth = dive.get('profondeur_max', 0)
                    st.markdown(f"⬇️ {depth:.1f}m" if depth else "—")

                with cols[4]:
                    duration = dive.get('duree_minutes', 0)
                    st.markdown(f"⏱️ {duration:.0f}min" if duration else "—")

                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
        else:
            st.info("Aucune activité récente")

# ============================================================
# TAB 2: STATISTIQUES DÉTAILLÉES
# ============================================================
with tab2:
    if stats['total_dives'] == 0:
        create_info_card(
            "Statistiques indisponibles",
            "Commencez par analyser une plongée pour voir vos statistiques détaillées.",
            "📊",
            "info"
        )
    else:
        st.markdown("### 📊 Statistiques Détaillées")
        st.markdown("<br>", unsafe_allow_html=True)

        # Métriques supplémentaires (4 colonnes)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            create_metric_card(
                "📊",
                f"{stats['avg_depth']}m",
                "Profondeur Moyenne"
            )

        with col2:
            create_metric_card(
                "🌡️",
                f"{stats['avg_temp']}°C",
                "Température Moyenne"
            )

        with col3:
            create_metric_card(
                "🫁",
                f"{stats['avg_sac']}L/min",
                "SAC Moyen"
            )

        with col4:
            create_metric_card(
                "🌍",
                str(stats['countries_count']),
                "Pays Visités"
            )

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Top sites
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 🏆 Top Sites de Plongée")
            fig_sites = create_top_sites_chart(limit=10)
            if fig_sites:
                st.plotly_chart(fig_sites, use_container_width=True)
            else:
                st.info("Pas de données disponibles")

        with col2:
            st.markdown("### 📈 Cette Année")
            st.markdown("<br>", unsafe_allow_html=True)

            create_metric_card(
                "🤿",
                str(stats['this_year']),
                "Plongées en 2025"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            create_metric_card(
                "📅",
                str(stats['this_month']),
                "Plongées ce Mois"
            )

# ============================================================
# TAB 3: CALENDRIER
# ============================================================
with tab3:
    st.markdown("### 📅 Calendrier des Plongées")
    st.markdown("<br>", unsafe_allow_html=True)

    create_info_card(
        "Fonctionnalité en développement",
        """
        Le calendrier interactif sera bientôt disponible !<br><br>
        <b>Fonctionnalités prévues :</b><br>
        • Vue calendrier avec les plongées<br>
        • Filtrage par mois/année<br>
        • Statistiques par période<br>
        • Export des données
        """,
        "🚧",
        "info"
    )

# ============================================================
# TAB 4: ACHIEVEMENTS
# ============================================================
with tab4:
    st.markdown("### 🏆 Achievements & Progression")
    st.markdown("<br>", unsafe_allow_html=True)

    # Calculer les achievements
    achievements = calculate_achievements(stats)

    # Compter les achievements débloqués
    unlocked_count = sum(1 for a in achievements if a['unlocked'])
    total_count = len(achievements)

    # Barre de progression globale
    st.markdown("#### 🎯 Progression Globale")
    create_progress_bar(
        "Achievements Débloqués",
        unlocked_count,
        total_count,
        "blue"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Afficher les achievements en grille
    st.markdown("#### 🏅 Badges")
    st.markdown("<br>", unsafe_allow_html=True)

    # Créer une grille 4 colonnes
    for i in range(0, len(achievements), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            if i + j < len(achievements):
                achievement = achievements[i + j]

                with col:
                    create_achievement_badge(
                        achievement['icon'],
                        achievement['title'],
                        achievement['description'],
                        achievement['unlocked'],
                        achievement['progress'],
                        achievement['target']
                    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Message de motivation
    if unlocked_count == total_count:
        create_info_card(
            "Félicitations!",
            "Vous avez débloqué tous les achievements disponibles ! Continuez à plonger pour débloquer de nouveaux badges à venir.",
            "🎉",
            "success"
        )
    elif unlocked_count > 0:
        next_achievement = next((a for a in achievements if not a['unlocked']), None)
        if next_achievement:
            progress_pct = (next_achievement['progress'] / next_achievement['target']) * 100
            create_info_card(
                "Prochain Objectif",
                f"<b>{next_achievement['title']}</b><br>{next_achievement['description']}<br><br>Progression: {progress_pct:.0f}%",
                "🎯",
                "info"
            )

# ============================================================
# TAB 5: ACTIONS RAPIDES
# ============================================================
with tab5:
    st.markdown("### ⚡ Actions Rapides")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-top: 0;">📤 Analyser une Plongée</h3>
            <p>Uploadez un fichier de plongée (.fit, .uddf, .xml, .dl7) pour :</p>
            <ul>
                <li>📊 Visualiser le profil de plongée</li>
                <li>🔬 Analyser la physique (SAC, saturation N₂)</li>
                <li>⚠️ Détecter les alertes de sécurité</li>
                <li>💾 Sauvegarder dans votre journal</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📤 Analyser une Plongée", use_container_width=True, type="primary"):
            st.switch_page("pages/1_📤_Analyse.py")

    with col2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-top: 0;">📖 Consulter le Journal</h3>
            <p>Accédez à votre journal de plongées pour :</p>
            <ul>
                <li>📋 Voir l'historique complet</li>
                <li>🔍 Filtrer par site, date, profondeur</li>
                <li>📊 Statistiques agrégées</li>
                <li>📄 Exporter en PDF</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📖 Consulter le Journal", use_container_width=True):
            st.switch_page("pages/2_📖_Journal.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Bouton Carte
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-top: 0;">🗺️ Carte des Sites</h3>
            <p>Visualisez tous vos sites de plongée sur une carte interactive mondiale.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🗺️ Voir la Carte", use_container_width=True):
            st.switch_page("pages/3_🗺️_Carte.py")

    with col2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-top: 0;">📊 Statistiques Avancées</h3>
            <p>Explorez vos statistiques détaillées et votre progression.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Ce bouton reste sur la même page mais change d'onglet
        st.info("💡 Utilisez l'onglet 'Statistiques' ci-dessus pour accéder aux stats avancées")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem;">
    🤿 DIVE ANALYZER | Analyseur de Plongées Sous-Marines<br>
    Made with ❤️ and Streamlit
</div>
""", unsafe_allow_html=True)
