"""
Module de reconnaissance d'espèces marines par IA.

Fonctionnalités :
- Analyse d'images pour identifier poissons, coraux et autres organismes marins
- Intégration avec Claude Vision API (ou autre API d'IA)
- Stockage des résultats avec score de confiance
- Ajout manuel d'espèces
- Gestion du catalogue d'espèces
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import base64
import json
from logger import get_logger
from database import get_connection

logger = get_logger(__name__)


def add_species(
    scientific_name: str,
    common_name_fr: str = '',
    common_name_en: str = '',
    category: str = 'autre',
    description: str = '',
    conservation_status: str = '',
    habitat: str = '',
    depth_range: str = '',
    image_url: str = ''
) -> Optional[int]:
    """
    Ajoute une nouvelle espèce au catalogue.

    Args:
        scientific_name: Nom scientifique (obligatoire et unique)
        common_name_fr: Nom commun en français
        common_name_en: Nom commun en anglais
        category: Catégorie (poisson, corail, mollusque, etc.)
        description: Description de l'espèce
        conservation_status: Statut de conservation (LC, NT, VU, EN, CR)
        habitat: Type d'habitat
        depth_range: Plage de profondeur
        image_url: URL d'une image de référence

    Returns:
        ID de l'espèce créée, ou None si erreur
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO species
            (scientific_name, common_name_fr, common_name_en, category,
             description, conservation_status, habitat, depth_range,
             image_url, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scientific_name, common_name_fr, common_name_en, category,
            description, conservation_status, habitat, depth_range,
            image_url, datetime.now().isoformat()
        ))

        conn.commit()
        species_id = cursor.lastrowid
        logger.info(f"Espèce ajoutée : {scientific_name} (ID={species_id})")
        return species_id

    except sqlite3.IntegrityError:
        logger.warning(f"L'espèce {scientific_name} existe déjà")
        return None
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de l'ajout de l'espèce : {e}")
        return None
    finally:
        conn.close()


def get_species_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Recherche une espèce par son nom (scientifique ou commun).

    Args:
        name: Nom à rechercher (scientifique ou commun)

    Returns:
        Dictionnaire avec les informations de l'espèce, ou None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, scientific_name, common_name_fr, common_name_en, category,
               description, conservation_status, habitat, depth_range,
               image_url, created_date
        FROM species
        WHERE scientific_name = ?
           OR common_name_fr = ?
           OR common_name_en = ?
        LIMIT 1
    """, (name, name, name))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'scientific_name': result[1],
            'common_name_fr': result[2],
            'common_name_en': result[3],
            'category': result[4],
            'description': result[5],
            'conservation_status': result[6],
            'habitat': result[7],
            'depth_range': result[8],
            'image_url': result[9],
            'created_date': result[10]
        }

    return None


def search_species(query: str, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Recherche des espèces par mot-clé.

    Args:
        query: Terme de recherche
        category: Filtrer par catégorie (optionnel)
        limit: Nombre maximum de résultats

    Returns:
        Liste d'espèces correspondantes
    """
    conn = get_connection()
    cursor = conn.cursor()

    query_pattern = f"%{query}%"

    if category:
        cursor.execute("""
            SELECT id, scientific_name, common_name_fr, common_name_en, category,
                   description, conservation_status, habitat, depth_range
            FROM species
            WHERE category = ?
              AND (scientific_name LIKE ? OR common_name_fr LIKE ? OR common_name_en LIKE ?)
            ORDER BY scientific_name
            LIMIT ?
        """, (category, query_pattern, query_pattern, query_pattern, limit))
    else:
        cursor.execute("""
            SELECT id, scientific_name, common_name_fr, common_name_en, category,
                   description, conservation_status, habitat, depth_range
            FROM species
            WHERE scientific_name LIKE ? OR common_name_fr LIKE ? OR common_name_en LIKE ?
            ORDER BY scientific_name
            LIMIT ?
        """, (query_pattern, query_pattern, query_pattern, limit))

    columns = [desc[0] for desc in cursor.description]
    species_list = []

    for row in cursor.fetchall():
        species_dict = dict(zip(columns, row))
        species_list.append(species_dict)

    conn.close()
    return species_list


