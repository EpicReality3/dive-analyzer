"""
Module d'export PDF pour les rapports de plongée.

Génère des rapports PDF complets incluant :
- Statistiques de plongée
- Graphique du profil de profondeur
- Galerie de photos avec espèces identifiées
- Liste des espèces observées
"""

import io
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from PIL import Image as PILImage
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour génération PDF
import matplotlib.pyplot as plt
import pandas as pd
import requests
from urllib.parse import quote

import database
import media_manager
import species_recognition
import parser as dive_parser
import visualizer
from logger import get_logger
from config import config

logger = get_logger(__name__)

# Configuration PDF
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 2 * cm
MARGIN_RIGHT = 2 * cm
MARGIN_TOP = 2 * cm
MARGIN_BOTTOM = 2 * cm
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# Dossier d'export
EXPORT_DIR = config.APP_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


def generate_dive_pdf(dive_id: int, output_path: Optional[Path] = None) -> Optional[Path]:
    """
    Génère un rapport PDF complet pour une plongée.

    Args:
        dive_id: ID de la plongée à exporter
        output_path: Chemin de sortie optionnel. Si None, génère dans exports/

    Returns:
        Path du fichier PDF créé, ou None si erreur
    """
    try:
        logger.info(f"Génération PDF pour plongée {dive_id}")

        # 1. Récupérer toutes les données
        dive_data = database.get_dive_by_id(dive_id)
        if not dive_data:
            logger.error(f"Plongée {dive_id} introuvable")
            return None

        # Récupérer le DataFrame du profil
        df = database.get_dive_cache(dive_id)
        if df is None:
            # Tenter de parser le fichier
            file_path = Path(dive_data['fichier_original_path'])
            if file_path.exists():
                logger.info(f"Parsing du fichier {file_path}")

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
                df = dive_parser.parse_dive_file(fake_file)
            else:
                logger.warning(f"Fichier de profil introuvable : {file_path}")
                df = None

        dive_media = media_manager.get_dive_media(dive_id)
        dive_species = species_recognition.get_dive_species(dive_id)

        # 2. Déterminer le chemin de sortie
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dive_{dive_id}_{timestamp}.pdf"
            output_path = EXPORT_DIR / filename

        # 3. Créer le PDF
        c = canvas.Canvas(str(output_path), pagesize=A4)

        # Position verticale courante
        y = PAGE_HEIGHT - MARGIN_TOP

        # 4. Ajouter les sections
        y = _create_header(c, dive_data, y)
        y = _add_statistics_section(c, dive_data, y)

        if df is not None and not df.empty:
            y = _add_dive_profile_graph(c, df, y)

        # Ajouter la carte de localisation
        y = _add_location_map(c, dive_data, y)

        if dive_species:
            y = _add_species_list(c, dive_species, y)

        if dive_media:
            y = _add_photo_gallery(c, dive_media, dive_species, y)

        # 5. Ajouter footer avec métadonnées
        _add_footer(c, dive_id)

        # 6. Sauvegarder
        c.save()
        logger.info(f"PDF généré avec succès : {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF : {e}", exc_info=True)
        return None


