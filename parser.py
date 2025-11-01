"""
Module de parsing pour les fichiers de plongée.

Ce module définit une architecture extensible pour parser différents formats
de fichiers de plongée (FIT, XML, UDDF, DL7) vers un DataFrame pandas unifié.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from abc import ABC, abstractmethod
from fitparse import FitFile
from io import BytesIO
import xml.etree.ElementTree as ET


class BaseDiveParser(ABC):
    """
    Classe abstraite de base pour tous les parsers de fichiers de plongée.

    Cette interface garantit que tous les parsers implémentent une méthode parse()
    qui retourne un DataFrame avec une structure standardisée :
    - temps_secondes : float (temps écoulé depuis le début de la plongée)
    - profondeur_metres : float (profondeur en mètres)
    - temperature_celsius : float (température de l'eau)
    - pression_bouteille_bar : float (pression restante dans la bouteille)
    """

    def __init__(self, file_content: bytes):
        """
        Initialise le parser avec le contenu du fichier.

        Args:
            file_content: Contenu brut du fichier en bytes
        """
        self.file_content = file_content

    @abstractmethod
    def parse(self) -> pd.DataFrame:
        """
        Parse le fichier et retourne un DataFrame standardisé.

        Returns:
            DataFrame avec colonnes : temps_secondes, profondeur_metres,
            temperature_celsius, pression_bouteille_bar
        """
        pass


class FitParser(BaseDiveParser):
    """Parser pour les fichiers Garmin FIT."""

    def parse(self) -> pd.DataFrame:
        """
        Parse un fichier FIT et extrait les données de plongée.

        Returns:
            DataFrame avec les données de plongée parsées, trié par temps
        """
        try:
            # Créer un objet FitFile depuis le contenu bytes
            fitfile = FitFile(BytesIO(self.file_content))

            # Liste pour stocker les points de données
            data_points = []
            first_timestamp = None

            # Parcourir tous les messages de type 'record' (points de mesure)
            for record in fitfile.get_messages('record'):
                # Convertir le record en dictionnaire de valeurs
                record_data = {}

                for data in record:
                    record_data[data.name] = data.value

                # Vérifier que nous avons au moins un timestamp
                if 'timestamp' not in record_data:
                    continue

                # Initialiser le premier timestamp pour calculer le temps relatif
                if first_timestamp is None:
                    first_timestamp = record_data['timestamp']

                # Calculer le temps écoulé en secondes depuis le début de la plongée
                time_delta = (record_data['timestamp'] - first_timestamp).total_seconds()

                # Extraire les données (avec valeurs par défaut si absent)
                # La profondeur peut être sous différents noms selon le modèle
                depth = record_data.get('depth', np.nan)
                if depth is not None and not isinstance(depth, float):
                    depth = float(depth)

                # Température
                temperature = record_data.get('temperature', np.nan)
                if temperature is not None and not isinstance(temperature, float):
                    temperature = float(temperature)

                # Pression bouteille (peut varier selon le modèle Garmin)
                # Chercher différents noms possibles
                tank_pressure = record_data.get('tank_pressure',
                               record_data.get('pressure',
                               record_data.get('cylinder_pressure', np.nan)))
                if tank_pressure is not None and not isinstance(tank_pressure, float):
                    tank_pressure = float(tank_pressure)

                # Ajouter le point de données
                data_points.append({
                    'temps_secondes': int(time_delta),
                    'profondeur_metres': depth,
                    'temperature_celsius': temperature,
                    'pression_bouteille_bar': tank_pressure
                })

            # Créer le DataFrame
            df = pd.DataFrame(data_points)

            # S'assurer que le DataFrame a les bonnes colonnes même s'il est vide
            if df.empty:
                df = pd.DataFrame(columns=[
                    'temps_secondes',
                    'profondeur_metres',
                    'temperature_celsius',
                    'pression_bouteille_bar'
                ])
            else:
                # Trier par temps
                df = df.sort_values('temps_secondes').reset_index(drop=True)

            return df

        except Exception as e:
            # En cas d'erreur, logger et retourner DataFrame vide
            print(f"Erreur lors du parsing FIT: {e}")
            return pd.DataFrame(columns=[
                'temps_secondes',
                'profondeur_metres',
                'temperature_celsius',
                'pression_bouteille_bar'
            ])


class XmlParser(BaseDiveParser):
    """Parser pour les fichiers XML génériques."""

    def parse(self) -> pd.DataFrame:
        """
        Parse un fichier XML.

        TODO: Implémenter parsing XML
        """
        # Retourne DataFrame vide avec la structure attendue
        return pd.DataFrame(columns=[
            'temps_secondes',
            'profondeur_metres',
            'temperature_celsius',
            'pression_bouteille_bar'
        ])


class UddfParser(BaseDiveParser):
    """Parser pour les fichiers UDDF (Universal Dive Data Format)."""

    def parse(self) -> pd.DataFrame:
        """
        Parse un fichier UDDF et extrait les données de plongée.

        Format UDDF typique :
        <uddf>
          <profiledata>
            <repetitiongroup>
              <dive>
                <samples>
                  <waypoint>
                    <divetime>0</divetime>
                    <depth>0.0</depth>
                    <temperature>24.0</temperature>
                    <tankpressure>200.0</tankpressure>
                  </waypoint>
                </samples>
              </dive>
            </repetitiongroup>
          </profiledata>
        </uddf>

        Returns:
            DataFrame avec les données de plongée parsées, trié par temps
        """
        try:
            # Parser le XML depuis le contenu bytes
            root = ET.fromstring(self.file_content)

            # Liste pour stocker les points de données
            data_points = []

            # Trouver tous les waypoints (points de mesure) dans le fichier
            # Le './/waypoint' recherche récursivement tous les éléments waypoint
            waypoints = root.findall('.//waypoint')

            for waypoint in waypoints:
                # Extraire le temps de plongée (divetime en secondes)
                divetime_elem = waypoint.find('divetime')
                if divetime_elem is not None and divetime_elem.text:
                    temps_secondes = float(divetime_elem.text)
                else:
                    # Si pas de temps, on ne peut pas utiliser ce point
                    continue

                # Extraire la profondeur (depth en mètres)
                depth_elem = waypoint.find('depth')
                profondeur_metres = float(depth_elem.text) if depth_elem is not None and depth_elem.text else np.nan

                # Extraire la température (temperature en Celsius)
                temp_elem = waypoint.find('temperature')
                temperature_celsius = float(temp_elem.text) if temp_elem is not None and temp_elem.text else np.nan

                # Extraire la pression de la bouteille (tankpressure en bar)
                # Certains fichiers peuvent utiliser d'autres noms
                pressure_elem = waypoint.find('tankpressure')
                if pressure_elem is None:
                    pressure_elem = waypoint.find('pressure')
                pression_bouteille_bar = float(pressure_elem.text) if pressure_elem is not None and pressure_elem.text else np.nan

                # Ajouter le point de données
                data_points.append({
                    'temps_secondes': int(temps_secondes),
                    'profondeur_metres': profondeur_metres,
                    'temperature_celsius': temperature_celsius,
                    'pression_bouteille_bar': pression_bouteille_bar
                })

            # Créer le DataFrame
            df = pd.DataFrame(data_points)

            # S'assurer que le DataFrame a les bonnes colonnes même s'il est vide
            if df.empty:
                df = pd.DataFrame(columns=[
                    'temps_secondes',
                    'profondeur_metres',
                    'temperature_celsius',
                    'pression_bouteille_bar'
                ])
            else:
                # Trier par temps
                df = df.sort_values('temps_secondes').reset_index(drop=True)

            return df

        except ET.ParseError as e:
            # Erreur de parsing XML
            print(f"Erreur lors du parsing XML UDDF: {e}")
            return pd.DataFrame(columns=[
                'temps_secondes',
                'profondeur_metres',
                'temperature_celsius',
                'pression_bouteille_bar'
            ])
        except Exception as e:
            # Autres erreurs
            print(f"Erreur lors du parsing UDDF: {e}")
            return pd.DataFrame(columns=[
                'temps_secondes',
                'profondeur_metres',
                'temperature_celsius',
                'pression_bouteille_bar'
            ])


class Dl7Parser(BaseDiveParser):
    """Parser pour les fichiers DL7."""

    def parse(self) -> pd.DataFrame:
        """
        Parse un fichier DL7.

        TODO: Implémenter parsing DL7
        """
        # Retourne DataFrame vide avec la structure attendue
        return pd.DataFrame(columns=[
            'temps_secondes',
            'profondeur_metres',
            'temperature_celsius',
            'pression_bouteille_bar'
        ])


def parse_dive_file(uploaded_file) -> pd.DataFrame:
    """
    Détecte le format du fichier et utilise le parser approprié.

    Args:
        uploaded_file: Fichier uploadé via Streamlit (avec attributs .name et .read())

    Returns:
        DataFrame avec les données de plongée parsées

    Raises:
        ValueError: Si le format de fichier n'est pas supporté
    """
    # Récupérer l'extension du fichier
    file_extension = Path(uploaded_file.name).suffix.lower()

    # Lire le contenu du fichier
    file_content = uploaded_file.read()

    # Sélectionner le parser approprié selon l'extension
    if file_extension == '.fit':
        parser = FitParser(file_content)
    elif file_extension == '.xml':
        parser = XmlParser(file_content)
    elif file_extension == '.uddf':
        parser = UddfParser(file_content)
    elif file_extension == '.dl7':
        parser = Dl7Parser(file_content)
    else:
        raise ValueError(f"Format de fichier non supporté : {file_extension}")

    # Parser et retourner le DataFrame
    return parser.parse()
