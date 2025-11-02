"""
Module d'analyse physique pour les données de plongée.

Ce module fournit des fonctions pour calculer des métriques physiques
avancées à partir des profils de plongée.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple


def calculate_average_pressure(df: pd.DataFrame) -> float:
    """
    Calcule la pression absolue moyenne en utilisant l'intégration continue.

    Formule: P_moy = (1/T) × Σ[P_abs(t_i) × Δt_i]
    où P_abs = (Profondeur/10 + 1) bar

    Args:
        df: DataFrame avec colonnes temps_secondes et profondeur_metres

    Returns:
        Pression absolue moyenne en bar

    Note:
        Cette méthode pondère chaque pression par la durée passée à cette
        profondeur, ce qui est plus précis qu'une simple moyenne arithmétique.
    """
    # Calculer la pression absolue pour chaque point
    # P_abs = (Profondeur/10 + 1) bar
    pressions = (df['profondeur_metres'] / 10) + 1

    # Calculer les intervalles de temps (Δt)
    # Pour chaque point, on prend la moitié de l'intervalle avec le point précédent
    # et la moitié avec le point suivant
    deltas = np.zeros(len(df))

    for i in range(len(df)):
        if i == 0:
            # Premier point : prendre tout l'intervalle jusqu'au suivant
            deltas[i] = df['temps_secondes'].iloc[i+1] - df['temps_secondes'].iloc[i]
        elif i == len(df) - 1:
            # Dernier point : prendre tout l'intervalle depuis le précédent
            deltas[i] = df['temps_secondes'].iloc[i] - df['temps_secondes'].iloc[i-1]
        else:
            # Points intermédiaires : moyenne des deux intervalles
            delta_avant = df['temps_secondes'].iloc[i] - df['temps_secondes'].iloc[i-1]
            delta_apres = df['temps_secondes'].iloc[i+1] - df['temps_secondes'].iloc[i]
            deltas[i] = (delta_avant + delta_apres) / 2

    # Intégration : Σ[P_abs(t_i) × Δt_i]
    integrale = np.sum(pressions * deltas)

    # Diviser par le temps total
    temps_total = df['temps_secondes'].iloc[-1] - df['temps_secondes'].iloc[0]

    return integrale / temps_total


def calculate_sac(
    df: pd.DataFrame,
    pression_debut_bar: Optional[float] = None,
    pression_fin_bar: Optional[float] = None,
    volume_bouteille_litres: Optional[float] = None
) -> Optional[Dict[str, float]]:
    """
    Calcule le SAC (Surface Air Consumption) en L/min.

    Deux modes de calcul :
    - Mode A : Avec données de pression dans le DataFrame (pression_bouteille_bar)
    - Mode B : Avec saisie manuelle (paramètres optionnels)

    Formule: SAC = (P_début - P_fin) × V_bouteille / (Temps × P_moyenne)

    Args:
        df: DataFrame avec profondeur et temps (et optionnellement pression_bouteille_bar)
        pression_debut_bar: Pression début manuelle (Mode B uniquement)
        pression_fin_bar: Pression fin manuelle (Mode B uniquement)
        volume_bouteille_litres: Volume bouteille manuel (Mode B uniquement)

    Returns:
        Dictionnaire avec:
        - sac: SAC en L/min
        - mode: 'auto' (données du fichier) ou 'manual' (saisie utilisateur)
        - pression_moyenne: Pression moyenne calculée
        Ou None si calcul impossible
    """
    # Vérifier si on a les données de pression dans le DataFrame
    has_pressure_data = 'pression_bouteille_bar' in df.columns and \
                       df['pression_bouteille_bar'].notna().any()

    # MODE A : Données de pression disponibles
    if has_pressure_data:
        # Extraire première et dernière pression valide
        pressions_valides = df['pression_bouteille_bar'].dropna()
        if len(pressions_valides) < 2:
            return None

        p_debut = pressions_valides.iloc[0]
        p_fin = pressions_valides.iloc[-1]

        # Volume bouteille : si pas fourni, utiliser valeur standard (12L bi-bouteille)
        v_bouteille = volume_bouteille_litres if volume_bouteille_litres else 12.0
        mode = 'auto'

    # MODE B : Saisie manuelle requise
    elif pression_debut_bar and pression_fin_bar and volume_bouteille_litres:
        p_debut = pression_debut_bar
        p_fin = pression_fin_bar
        v_bouteille = volume_bouteille_litres
        mode = 'manual'

    else:
        # Pas assez de données pour calculer
        return None

    # Calculer le temps total en minutes
    temps_total_min = (df['temps_secondes'].iloc[-1] - df['temps_secondes'].iloc[0]) / 60

    # Calculer la pression moyenne avec intégration continue
    p_moyenne = calculate_average_pressure(df)

    # Calculer le SAC
    # SAC = (P_début - P_fin) × V_bouteille / (Temps × P_moyenne)
    volume_consomme = (p_debut - p_fin) * v_bouteille
    sac = volume_consomme / (temps_total_min * p_moyenne)

    return {
        'sac': sac,
        'mode': mode,
        'pression_moyenne': p_moyenne,
        'volume_consomme': volume_consomme,
        'temps_total_min': temps_total_min
    }


def calculate_bottom_time(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule le temps de fond (entre 3m descente et 3m remontée).

    Le temps de fond commence quand on descend sous 3m pour la première fois
    et se termine quand on remonte au-dessus de 3m pour la dernière fois.

    Args:
        df: DataFrame avec colonnes temps_secondes et profondeur_metres

    Returns:
        Dictionnaire avec:
        - temps_fond_minutes: Temps de fond en minutes
        - temps_debut_secondes: Timestamp du début du fond
        - temps_fin_secondes: Timestamp de la fin du fond
    """
    DEPTH_THRESHOLD = 3.0  # 3 mètres

    # Trouver premier moment où on descend sous 3m
    sous_3m = df['profondeur_metres'] > DEPTH_THRESHOLD

    if not sous_3m.any():
        return {
            'temps_fond_minutes': 0,
            'temps_debut_secondes': 0,
            'temps_fin_secondes': 0
        }

    # Premier index où profondeur > 3m
    idx_debut = df[sous_3m].index[0]
    temps_debut = df.loc[idx_debut, 'temps_secondes']

    # Dernier index où profondeur > 3m
    idx_fin = df[sous_3m].index[-1]
    temps_fin = df.loc[idx_fin, 'temps_secondes']

    # Temps de fond en minutes
    temps_fond_min = (temps_fin - temps_debut) / 60

    return {
        'temps_fond_minutes': temps_fond_min,
        'temps_debut_secondes': temps_debut,
        'temps_fin_secondes': temps_fin
    }