def _create_header(c: canvas.Canvas, dive_data: Dict[str, Any], y: float) -> float:
    """
    Crée l'entête du rapport PDF.

    Args:
        c: Canvas PDF
        dive_data: Données de la plongée
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    # Titre principal
    c.setFont("Helvetica-Bold", 20)
    c.drawString(MARGIN_LEFT, y, "RAPPORT DE PLONGÉE")
    y -= 25

    # Ligne de séparation
    c.setStrokeColor(colors.HexColor("#1f77b4"))
    c.setLineWidth(2)
    c.line(MARGIN_LEFT, y, PAGE_WIDTH - MARGIN_RIGHT, y)
    y -= 20

    # Informations générales
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)

    # Date
    date_str = dive_data['date']
    if date_str:
        try:
            date_obj = datetime.fromisoformat(date_str.replace(' ', 'T'))
            date_formatted = date_obj.strftime("%d/%m/%Y à %H:%M")
        except:
            date_formatted = date_str
    else:
        date_formatted = "Date inconnue"

    c.drawString(MARGIN_LEFT, y, f"📅 Date : {date_formatted}")
    y -= 18

    # Site
    c.drawString(MARGIN_LEFT, y, f"📍 Site : {dive_data['site_nom']}")
    y -= 18

    # Buddy
    if dive_data['buddy_nom']:
        c.drawString(MARGIN_LEFT, y, f"👥 Buddy : {dive_data['buddy_nom']}")
        y -= 18

    # Type et note
    dive_type = dive_data.get('dive_type', '').capitalize()
    rating = dive_data.get('rating', 0)
    rating_stars = "⭐" * int(rating) if rating else "N/A"

    c.drawString(MARGIN_LEFT, y, f"🤿 Type : {dive_type}")
    c.drawString(PAGE_WIDTH - MARGIN_RIGHT - 120, y, f"Note : {rating_stars}")
    y -= 30

    return y


def _add_statistics_section(c: canvas.Canvas, dive_data: Dict[str, Any], y: float) -> float:
    """
    Ajoute la section des statistiques techniques.

    Args:
        c: Canvas PDF
        dive_data: Données de la plongée
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    # Titre de section
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1f77b4"))
    c.drawString(MARGIN_LEFT, y, "📊 STATISTIQUES TECHNIQUES")
    y -= 20

    c.setFillColor(colors.black)

    # Créer tableau des statistiques
    data = []

    # Ligne 1
    prof_max = f"{dive_data['profondeur_max']:.1f} m" if dive_data['profondeur_max'] else "N/A"
    duree = f"{dive_data['duree_minutes']:.0f} min" if dive_data['duree_minutes'] else "N/A"
    data.append(["Profondeur max", prof_max, "Durée totale", duree])

    # Ligne 2
    temp = f"{dive_data['temperature_min']:.1f}°C" if dive_data['temperature_min'] else "N/A"
    sac = f"{dive_data['sac']:.1f} L/min" if dive_data['sac'] else "N/A"
    data.append(["Température min", temp, "SAC", sac])

    # Ligne 3
    temps_fond = f"{dive_data.get('temps_fond_minutes', 0):.1f} min" if dive_data.get('temps_fond_minutes') else "N/A"
    vitesse_max = f"{dive_data.get('vitesse_remontee_max', 0):.1f} m/min" if dive_data.get('vitesse_remontee_max') else "N/A"
    data.append(["Temps de fond", temps_fond, "Vitesse remontée max", vitesse_max])

    # Créer le tableau
    col_widths = [CONTENT_WIDTH * 0.3, CONTENT_WIDTH * 0.2, CONTENT_WIDTH * 0.3, CONTENT_WIDTH * 0.2]
    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0f0f0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    # Calculer hauteur du tableau
    table_width, table_height = table.wrapOn(c, CONTENT_WIDTH, PAGE_HEIGHT)
    table.drawOn(c, MARGIN_LEFT, y - table_height)
    y -= table_height + 10

    # Conditions environnementales
    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN_LEFT, y, "Conditions :")
    y -= 15

    c.setFont("Helvetica", 10)
    conditions_parts = []

    if dive_data.get('houle'):
        conditions_parts.append(f"Houle : {dive_data['houle']}")
    if dive_data.get('visibilite_metres'):
        conditions_parts.append(f"Visibilité : {dive_data['visibilite_metres']}m")
    if dive_data.get('courant'):
        conditions_parts.append(f"Courant : {dive_data['courant']}")

    if conditions_parts:
        conditions_text = " • ".join(conditions_parts)
        c.drawString(MARGIN_LEFT + 10, y, conditions_text)
        y -= 18

    # Notes
    if dive_data.get('notes'):
        y -= 5
        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN_LEFT, y, "Notes :")
        y -= 15

        c.setFont("Helvetica", 9)
        # Gérer texte multi-lignes
        notes = dive_data['notes']
        max_width = CONTENT_WIDTH - 10

        # Découper en lignes
        from reportlab.pdfbase.pdfmetrics import stringWidth
        words = notes.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if stringWidth(test_line, "Helvetica", 9) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Limiter à 5 lignes pour ne pas déborder
        for line in lines[:5]:
            c.drawString(MARGIN_LEFT + 10, y, line)
            y -= 12

        if len(lines) > 5:
            c.drawString(MARGIN_LEFT + 10, y, "...")
            y -= 12

    y -= 20
    return y


