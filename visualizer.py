"""
Module de visualisation pour les données de plongée.

Ce module fournit des fonctions pour créer des graphiques interactifs
avec Plotly à partir des données de plongée parsées.
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np


def calculate_ascent_speed(df: pd.DataFrame) -> pd.Series:
    """
    Calcule la vitesse de remontée entre chaque point de mesure.

    Args:
        df: DataFrame avec colonnes temps_secondes et profondeur_metres

    Returns:
        Series contenant la vitesse de remontée en m/min pour chaque point
        (valeur positive = remontée, négative = descente)

    Note:
        Le premier point a une vitesse de 0 (pas de point précédent)
    """
    # Initialiser avec des zéros
    speeds = np.zeros(len(df))

    # Calculer les différences de profondeur et de temps
    # Note: En remontée, profondeur diminue, donc Δprofondeur est négatif
    # On inverse le signe pour avoir vitesse positive = remontée
    for i in range(1, len(df)):
        delta_depth = df['profondeur_metres'].iloc[i] - df['profondeur_metres'].iloc[i-1]
        delta_time = df['temps_secondes'].iloc[i] - df['temps_secondes'].iloc[i-1]

        if delta_time > 0:
            # Vitesse en m/s, puis convertir en m/min
            # Inverser le signe : remontée (prof diminue) = vitesse positive
            speed_ms = -delta_depth / delta_time
            speeds[i] = speed_ms * 60  # Convertir en m/min
        else:
            speeds[i] = 0

    # Clipper les valeurs aberrantes (max 30 m/min est déjà très rapide)
    speeds = np.clip(speeds, -30, 30)

    return pd.Series(speeds, index=df.index)


def detect_safety_stops(df: pd.DataFrame) -> list[dict]:
    """
    Détecte les paliers de sécurité dans le profil de plongée.

    Un palier est défini comme :
    - Variation de profondeur ± 1.5m pendant au moins 30 secondes
    - Vitesse proche de 0 (stabilisation)

    Args:
        df: DataFrame avec colonnes temps_secondes et profondeur_metres

    Returns:
        Liste de dictionnaires avec :
        - prof_moyenne: Profondeur moyenne du palier (m)
        - temps_debut: Temps de début du palier (s)
        - temps_fin: Temps de fin du palier (s)
        - duree: Durée du palier (s)
    """
    paliers = []

    # Paramètres de détection
    DEPTH_TOLERANCE = 1.5  # ± 1.5m
    MIN_DURATION = 30  # 30 secondes minimum

    i = 0
    while i < len(df) - 1:
        # Profondeur de référence
        ref_depth = df['profondeur_metres'].iloc[i]
        start_time = df['temps_secondes'].iloc[i]

        # Chercher combien de temps on reste à cette profondeur
        j = i + 1
        while j < len(df):
            current_depth = df['profondeur_metres'].iloc[j]
            if abs(current_depth - ref_depth) > DEPTH_TOLERANCE:
                break
            j += 1

        # Calculer la durée
        end_time = df['temps_secondes'].iloc[j-1]
        duration = end_time - start_time

        # Si c'est un palier valide (durée suffisante)
        if duration >= MIN_DURATION:
            # Calculer profondeur moyenne sur le segment
            avg_depth = df['profondeur_metres'].iloc[i:j].mean()

            paliers.append({
                'prof_moyenne': avg_depth,
                'temps_debut': start_time,
                'temps_fin': end_time,
                'duree': duration
            })

            i = j  # Avancer après le palier
        else:
            i += 1  # Avancer d'un point

    return paliers


def plot_depth_profile(df: pd.DataFrame) -> go.Figure:
    """
    Crée un graphique du profil de profondeur de la plongée avec analyse avancée.

    Args:
        df: DataFrame avec colonnes temps_secondes et profondeur_metres

    Returns:
        Figure Plotly interactive du profil de profondeur

    Le graphique affiche :
    - Axe X : Temps écoulé en minutes
    - Axe Y : Profondeur en mètres (inversé)
    - Code couleur selon vitesse de remontée (bleu/orange/rouge)
    - Annotation profondeur maximale
    - Annotations des paliers de sécurité détectés
    """
    # Convertir le temps de secondes en minutes
    temps_minutes = df['temps_secondes'] / 60

    # Calculer les vitesses de remontée
    speeds = calculate_ascent_speed(df)

    # Créer la figure
    fig = go.Figure()

    # Tracker pour savoir si on a déjà ajouté chaque couleur à la légende
    legend_added = {'blue': False, 'orange': False, 'red': False}

    # Créer des segments colorés selon la vitesse de remontée
    # Bleu: < 10 m/min, Orange: 10-15 m/min, Rouge: > 15 m/min
    i = 0
    while i < len(df):
        # Déterminer la couleur et le label du segment actuel
        speed = speeds.iloc[i]

        if speed < 10:
            color = '#1f77b4'  # Bleu
            color_key = 'blue'
            speed_label = '🔵 Vitesse OK (< 10 m/min)'
        elif speed < 15:
            color = '#ff7f0e'  # Orange
            color_key = 'orange'
            speed_label = '🟠 Vitesse élevée (10-15 m/min)'
        else:
            color = '#d62728'  # Rouge
            color_key = 'red'
            speed_label = '🔴 Vitesse excessive (> 15 m/min)'

        # Trouver la fin du segment de même couleur
        j = i + 1
        while j < len(df):
            next_speed = speeds.iloc[j]
            if (next_speed < 10 and speed >= 10) or \
               (next_speed >= 10 and next_speed < 15 and (speed < 10 or speed >= 15)) or \
               (next_speed >= 15 and speed < 15):
                break
            j += 1

        # Déterminer si on affiche cette entrée dans la légende
        show_legend = not legend_added[color_key]
        if show_legend:
            legend_added[color_key] = True

        # Créer la trace pour ce segment avec hover personnalisé pour chaque point
        segment_speeds = speeds.iloc[i:j+1]
        hover_texts = [f'Temps: {t:.1f} min | Prof: {p:.1f} m | Vitesse: {s:.1f} m/min'
                       for t, p, s in zip(temps_minutes.iloc[i:j+1],
                                          df['profondeur_metres'].iloc[i:j+1],
                                          segment_speeds)]

        trace = go.Scatter(
            x=temps_minutes.iloc[i:j+1],
            y=df['profondeur_metres'].iloc[i:j+1],
            mode='lines',
            name=speed_label,
            line=dict(color=color, width=2),
            showlegend=show_legend,
            hovertext=hover_texts,
            hovertemplate='%{hovertext}<extra></extra>'
        )
        fig.add_trace(trace)

        i = j

    # Trouver et annoter la profondeur maximale
    max_depth_idx = df['profondeur_metres'].idxmax()
    max_depth = df['profondeur_metres'].iloc[max_depth_idx]
    max_depth_time = temps_minutes.iloc[max_depth_idx]

    fig.add_annotation(
        x=max_depth_time,
        y=max_depth,
        text=f"⬇️ Prof. Max: {max_depth:.1f} m",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor='#d62728',
        ax=40,
        ay=-40,
        bgcolor='white',
        bordercolor='#d62728',
        borderwidth=2,
        font=dict(size=12, color='#d62728')
    )

    # Détecter et afficher les paliers de sécurité (rectangles transparents)
    paliers = detect_safety_stops(df)

    for palier in paliers:
        # Convertir les temps en minutes
        temps_debut_min = palier['temps_debut'] / 60
        temps_fin_min = palier['temps_fin'] / 60
        prof_moy = palier['prof_moyenne']

        # Calculer les limites du rectangle (±0.75m autour de la profondeur moyenne)
        prof_min = prof_moy - 0.75
        prof_max = prof_moy + 0.75

        # Ajouter un rectangle semi-transparent vert en arrière-plan
        fig.add_shape(
            type='rect',
            x0=temps_debut_min,
            y0=prof_min,
            x1=temps_fin_min,
            y1=prof_max,
            fillcolor='rgba(144, 238, 144, 0.2)',  # Vert pâle transparent
            line=dict(width=0),  # Pas de bordure
            layer='below'  # Derrière la courbe
        )

    # Configurer le layout
    fig.update_layout(
        title='🤿 Profil de Plongée',
        xaxis=dict(
            title='Temps (minutes)',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            title='Profondeur (mètres)',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False,
            autorange='reversed'  # Inverser l'axe Y
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=40, t=60, b=60),
        hovermode='closest',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    return fig
