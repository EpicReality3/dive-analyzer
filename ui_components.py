"""
Module de composants UI réutilisables pour l'application Dive Analyzer.

Ce module fournit des composants d'interface utilisateur stylisés et réutilisables
avec le style glassmorphism et les animations.
"""

import streamlit as st
import textwrap
from pathlib import Path


def load_custom_css():
    """
    Charge le fichier CSS personnalisé dans l'application Streamlit.

    Cette fonction doit être appelée au début de chaque page qui utilise
    les composants UI personnalisés.
    """
    css_file = Path(__file__).parent / ".streamlit" / "style.css"

    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
            st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Fichier CSS personnalisé introuvable")


def create_metric_card(icon: str, value: str, label: str, delta: str = None):
    """
    Crée une carte de métrique stylisée avec effet glassmorphism.

    Args:
        icon: Emoji ou icône à afficher
        value: Valeur principale de la métrique
        label: Label descriptif de la métrique
        delta: Variation optionnelle (ex: "+5%" ou "-2")

    Example:
        >>> create_metric_card("🤿", "42", "Plongées Totales", "+5")
    """
    delta_html = ""
    if delta:
        # Déterminer la couleur selon le signe
        if delta.startswith('+'):
            delta_color = "#10b981"  # Vert
            delta_icon = "↗"
        elif delta.startswith('-'):
            delta_color = "#ef4444"  # Rouge
            delta_icon = "↘"
        else:
            delta_color = "#6b7280"  # Gris
            delta_icon = ""

        delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 5px; font-weight: 600;">{delta_icon} {delta}</div>'

    html = f'''
    <div class="metric-card animate-fade-in">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


def create_achievement_badge(
    icon: str,
    title: str,
    description: str,
    unlocked: bool = False,
    progress: int = 0,
    target: int = 100
):
    """
    Crée un badge d'achievement avec effet hover et animation.

    Args:
        icon: Emoji représentant l'achievement
        title: Titre de l'achievement
        description: Description de l'achievement
        unlocked: True si l'achievement est débloqué
        progress: Progression actuelle (si non débloqué)
        target: Objectif à atteindre (si non débloqué)

    Example:
        >>> create_achievement_badge(
        ...     "🏆",
        ...     "Explorateur",
        ...     "Effectuer 10 plongées",
        ...     unlocked=True
        ... )
    """
    locked_class = "" if unlocked else "locked"

    # Progress bar HTML (seulement si non débloqué)
    progress_html = ""
    if not unlocked and target > 0:
        progress_pct = min(100, (progress / target) * 100)
        progress_html = f'<div style="margin-top: 10px;"><div class="progress-bar-container" style="height: 8px;"><div class="progress-bar-fill" style="width: {progress_pct}%;"></div></div><div style="font-size: 0.7rem; color: #94a3b8; margin-top: 3px; text-align: center;">{progress} / {target}</div></div>'

    html = f'''
    <div class="achievement-badge {locked_class} animate-fade-in">
        <div class="achievement-icon">{icon}</div>
        <div class="achievement-title">{title}</div>
        <div class="achievement-description">{description}</div>
        {progress_html}
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


def create_glass_card(content: str, hover_effect: bool = True):
    """
    Crée une carte avec effet glassmorphism pour encapsuler du contenu.

    Args:
        content: Contenu HTML à afficher dans la carte
        hover_effect: Active l'effet de survol (True par défaut)

    Example:
        >>> create_glass_card("<h3>Titre</h3><p>Contenu...</p>")
    """
    hover_class = "glass-card" if hover_effect else "glass-card-no-hover"

    html = f'''
    <div class="{hover_class}">
        {content}
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


def create_progress_bar(
    label: str,
    value: int,
    max_value: int,
    color: str = "blue"
):
    """
    Crée une barre de progression stylisée.

    Args:
        label: Label de la barre de progression
        value: Valeur actuelle
        max_value: Valeur maximale
        color: Couleur de la barre ("blue", "green", "orange", "red")

    Example:
        >>> create_progress_bar("Niveau", 75, 100, "blue")
    """
    percentage = min(100, (value / max_value) * 100) if max_value > 0 else 0

    # Définir les couleurs selon le paramètre
    color_map = {
        "blue": "linear-gradient(90deg, #3b82f6 0%, #06b6d4 100%)",
        "green": "linear-gradient(90deg, #10b981 0%, #059669 100%)",
        "orange": "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)",
        "red": "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)"
    }

    gradient = color_map.get(color, color_map["blue"])

    html = f'''
    <div style="margin: 15px 0;">
        <div style="
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            color: #cbd5e1;
            font-size: 0.9rem;
        ">
            <span>{label}</span>
            <span>{value} / {max_value}</span>
        </div>
        <div class="progress-bar-container">
            <div style="
                background: {gradient};
                height: 100%;
                width: {percentage}%;
                border-radius: 10px;
                transition: width 0.5s ease;
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
            "></div>
        </div>
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