def _add_dive_profile_graph(c: canvas.Canvas, df, y: float) -> float:
    """
    Ajoute le graphique du profil de plongée.

    Args:
        c: Canvas PDF
        df: DataFrame avec les données de profil
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    try:
        # Titre de section
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#1f77b4"))
        c.drawString(MARGIN_LEFT, y, "📈 PROFIL DE PLONGÉE")
        y -= 25

        c.setFillColor(colors.black)

        # Créer le graphique avec matplotlib (plus fiable que Kaleido)
        temps_minutes = df['temps_secondes'] / 60
        profondeur = df['profondeur_metres']

        # Calculer vitesses de remontée pour coloration
        speeds = visualizer.calculate_ascent_speed(df)

        # Créer la figure matplotlib
        fig_mpl, ax = plt.subplots(figsize=(12, 5), dpi=150)

        # Tracer le profil avec segments colorés selon vitesse
        i = 0
        while i < len(df):
            speed = speeds.iloc[i]

            # Déterminer couleur
            if speed < 10:
                color = '#1f77b4'  # Bleu
            elif speed < 15:
                color = '#ff7f0e'  # Orange
            else:
                color = '#d62728'  # Rouge

            # Trouver fin du segment de même couleur
            j = i + 1
            while j < len(df):
                next_speed = speeds.iloc[j]
                if (next_speed < 10 and speed >= 10) or \
                   (next_speed >= 10 and next_speed < 15 and (speed < 10 or speed >= 15)) or \
                   (next_speed >= 15 and speed < 15):
                    break
                j += 1

            # Tracer segment
            ax.plot(temps_minutes.iloc[i:j+1], profondeur.iloc[i:j+1],
                   color=color, linewidth=2)
            i = j

        # Annoter profondeur max
        max_depth_idx = df['profondeur_metres'].idxmax()
        max_depth = df['profondeur_metres'].iloc[max_depth_idx]
        max_depth_time = temps_minutes.iloc[max_depth_idx]
        ax.annotate(f'Prof. Max: {max_depth:.1f} m',
                   xy=(max_depth_time, max_depth),
                   xytext=(max_depth_time + 2, max_depth - 2),
                   arrowprops=dict(arrowstyle='->', color='#d62728', lw=2),
                   fontsize=10, color='#d62728', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#d62728', linewidth=2))

        # Configuration axes
        ax.set_xlabel('Temps (minutes)', fontsize=11, weight='bold')
        ax.set_ylabel('Profondeur (mètres)', fontsize=11, weight='bold')
        ax.set_title('Profil de Plongée', fontsize=13, weight='bold', pad=15)
        ax.invert_yaxis()  # Inverser axe Y
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('white')
        fig_mpl.patch.set_facecolor('white')

        # Convertir en PNG
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig_mpl)
        buf.seek(0)

        # Charger l'image avec PIL
        img = PILImage.open(buf)

        # Calculer les dimensions pour le PDF (max width = CONTENT_WIDTH)
        img_width, img_height = img.size
        aspect_ratio = img_height / img_width
        pdf_img_width = min(CONTENT_WIDTH, 16 * cm)
        pdf_img_height = pdf_img_width * aspect_ratio

        # Vérifier si l'image tient sur la page
        if y - pdf_img_height < MARGIN_BOTTOM:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN_TOP

        # Dessiner l'image
        img_path = EXPORT_DIR / "temp_graph.png"
        img.save(img_path, "PNG")

        c.drawImage(str(img_path), MARGIN_LEFT, y - pdf_img_height,
                   width=pdf_img_width, height=pdf_img_height)

        # Nettoyer le fichier temporaire
        img_path.unlink()

        y -= pdf_img_height + 10

        # Bandeau sécurité
        speeds = visualizer.calculate_ascent_speed(df)
        max_speed = speeds.max()

        c.setFont("Helvetica-Bold", 10)
        if max_speed < 10.0:
            c.setFillColor(colors.green)
            safety_text = f"✓ Plongée sécuritaire - Vitesse remontée max : {max_speed:.1f} m/min"
        else:
            c.setFillColor(colors.red)
            safety_text = f"⚠ Alerte - Vitesse remontée max : {max_speed:.1f} m/min (> 10 m/min)"

        c.drawString(MARGIN_LEFT, y, safety_text)
        y -= 25

        c.setFillColor(colors.black)

    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du graphique : {e}", exc_info=True)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.red)
        c.drawString(MARGIN_LEFT, y, "⚠ Impossible de générer le graphique de profil")
        y -= 20
        c.setFillColor(colors.black)

    return y


def _add_location_map(c: canvas.Canvas, dive_data: Dict[str, Any], y: float) -> float:
    """
    Ajoute une carte statique du site de plongée si les coordonnées GPS sont disponibles.

    Args:
        c: Canvas PDF
        dive_data: Données de la plongée (doit contenir site_id)
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    try:
        # Récupérer le site complet avec coordonnées GPS
        site_data = database.get_site_by_name(dive_data['site_nom'])

        if not site_data or not site_data.get('coordonnees_gps'):
            logger.info("Pas de coordonnées GPS disponibles pour ce site")
            return y

        # Parser les coordonnées
        coords = site_data['coordonnees_gps'].split(',')
        if len(coords) != 2:
            logger.warning(f"Format de coordonnées invalide: {site_data['coordonnees_gps']}")
            return y

        try:
            lat = float(coords[0].strip())
            lon = float(coords[1].strip())
        except ValueError:
            logger.warning(f"Coordonnées GPS invalides: {site_data['coordonnees_gps']}")
            return y

        # Vérifier l'espace disponible
        if y - 250 < MARGIN_BOTTOM:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN_TOP

        # Titre de section
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#1f77b4"))
        c.drawString(MARGIN_LEFT, y, "🗺️ LOCALISATION")
        y -= 25

        c.setFillColor(colors.black)

        # Créer une carte simple avec matplotlib
        fig_map, ax_map = plt.subplots(figsize=(8, 4), dpi=150)

        # Créer une carte basique avec un marqueur
        # Utiliser un fond bleu pour l'océan
        ax_map.set_xlim(lon - 0.05, lon + 0.05)
        ax_map.set_ylim(lat - 0.025, lat + 0.025)
        ax_map.set_facecolor('#b3d9ff')  # Bleu clair pour l'eau

        # Ajouter un marqueur rouge pour le site
        ax_map.plot(lon, lat, 'ro', markersize=15, label=dive_data['site_nom'],
                   markeredgecolor='white', markeredgewidth=2, zorder=5)

        # Ajouter une grille
        ax_map.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Labels
        ax_map.set_xlabel('Longitude', fontsize=10, weight='bold')
        ax_map.set_ylabel('Latitude', fontsize=10, weight='bold')
        ax_map.set_title(f'Site: {dive_data["site_nom"]}', fontsize=11, weight='bold', pad=10)

        # Ajouter les coordonnées en texte
        coord_text = f'📍 {lat:.4f}°, {lon:.4f}°'
        ax_map.text(0.5, 0.02, coord_text, transform=ax_map.transAxes,
                   ha='center', va='bottom', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))

        # Légende
        ax_map.legend(loc='upper right', fontsize=9)

        # Note : Pour une meilleure carte, on pourrait télécharger une tuile OSM
        # mais cela nécessiterait une connexion internet et des packages supplémentaires

        # Convertir en PNG
        buf_map = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf_map, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig_map)
        buf_map.seek(0)

        # Charger l'image avec PIL
        img_map = PILImage.open(buf_map)

        # Calculer les dimensions pour le PDF
        img_width, img_height = img_map.size
        aspect_ratio = img_height / img_width
        pdf_img_width = min(CONTENT_WIDTH, 14 * cm)
        pdf_img_height = pdf_img_width * aspect_ratio

        # Dessiner l'image
        img_path = EXPORT_DIR / "temp_map.png"
        img_map.save(img_path, "PNG")

        c.drawImage(str(img_path), MARGIN_LEFT, y - pdf_img_height,
                   width=pdf_img_width, height=pdf_img_height)

        # Nettoyer le fichier temporaire
        img_path.unlink()

        y -= pdf_img_height + 15

        # Informations GPS en texte
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#666666"))
        info_text = f"Coordonnées GPS: {lat:.6f}°, {lon:.6f}° | {site_data.get('pays', 'Non renseigné')}"
        c.drawString(MARGIN_LEFT, y, info_text)
        y -= 25

        c.setFillColor(colors.black)

        logger.info(f"Carte ajoutée pour le site {dive_data['site_nom']}")

    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la carte : {e}", exc_info=True)
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.red)
        c.drawString(MARGIN_LEFT, y, "⚠ Impossible de générer la carte")
        y -= 20
        c.setFillColor(colors.black)

    return y


