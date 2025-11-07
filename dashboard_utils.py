"""
Module de fonctions utilitaires pour le dashboard avec mise en cache.

Ce module fournit des fonctions optimisées pour calculer et afficher
les statistiques du dashboard, avec caching Streamlit pour améliorer les performances.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import database
from logger import get_logger

logger = get_logger(__name__)


@st.cache_data(ttl=60)
def get_dashboard_stats() -> Dict[str, Any]:
    """
    Calcule toutes les statistiques principales du dashboard.

    Cette fonction est cachée pendant 60 secondes pour améliorer les performances.
    Elle agrège les données de la base et calcule les métriques principales.

    Returns:
        Dictionnaire contenant toutes les statistiques:
        - total_dives: Nombre total de plongées
        - total_hours: Nombre d'heures total sous l'eau
        - max_depth: Profondeur maximale atteinte
        - avg_depth: Profondeur moyenne
        - total_sites: Nombre de sites visités
        - countries_count: Nombre de pays visités
        - avg_sac: SAC moyen
        - avg_temp: Température moyenne
        - recent_dives: 5 dernières plongées
        - this_month: Nombre de plongées ce mois
        - this_year: Nombre de plongées cette année
    """
    try:
        # Récupérer toutes les plongées
        df = database.get_all_dives()

        if df.empty:
            return {
                'total_dives': 0,
                'total_hours': 0,
                'max_depth': 0,
                'avg_depth': 0,
                'total_sites': 0,
                'countries_count': 0,
                'avg_sac': 0,
                'avg_temp': 0,
                'recent_dives': [],
                'this_month': 0,
                'this_year': 0
            }

        # Statistiques de base
        total_dives = len(df)
        total_hours = df['duree_minutes'].sum() / 60.0 if 'duree_minutes' in df.columns else 0
        max_depth = df['profondeur_max'].max() if 'profondeur_max' in df.columns else 0
        avg_depth = df['profondeur_max'].mean() if 'profondeur_max' in df.columns else 0
        avg_sac = df['sac'].mean() if 'sac' in df.columns else 0
        avg_temp = df['temperature_min'].mean() if 'temperature_min' in df.columns else 0

        # Sites uniques
        total_sites = df['site'].nunique() if 'site' in df.columns else 0

        # Nombre de pays (récupérer depuis les sites)
        sites = database.get_all_sites_with_stats()
        countries_count = len(set(site['pays'] for site in sites if site.get('pays')))

        # Plongées récentes (5 dernières)
        recent_dives = df.head(5).to_dict('records') if not df.empty else []

        # Statistiques temporelles
        now = datetime.now()
        df['date'] = pd.to_datetime(df['date'])

        # Ce mois
        first_day_month = datetime(now.year, now.month, 1)
        this_month = len(df[df['date'] >= first_day_month])

        # Cette année
        first_day_year = datetime(now.year, 1, 1)
        this_year = len(df[df['date'] >= first_day_year])

        return {
            'total_dives': total_dives,
            'total_hours': round(total_hours, 1),
            'max_depth': round(max_depth, 1) if max_depth else 0,
            'avg_depth': round(avg_depth, 1) if avg_depth else 0,
            'total_sites': total_sites,
            'countries_count': countries_count,
            'avg_sac': round(avg_sac, 1) if avg_sac else 0,
            'avg_temp': round(avg_temp, 1) if avg_temp else 0,
            'recent_dives': recent_dives,
            'this_month': this_month,
            'this_year': this_year
        }

    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques du dashboard : {e}", exc_info=True)
        # Retourner des valeurs par défaut en cas d'erreur
        return {
            'total_dives': 0,
            'total_hours': 0,
            'max_depth': 0,
            'avg_depth': 0,
            'total_sites': 0,
            'countries_count': 0,
            'avg_sac': 0,
            'avg_temp': 0,
            'recent_dives': [],
            'this_month': 0,
            'this_year': 0
        }


@st.cache_data(ttl=60)
def create_evolution_chart(period: str = "year") -> Optional[go.Figure]:
    """
    Crée un graphique d'évolution du nombre de plongées.

    Args:
        period: Période à afficher ("month", "year", "all")

    Returns:
        Figure Plotly ou None si pas de données
    """
    try:
        df = database.get_all_dives()

        if df.empty:
            return None

        # Convertir la colonne date en datetime
        df['date'] = pd.to_datetime(df['date'])

        # Filtrer selon la période
        now = datetime.now()
        if period == "month":
            first_day = datetime(now.year, now.month, 1)
            df = df[df['date'] >= first_day]
            freq = 'D'  # Par jour
            title = "Évolution ce mois"
        elif period == "year":
            first_day = datetime(now.year, 1, 1)
            df = df[df['date'] >= first_day]
            freq = 'W'  # Par semaine
            title = "Évolution cette année"
        else:  # all
            freq = 'M'  # Par mois
            title = "Évolution totale"

        if df.empty:
            return None

        # Grouper par période et compter
        df_grouped = df.groupby(pd.Grouper(key='date', freq=freq)).size().reset_index(name='count')

        # Créer le graphique
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df_grouped['date'],
            y=df_grouped['count'],
            mode='lines+markers',
            name='Plongées',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8, color='#60a5fa'),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)'
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Nombre de plongées",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0f2fe'),
            hovermode='x unified',
            showlegend=False
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(59, 130, 246, 0.1)',
            zeroline=False
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgba(59, 130, 246, 0.1)',
            zeroline=False
        )

        return fig

    except Exception as e:
        logger.error(f"Erreur lors de la création du graphique d'évolution : {e}", exc_info=True)
        return None


@st.cache_data(ttl=60)
def create_depth_distribution_chart() -> Optional[go.Figure]:
    """
    Crée un graphique de distribution des profondeurs.

    Returns:
        Figure Plotly ou None si pas de données
    """
    try:
        df = database.get_all_dives()

        if df.empty or 'profondeur_max' not in df.columns:
            return None

        # Supprimer les valeurs nulles
        depths = df['profondeur_max'].dropna()

        if depths.empty:
            return None

        # Créer un histogramme
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=depths,
            nbinsx=20,
            marker=dict(
                color='#3b82f6',
                line=dict(color='#60a5fa', width=1)
            ),
            name='Plongées'
        ))

        fig.update_layout(
            title="Distribution des Profondeurs",
            xaxis_title="Profondeur (m)",
            yaxis_title="Nombre de plongées",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0f2fe'),
            showlegend=False
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(59, 130, 246, 0.1)',
            zeroline=False
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgba(59, 130, 246, 0.1)',
            zeroline=False
        )

        return fig

    except Exception as e:
        logger.error(f"Erreur lors de la création du graphique de distribution : {e}", exc_info=True)
        return None


@st.cache_data(ttl=60)
def create_top_sites_chart(limit: int = 5) -> Optional[go.Figure]:
    """
    Crée un graphique des sites les plus visités.

    Args:
        limit: Nombre de sites à afficher (par défaut 5)

    Returns:
        Figure Plotly ou None si pas de données
    """
    try:
        sites = database.get_all_sites_with_stats()

        if not sites:
            return None

        # Filtrer les sites avec au moins une plongée et trier
        sites_with_dives = [s for s in sites if s['nombre_plongees'] > 0]
        sites_sorted = sorted(sites_with_dives, key=lambda x: x['nombre_plongees'], reverse=True)[:limit]

        if not sites_sorted:
            return None

        # Extraire les données
        names = [s['nom'] for s in sites_sorted]
        counts = [s['nombre_plongees'] for s in sites_sorted]

        # Créer le graphique
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=counts,
            y=names,
            orientation='h',
            marker=dict(
                color='#3b82f6',
                line=dict(color='#60a5fa', width=1)
            ),
            text=counts,
            textposition='outside'
        ))

        fig.update_layout(
            title=f"Top {limit} des Sites",
            xaxis_title="Nombre de plongées",
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#e0f2fe'),
            showlegend=False,
            margin=dict(l=150)
        )

        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(59, 130, 246, 0.1)',
            zeroline=False
        )

        fig.update_yaxes(
            showgrid=False
        )

        return fig

    except Exception as e:
        logger.error(f"Erreur lors de la création du graphique des top sites : {e}", exc_info=True)
        return None


@st.cache_data(ttl=60)
def calculate_achievements(stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calcule les achievements débloqués et leur progression.

    Args:
        stats: Dictionnaire de statistiques (de get_dashboard_stats())

    Returns:
        Liste d'achievements avec leur statut (unlocked, progress, target)
    """
    total_dives = stats.get('total_dives', 0)
    total_hours = stats.get('total_hours', 0)
    max_depth = stats.get('max_depth', 0)
    total_sites = stats.get('total_sites', 0)

    achievements = [
        {
            'icon': '🤿',
            'title': 'Premier Pas',
            'description': 'Effectuer votre première plongée',
            'unlocked': total_dives >= 1,
            'progress': min(total_dives, 1),
            'target': 1
        },
        {
            'icon': '🏊',
            'title': 'Explorateur',
            'description': 'Effectuer 10 plongées',
            'unlocked': total_dives >= 10,
            'progress': min(total_dives, 10),
            'target': 10
        },
        {
            'icon': '🐠',
            'title': 'Plongeur Confirmé',
            'description': 'Effectuer 50 plongées',
            'unlocked': total_dives >= 50,
            'progress': min(total_dives, 50),
            'target': 50
        },
        {
            'icon': '🦈',
            'title': 'Professionnel',
            'description': 'Effectuer 100 plongées',
            'unlocked': total_dives >= 100,
            'progress': min(total_dives, 100),
            'target': 100
        },
        {
            'icon': '⬇️',
            'title': 'Abysses',
            'description': 'Descendre à 40 mètres',
            'unlocked': max_depth >= 40,
            'progress': min(max_depth, 40),
            'target': 40
        },
        {
            'icon': '⏱️',
            'title': 'Marathon',
            'description': 'Cumuler 50 heures sous l\'eau',
            'unlocked': total_hours >= 50,
            'progress': min(total_hours, 50),
            'target': 50
        },
        {
            'icon': '🗺️',
            'title': 'Globe-Trotter',
            'description': 'Visiter 10 sites différents',
            'unlocked': total_sites >= 10,
            'progress': min(total_sites, 10),
            'target': 10
        },
        {
            'icon': '🌍',
            'title': 'Voyageur',
            'description': 'Plonger dans 5 pays différents',
            'unlocked': stats.get('countries_count', 0) >= 5,
            'progress': min(stats.get('countries_count', 0), 5),
            'target': 5
        }
    ]

    return achievements