def add_species_to_dive(
    dive_id: int,
    species_id: int,
    media_id: Optional[int] = None,
    confidence_score: Optional[float] = None,
    quantity: int = 1,
    notes: str = '',
    detected_by: str = 'manual'
) -> Optional[int]:
    """
    Associe une espèce à une plongée.

    Args:
        dive_id: ID de la plongée
        species_id: ID de l'espèce
        media_id: ID du média (photo/vidéo) où l'espèce a été détectée
        confidence_score: Score de confiance de la détection IA (0-1)
        quantity: Nombre d'individus observés
        notes: Notes additionnelles
        detected_by: Source de la détection ('ai', 'manual', 'verified')

    Returns:
        ID de l'association créée, ou None si erreur
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO dive_species
            (dive_id, species_id, media_id, confidence_score, quantity,
             notes, detected_by, detection_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dive_id, species_id, media_id, confidence_score, quantity,
            notes, detected_by, datetime.now().isoformat()
        ))

        conn.commit()
        association_id = cursor.lastrowid
        logger.info(f"Espèce associée à la plongée : dive_id={dive_id}, species_id={species_id}")
        return association_id

    except sqlite3.IntegrityError:
        logger.warning(f"Association déjà existante : dive_id={dive_id}, species_id={species_id}")
        return None
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de l'association de l'espèce : {e}")
        return None
    finally:
        conn.close()


def get_dive_species(dive_id: int) -> List[Dict[str, Any]]:
    """
    Récupère toutes les espèces associées à une plongée.

    Args:
        dive_id: ID de la plongée

    Returns:
        Liste d'espèces avec leurs détails
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ds.id, ds.species_id, ds.media_id, ds.confidence_score,
               ds.quantity, ds.notes, ds.detected_by, ds.detection_date,
               s.scientific_name, s.common_name_fr, s.common_name_en,
               s.category, s.conservation_status
        FROM dive_species ds
        JOIN species s ON ds.species_id = s.id
        WHERE ds.dive_id = ?
        ORDER BY ds.detection_date DESC
    """, (dive_id,))

    columns = [desc[0] for desc in cursor.description]
    species_list = []

    for row in cursor.fetchall():
        species_dict = dict(zip(columns, row))
        species_list.append(species_dict)

    conn.close()
    return species_list


def analyze_image_with_ai(image_path: Path) -> List[Dict[str, Any]]:
    """
    Analyse une image pour détecter des espèces marines avec l'IA.

    Cette fonction utilise Claude Vision API pour identifier les espèces.
    Note : Nécessite une clé API Anthropic configurée dans les variables d'environnement.

    Args:
        image_path: Chemin vers l'image à analyser

    Returns:
        Liste de détections avec nom d'espèce et score de confiance
    """
    try:
        # Importer anthropic seulement si nécessaire
        import anthropic
        import os

        # Vérifier si la clé API est disponible
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY non configurée - analyse IA désactivée")
            return []

        # Lire et encoder l'image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Déterminer le type MIME
        import mimetypes
        mime_type = mimetypes.guess_type(str(image_path))[0] or 'image/jpeg'

        # Créer le client Anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Construire le prompt
        prompt = """Analyse cette image de plongée sous-marine et identifie toutes les espèces marines visibles.

Pour chaque espèce détectée, fournis :
1. Le nom scientifique
2. Le nom commun en français
3. Le nom commun en anglais
4. La catégorie (poisson, corail, mollusque, crustacé, échinoderme, mammifère, reptile, autre)
5. Un score de confiance entre 0 et 1

Réponds UNIQUEMENT avec un JSON valide au format suivant :
{
  "species": [
    {
      "scientific_name": "Nom scientifique",
      "common_name_fr": "Nom français",
      "common_name_en": "Nom anglais",
      "category": "poisson",
      "confidence": 0.95
    }
  ]
}