def get_temperature_stats(df: pd.DataFrame) -> Optional[Dict[str, float]]:
    """
    Calcule les statistiques de température avec timestamps.

    Args:
        df: DataFrame avec colonnes temperature_celsius et temps_secondes

    Returns:
        Dictionnaire avec:
        - temp_min: Température minimale (°C)
        - temp_max: Température maximale (°C)
        - temp_min_time: Timestamp de la temp min (minutes)
        - temp_max_time: Timestamp de la temp max (minutes)
        Ou None si pas de données de température
    """
    if 'temperature_celsius' not in df.columns:
        return None

    # Filtrer les valeurs valides (non-NaN)
    temp_valides = df['temperature_celsius'].dropna()

    if len(temp_valides) == 0:
        return None

    # Trouver min et max
    idx_min = temp_valides.idxmin()
    idx_max = temp_valides.idxmax()

    temp_min = df.loc[idx_min, 'temperature_celsius']
    temp_max = df.loc[idx_max, 'temperature_celsius']

    time_min = df.loc[idx_min, 'temps_secondes'] / 60  # Convertir en minutes
    time_max = df.loc[idx_max, 'temps_secondes'] / 60

    return {
        'temp_min': temp_min,
        'temp_max': temp_max,
        'temp_min_time': time_min,
        'temp_max_time': time_max
    }