def _add_species_list(c: canvas.Canvas, dive_species: List[Dict[str, Any]], y: float) -> float:
    """
    Ajoute la liste des espèces observées.

    Args:
        c: Canvas PDF
        dive_species: Liste des espèces observées
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    # Vérifier si nouvelle page nécessaire
    if y < MARGIN_BOTTOM + 100:
        c.showPage()
        y = PAGE_HEIGHT - MARGIN_TOP

    # Titre de section
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1f77b4"))
    c.drawString(MARGIN_LEFT, y, f"🐠 ESPÈCES OBSERVÉES ({len(dive_species)})")
    y -= 20

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)

    # Emojis par catégorie
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

    for species in dive_species:
        # Vérifier si on doit changer de page
        if y < MARGIN_BOTTOM + 30:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN_TOP

        emoji = emoji_map.get(species['category'], '🌊')
        common_name = species['common_name_fr'] or species['scientific_name']

        # Nom commun en normal
        c.setFont("Helvetica", 10)
        text = f"{emoji} {common_name}"
        c.drawString(MARGIN_LEFT, y, text)

        # Nom scientifique en italique
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.grey)
        c.drawString(MARGIN_LEFT + 15, y - 12, species['scientific_name'])

        c.setFillColor(colors.black)

        # Informations additionnelles
        info_parts = []
        if species.get('quantity') and species['quantity'] > 1:
            info_parts.append(f"Qté: {species['quantity']}")

        if species.get('detected_by'):
            detection_map = {'ai': '🤖 IA', 'manual': '✍️ Manuel', 'verified': '✓ Vérifié'}
            info_parts.append(detection_map.get(species['detected_by'], ''))

        if info_parts:
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.HexColor("#666666"))
            c.drawString(PAGE_WIDTH - MARGIN_RIGHT - 100, y - 6, " • ".join(info_parts))
            c.setFillColor(colors.black)

        y -= 25

    y -= 15
    return y


def _add_photo_gallery(c: canvas.Canvas, dive_media: List[Dict[str, Any]],
                       dive_species: List[Dict[str, Any]], y: float) -> float:
    """
    Ajoute la galerie de photos avec les espèces identifiées.

    Args:
        c: Canvas PDF
        dive_media: Liste des médias de la plongée
        dive_species: Liste des espèces (pour lier aux médias)
        y: Position verticale courante

    Returns:
        Nouvelle position verticale
    """
    # Filtrer uniquement les photos
    photos = [m for m in dive_media if m['type'] == 'photo']

    if not photos:
        return y

    # Vérifier si nouvelle page nécessaire
    if y < MARGIN_BOTTOM + 100:
        c.showPage()
        y = PAGE_HEIGHT - MARGIN_TOP

    # Titre de section
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1f77b4"))
    c.drawString(MARGIN_LEFT, y, f"📸 GALERIE PHOTOS ({len(photos)})")
    y -= 25

    c.setFillColor(colors.black)

    # Ajouter chaque photo
    for idx, media in enumerate(photos, 1):
        photo_path = Path(media['filepath'])

        if not photo_path.exists():
            logger.warning(f"Photo introuvable : {photo_path}")
            continue

        # Vérifier si nouvelle page nécessaire
        if y < MARGIN_BOTTOM + 120:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN_TOP

        try:
            # Charger l'image
            img = PILImage.open(photo_path)

            # Calculer dimensions (max 12cm de large)
            img_width, img_height = img.size
            aspect_ratio = img_height / img_width
            pdf_img_width = min(12 * cm, CONTENT_WIDTH)
            pdf_img_height = pdf_img_width * aspect_ratio

            # Limiter la hauteur à 10cm
            if pdf_img_height > 10 * cm:
                pdf_img_height = 10 * cm
                pdf_img_width = pdf_img_height / aspect_ratio

            # Vérifier si l'image tient
            if y - pdf_img_height - 40 < MARGIN_BOTTOM:
                c.showPage()
                y = PAGE_HEIGHT - MARGIN_TOP

            # Dessiner l'image
            c.drawImage(str(photo_path), MARGIN_LEFT, y - pdf_img_height,
                       width=pdf_img_width, height=pdf_img_height,
                       preserveAspectRatio=True)

            y -= pdf_img_height + 5

            # Caption avec espèces
            caption = _format_species_caption(media['id'], dive_species)

            if caption:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.HexColor("#666666"))

                # Gérer caption multi-lignes
                max_caption_width = pdf_img_width
                from reportlab.pdfbase.pdfmetrics import stringWidth

                if stringWidth(caption, "Helvetica-Oblique", 8) > max_caption_width:
                    # Tronquer si trop long
                    while stringWidth(caption + "...", "Helvetica-Oblique", 8) > max_caption_width and len(caption) > 20:
                        caption = caption[:-1]
                    caption += "..."

                c.drawString(MARGIN_LEFT, y, caption)
                y -= 12
                c.setFillColor(colors.black)

            y -= 10

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la photo {photo_path} : {e}")
            continue

    return y


def _format_species_caption(media_id: int, dive_species: List[Dict[str, Any]]) -> str:
    """
    Formate la caption d'une photo avec les espèces identifiées.

    Args:
        media_id: ID du média
        dive_species: Liste complète des espèces de la plongée

    Returns:
        Caption formatée
    """
    # Récupérer les espèces pour ce média
    media_species = species_recognition.get_media_species(media_id)

    if not media_species:
        return ""

    # Formater les 3 premières espèces
    caption_parts = []
    for sp in media_species[:3]:
        common = sp['common_name_fr'] or sp['scientific_name']
        scientific = sp['scientific_name']
        caption_parts.append(f"{common} ({scientific})")

    if len(media_species) > 3:
        caption_parts.append(f"+ {len(media_species) - 3} autres")

    return " • ".join(caption_parts)


def _add_footer(c: canvas.Canvas, dive_id: int) -> None:
    """
    Ajoute un footer avec métadonnées sur toutes les pages.

    Args:
        c: Canvas PDF
        dive_id: ID de la plongée
    """
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)

    # Footer gauche
    footer_left = f"Dive Analyzer - Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    c.drawString(MARGIN_LEFT, MARGIN_BOTTOM - 10, footer_left)

    # Footer droit
    footer_right = f"Plongée #{dive_id}"
    c.drawRightString(PAGE_WIDTH - MARGIN_RIGHT, MARGIN_BOTTOM - 10, footer_right)

    c.setFillColor(colors.black)