Si aucune espèce n'est détectable, retourne : {"species": []}
"""

        # Appeler l'API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Parser la réponse
        response_text = message.content[0].text

        # Extraire le JSON de la réponse
        # La réponse peut contenir du texte avant/après le JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_data = json.loads(json_match.group())
            detected_species = response_data.get('species', [])

            logger.info(f"Détection IA : {len(detected_species)} espèce(s) trouvée(s)")
            return detected_species
        else:
            logger.warning("Impossible de parser la réponse JSON de l'IA")
            return []

    except ImportError:
        logger.warning("Module 'anthropic' non installé - analyse IA désactivée")
        return []
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse IA : {e}")
        return []


def process_image_and_add_species(
    image_path: Path,
    dive_id: int,
    media_id: Optional[int] = None,
    auto_add: bool = False,
    confidence_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Analyse une image avec l'IA et ajoute les espèces détectées à la plongée.

    Args:
        image_path: Chemin de l'image
        dive_id: ID de la plongée
        media_id: ID du média associé
        auto_add: Si True, ajoute automatiquement les espèces avec confiance >= threshold
        confidence_threshold: Seuil de confiance pour l'ajout automatique

    Returns:
        Liste des espèces détectées avec leurs IDs d'association
    """
    detections = analyze_image_with_ai(image_path)
    results = []

    for detection in detections:
        scientific_name = detection.get('scientific_name', '')
        common_name_fr = detection.get('common_name_fr', '')
        common_name_en = detection.get('common_name_en', '')
        category = detection.get('category', 'autre')
        confidence = detection.get('confidence', 0.0)

        # Vérifier si l'espèce existe déjà
        species = get_species_by_name(scientific_name)

        if not species:
            # Ajouter l'espèce au catalogue
            species_id = add_species(
                scientific_name=scientific_name,
                common_name_fr=common_name_fr,
                common_name_en=common_name_en,
                category=category,
                description=f"Espèce détectée automatiquement par IA"
            )
        else:
            species_id = species['id']

        result = {
            'species_id': species_id,
            'scientific_name': scientific_name,
            'common_name_fr': common_name_fr,
            'confidence': confidence,
            'added': False,
            'association_id': None
        }

        # Ajouter à la plongée si auto_add est activé et confiance suffisante
        if auto_add and confidence >= confidence_threshold and species_id:
            association_id = add_species_to_dive(
                dive_id=dive_id,
                species_id=species_id,
                media_id=media_id,
                confidence_score=confidence,
                detected_by='ai'
            )
            if association_id:
                result['added'] = True
                result['association_id'] = association_id

        results.append(result)

    return results


def get_species_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur les espèces.

    Returns:
        Dictionnaire avec les statistiques
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total d'espèces par catégorie
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM species
        GROUP BY category
        ORDER BY count DESC
    """)
    category_stats = dict(cursor.fetchall())

    # Espèces les plus observées
    cursor.execute("""
        SELECT s.scientific_name, s.common_name_fr, COUNT(ds.id) as observation_count
        FROM species s
        LEFT JOIN dive_species ds ON s.id = ds.species_id
        GROUP BY s.id
        ORDER BY observation_count DESC
        LIMIT 10
    """)
    top_species = []
    for row in cursor.fetchall():
        top_species.append({
            'scientific_name': row[0],
            'common_name_fr': row[1],
            'observation_count': row[2]
        })

    # Total d'espèces dans le catalogue
    cursor.execute("SELECT COUNT(*) FROM species")
    total_species = cursor.fetchone()[0]

    # Total d'observations
    cursor.execute("SELECT COUNT(*) FROM dive_species")
    total_observations = cursor.fetchone()[0]

    # Détections par type
    cursor.execute("""
        SELECT detected_by, COUNT(*) as count
        FROM dive_species
        GROUP BY detected_by
    """)
    detection_stats = dict(cursor.fetchall())

    conn.close()

    return {
        'total_species': total_species,
        'total_observations': total_observations,
        'category_stats': category_stats,
        'top_species': top_species,
        'detection_stats': detection_stats
    }
