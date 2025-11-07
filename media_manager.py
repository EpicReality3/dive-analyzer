"""
Module de gestion des médias (photos et vidéos) pour le journal de plongée.

Fonctionnalités :
- Upload et stockage de photos/vidéos
- Génération de miniatures pour les photos
- Validation des types de fichiers
- Association des médias aux plongées
- Récupération et affichage des médias
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import shutil
import mimetypes
from PIL import Image
import io
from logger import get_logger
from database import get_connection
from config import config

logger = get_logger(__name__)

# Configuration des médias
MEDIA_DIR = config.APP_DIR / "media"
PHOTO_DIR = MEDIA_DIR / "photos"
VIDEO_DIR = MEDIA_DIR / "videos"
THUMBNAIL_DIR = MEDIA_DIR / "thumbnails"

# Types de fichiers acceptés
ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm', '.mkv'}
MAX_MEDIA_SIZE_MB = 200  # 200 MB max pour les vidéos

# Taille des miniatures
THUMBNAIL_SIZE = (300, 300)


def init_media_directories() -> None:
    """
    Crée les répertoires nécessaires pour stocker les médias.
    """
    for directory in [MEDIA_DIR, PHOTO_DIR, VIDEO_DIR, THUMBNAIL_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Répertoire média créé/vérifié : {directory}")


def validate_media_file(file_path: Path, file_size: int) -> Tuple[bool, str, str]:
    """
    Valide un fichier média.

    Args:
        file_path: Chemin du fichier
        file_size: Taille du fichier en octets

    Returns:
        Tuple (is_valid, media_type, error_message)
        - is_valid: True si le fichier est valide
        - media_type: 'photo' ou 'video'
        - error_message: Message d'erreur si invalide
    """
    extension = file_path.suffix.lower()

    # Vérifier l'extension
    if extension in ALLOWED_PHOTO_EXTENSIONS:
        media_type = 'photo'
    elif extension in ALLOWED_VIDEO_EXTENSIONS:
        media_type = 'video'
    else:
        return False, '', f"Extension non supportée : {extension}"

    # Vérifier la taille
    size_mb = file_size / (1024 * 1024)
    if size_mb > MAX_MEDIA_SIZE_MB:
        return False, '', f"Fichier trop volumineux : {size_mb:.1f}MB (max {MAX_MEDIA_SIZE_MB}MB)"

    return True, media_type, ''


def create_thumbnail(image_path: Path, thumbnail_path: Path) -> bool:
    """
    Crée une miniature pour une image.

    Args:
        image_path: Chemin de l'image source
        thumbnail_path: Chemin de la miniature à créer

    Returns:
        True si la miniature a été créée avec succès
    """
    try:
        with Image.open(image_path) as img:
            # Convertir en RGB si nécessaire (pour les PNG avec transparence, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Redimensionner en gardant les proportions
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Sauvegarder la miniature
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            logger.debug(f"Miniature créée : {thumbnail_path}")
            return True

    except Exception as e:
        logger.error(f"Erreur lors de la création de la miniature : {e}")
        return False


def get_image_dimensions(image_path: Path) -> Tuple[Optional[int], Optional[int]]:
    """
    Récupère les dimensions d'une image.

    Args:
        image_path: Chemin de l'image

    Returns:
        Tuple (width, height) ou (None, None) si erreur
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Erreur lors de la lecture des dimensions : {e}")
        return None, None


def add_media_to_dive(
    dive_id: int,
    file_path: Path,
    file_size: int,
    description: str = '',
    tags: str = ''
) -> Optional[int]:
    """
    Ajoute un média (photo ou vidéo) à une plongée.

    Args:
        dive_id: ID de la plongée
        file_path: Chemin du fichier média
        file_size: Taille du fichier en octets
        description: Description optionnelle
        tags: Tags optionnels (séparés par des virgules)

    Returns:
        ID du média créé, ou None si erreur
    """
    # Valider le fichier
    is_valid, media_type, error_msg = validate_media_file(file_path, file_size)
    if not is_valid:
        logger.error(f"Validation échouée : {error_msg}")
        return None

    # Initialiser les répertoires
    init_media_directories()

    # Déterminer le répertoire de destination
    dest_dir = PHOTO_DIR if media_type == 'photo' else VIDEO_DIR

    # Générer un nom de fichier unique
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{dive_id}_{timestamp}{file_path.suffix.lower()}"
    dest_path = dest_dir / filename

    try:
        # Copier le fichier
        shutil.copy2(file_path, dest_path)
        logger.info(f"Fichier copié : {dest_path}")

        # Obtenir le type MIME
        mime_type = mimetypes.guess_type(str(dest_path))[0]

        # Traitement spécifique aux photos
        thumbnail_path = None
        width, height = None, None

        if media_type == 'photo':
            # Créer la miniature
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path_obj = THUMBNAIL_DIR / thumbnail_filename
            if create_thumbnail(dest_path, thumbnail_path_obj):
                thumbnail_path = str(thumbnail_path_obj)

            # Récupérer les dimensions
            width, height = get_image_dimensions(dest_path)

        # Insérer dans la base de données
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO dive_media
            (dive_id, type, filename, filepath, thumbnail_path, file_size_bytes,
             mime_type, width, height, upload_date, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dive_id, media_type, filename, str(dest_path), thumbnail_path,
            file_size, mime_type, width, height, datetime.now().isoformat(),
            description, tags
        ))

        conn.commit()
        media_id = cursor.lastrowid
        conn.close()

        logger.info(f"Média ajouté avec succès : ID={media_id}, type={media_type}")
        return media_id

    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du média : {e}")
        # Nettoyer le fichier copié en cas d'erreur
        if dest_path.exists():
            dest_path.unlink()
        return None