@st.cache_data(ttl=60)
def get_recent_activity(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Récupère l'activité récente (dernières plongées).

    Args:
        limit: Nombre de plongées à retourner (par défaut 10)

    Returns:
        Liste des plongées récentes avec leurs détails
    """
    try:
        df = database.get_all_dives()

        if df.empty:
            return []

        # Prendre les N dernières plongées
        recent = df.head(limit).to_dict('records')

        # Formater les dates
        for dive in recent:
            if 'date' in dive:
                try:
                    date_obj = pd.to_datetime(dive['date'])
                    dive['date_formatted'] = date_obj.strftime('%d/%m/%Y')
                    dive['time_formatted'] = date_obj.strftime('%H:%M')
                except:
                    dive['date_formatted'] = dive['date']
                    dive['time_formatted'] = ''

        return recent

    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'activité récente : {e}", exc_info=True)
        return []


@st.cache_data(ttl=60)
def get_stats_comparison() -> Dict[str, Dict[str, float]]:
    """
    Calcule les comparaisons de statistiques (mois actuel vs mois précédent).

    Returns:
        Dictionnaire avec les comparaisons:
        - dives: {current, previous, delta, delta_pct}
        - avg_depth: {current, previous, delta, delta_pct}
        - avg_duration: {current, previous, delta, delta_pct}
    """
    try:
        df = database.get_all_dives()

        if df.empty:
            return {}

        # Convertir la colonne date
        df['date'] = pd.to_datetime(df['date'])
        now = datetime.now()

        # Mois actuel
        first_day_current = datetime(now.year, now.month, 1)
        if now.month == 1:
            first_day_previous = datetime(now.year - 1, 12, 1)
            last_day_previous = datetime(now.year, 1, 1) - timedelta(days=1)
        else:
            first_day_previous = datetime(now.year, now.month - 1, 1)
            last_day_previous = first_day_current - timedelta(days=1)

        # Filtrer les données
        df_current = df[df['date'] >= first_day_current]
        df_previous = df[(df['date'] >= first_day_previous) & (df['date'] <= last_day_previous)]

        def calc_comparison(current_val, previous_val):
            delta = current_val - previous_val
            delta_pct = (delta / previous_val * 100) if previous_val != 0 else 0
            return {
                'current': round(current_val, 1),
                'previous': round(previous_val, 1),
                'delta': round(delta, 1),
                'delta_pct': round(delta_pct, 1)
            }

        # Nombre de plongées
        dives_current = len(df_current)
        dives_previous = len(df_previous)

        # Profondeur moyenne
        depth_current = df_current['profondeur_max'].mean() if not df_current.empty else 0
        depth_previous = df_previous['profondeur_max'].mean() if not df_previous.empty else 0

        # Durée moyenne
        duration_current = df_current['duree_minutes'].mean() if not df_current.empty else 0
        duration_previous = df_previous['duree_minutes'].mean() if not df_previous.empty else 0

        return {
            'dives': calc_comparison(dives_current, dives_previous),
            'avg_depth': calc_comparison(depth_current, depth_previous),
            'avg_duration': calc_comparison(duration_current, duration_previous)
        }

    except Exception as e:
        logger.error(f"Erreur lors du calcul des comparaisons : {e}", exc_info=True)
        return {}