def create_stat_comparison(
    icon: str,
    label: str,
    current_value: float,
    previous_value: float,
    unit: str = "",
    format_string: str = "{:.1f}"
):
    """
    Crée une carte de comparaison de statistiques avec indication de progression.

    Args:
        icon: Emoji ou icône
        label: Label de la statistique
        current_value: Valeur actuelle
        previous_value: Valeur précédente
        unit: Unité de mesure (ex: "m", "min", "°C")
        format_string: Format d'affichage des valeurs

    Example:
        >>> create_stat_comparison("⬇️", "Profondeur Max", 35.5, 30.2, "m")
    """
    # Calculer la différence et le pourcentage
    diff = current_value - previous_value

    if previous_value != 0:
        pct_change = (diff / abs(previous_value)) * 100
    else:
        pct_change = 100 if diff > 0 else 0

    # Déterminer la couleur et l'icône
    if diff > 0:
        color = "#10b981"
        arrow = "↗"
        sign = "+"
    elif diff < 0:
        color = "#ef4444"
        arrow = "↘"
        sign = ""
    else:
        color = "#6b7280"
        arrow = "→"
        sign = ""

    # Formater les valeurs
    current_str = format_string.format(current_value)
    diff_str = format_string.format(abs(diff))
    pct_str = format_string.format(abs(pct_change))

    html = f'''
    <div class="metric-card animate-fade-in">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{current_str}{unit}</div>
        <div style="
            color: {color};
            font-size: 0.9rem;
            margin-top: 8px;
            font-weight: 600;
        ">
            {arrow} {sign}{diff_str}{unit} ({sign}{pct_str}%)
        </div>
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)


def create_info_card(title: str, content: str, icon: str = "ℹ️", type: str = "info"):
    """
    Crée une carte d'information stylisée.

    Args:
        title: Titre de la carte
        content: Contenu de la carte (peut contenir du HTML)
        icon: Icône à afficher
        type: Type de carte ("info", "success", "warning", "error")

    Example:
        >>> create_info_card(
        ...     "Astuce",
        ...     "N'oubliez pas de vérifier votre équipement",
        ...     "💡",
        ...     "info"
        ... )
    """
    # Nettoyer le content: enlever l'indentation commune et les espaces de début/fin
    clean_content = textwrap.dedent(content).strip()

    # Définir les couleurs selon le type
    color_map = {
        "info": "rgba(59, 130, 246, 0.2)",
        "success": "rgba(16, 185, 129, 0.2)",
        "warning": "rgba(245, 158, 11, 0.2)",
        "error": "rgba(239, 68, 68, 0.2)"
    }

    border_map = {
        "info": "rgba(59, 130, 246, 0.4)",
        "success": "rgba(16, 185, 129, 0.4)",
        "warning": "rgba(245, 158, 11, 0.4)",
        "error": "rgba(239, 68, 68, 0.4)"
    }

    bg_color = color_map.get(type, color_map["info"])
    border_color = border_map.get(type, border_map["info"])

    html = f'''
    <div style="
        background: {bg_color};
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 2px solid {border_color};
        padding: 20px;
        margin: 15px 0;
    " class="animate-fade-in">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="font-size: 1.1rem; font-weight: 600; color: #e0f2fe;">{title}</span>
        </div>
        <div style="color: #cbd5e1; line-height: 1.6;">
            {clean_content}
        </div>
    </div>
    '''

    st.markdown(html, unsafe_allow_html=True)