def get_dive_media(dive_id: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les médias associés à une plongée.

    Args:
        dive_id: ID de la plongée

    Returns:
        Liste de dictionnaires contenant les informations des médias
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, filename, filepath, thumbnail_path, file_size_bytes,
               mime_type, width, height, duration_seconds, upload_date,
               description, tags
        FROM dive_media
        WHERE dive_id = ?
        ORDER BY upload_date DESC
    """, (dive_id,))

    columns = [desc[0] for desc in cursor.description]
    media_list = []

    for row in cursor.fetchall():
        media_dict = dict(zip(columns, row))
        media_list.append(media_dict)

    conn.close()
    return media_list


def get_all_media(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Récupère tous les médias de la base de données.

    Args:
        limit: Nombre maximum de médias à retourner
        offset: Nombre de médias à sauter

    Returns:
        Liste de dictionnaires contenant les informations des médias
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT m.id, m.dive_id, m.type, m.filename, m.filepath, m.thumbnail_path,
               m.file_size_bytes, m.mime_type, m.width, m.height, m.duration_seconds,
               m.upload_date, m.description, m.tags, d.date as dive_date, s.nom as site_nom
        FROM dive_media m
        JOIN dives d ON m.dive_id = d.id
        JOIN sites s ON d.site_id = s.id
        ORDER BY m.upload_date DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    columns = [desc[0] for desc in cursor.description]
    media_list = []

    for row in cursor.fetchall():
        media_dict = dict(zip(columns, row))
        media_list.append(media_dict)

    conn.close()
    return media_list


def delete_media(media_id: int) -> bool:
    """
    Supprime un média de la base de données et du système de fichiers.

    Args:
        media_id: ID du média à supprimer

    Returns:
        True si la suppression a réussi
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Récupérer les chemins des fichiers
        cursor.execute("""
            SELECT filepath, thumbnail_path
            FROM dive_media
            WHERE id = ?
        """, (media_id,))

        result = cursor.fetchone()
        if not result:
            logger.warning(f"Média {media_id} introuvable")
            return False

        filepath, thumbnail_path = result

        # Supprimer les fichiers
        if filepath and Path(filepath).exists():
            Path(filepath).unlink()
            logger.debug(f"Fichier supprimé : {filepath}")

        if thumbnail_path and Path(thumbnail_path).exists():
            Path(thumbnail_path).unlink()
            logger.debug(f"Miniature supprimée : {thumbnail_path}")

        # Supprimer de la base de données
        cursor.execute("DELETE FROM dive_media WHERE id = ?", (media_id,))
        conn.commit()
        conn.close()

        logger.info(f"Média {media_id} supprimé avec succès")
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Erreur lors de la suppression du média : {e}")
        return False


def get_media_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur les médias.

    Returns:
        Dictionnaire avec les statistiques
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_media,
            SUM(CASE WHEN type = 'photo' THEN 1 ELSE 0 END) as total_photos,
            SUM(CASE WHEN type = 'video' THEN 1 ELSE 0 END) as total_videos,
            SUM(file_size_bytes) as total_size_bytes,
            COUNT(DISTINCT dive_id) as dives_with_media
        FROM dive_media
    """)

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'total_media': result[0] or 0,
            'total_photos': result[1] or 0,
            'total_videos': result[2] or 0,
            'total_size_mb': round((result[3] or 0) / (1024 * 1024), 2),
            'dives_with_media': result[4] or 0
        }

    return {
        'total_media': 0,
        'total_photos': 0,
        'total_videos': 0,
        'total_size_mb': 0,
        'dives_with_media': 0
    }
