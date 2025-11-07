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


def add_or_get_species(
    scientific_name: str,
    common_name_fr: str = '',
    common_name_en: str = '',
    category: str = 'autre'
) -> Optional[int]:
    """
    Ajoute une espèce au catalogue ou récupère son ID si elle existe déjà.

    Cette fonction est pratique pour l'analyse d'images : elle évite les doublons
    en vérifiant d'abord si l'espèce existe déjà dans la base.

    Args:
        scientific_name: Nom scientifique (obligatoire)
        common_name_fr: Nom commun en français
        common_name_en: Nom commun en anglais
        category: Catégorie de l'espèce

    Returns:
        ID de l'espèce (existante ou nouvellement créée), ou None si erreur
    """
    # Vérifier si l'espèce existe déjà par nom scientifique
    existing_species = get_species_by_name(scientific_name)

    if existing_species:
        logger.debug(f"Espèce existante trouvée : {scientific_name} (ID={existing_species['id']})")
        return existing_species['id']

    # L'espèce n'existe pas, la créer
    logger.info(f"Nouvelle espèce détectée : {scientific_name}")
    species_id = add_species(
        scientific_name=scientific_name,
        common_name_fr=common_name_fr,
        common_name_en=common_name_en,
        category=category,
        description="Espèce détectée automatiquement par IA"
    )

    return species_id


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


def get_media_species(media_id: int) -> List[Dict[str, Any]]:
    """
    Récupère toutes les espèces associées à un média spécifique.

    Args:
        media_id: ID du média

    Returns:
        Liste d'espèces identifiées sur ce média
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ds.id, ds.species_id, ds.confidence_score,
               ds.quantity, ds.notes, ds.detected_by, ds.detection_date,
               s.scientific_name, s.common_name_fr, s.common_name_en,
               s.category, s.conservation_status
        FROM dive_species ds
        JOIN species s ON ds.species_id = s.id
        WHERE ds.media_id = ?
        ORDER BY ds.confidence_score DESC, ds.detection_date DESC
    """, (media_id,))

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
        import database

        # Vérifier si la clé API est disponible
        # Priorité 1 : Base de données (paramètres utilisateur)
        api_key = database.get_setting("anthropic_api_key", "")

        # Priorité 2 : Variable d'environnement
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            logger.warning("Clé API Claude non configurée - analyse IA désactivée. Configurez-la dans les Paramètres.")
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

        # Récupérer le modèle configuré (par défaut Haiku 4.5 pour rapidité et coût)
        model = database.get_setting("ai_model", "claude-3-5-haiku-20241022")

        logger.info(f"Analyse d'image avec modèle : {model}")

        # Appeler l'API
        try:
            message = client.messages.create(
                model=model,
                max_tokens=2048,  # Augmenté pour avoir plus de détails
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
        except anthropic.NotFoundError as e:
            logger.error(f"Modèle '{model}' introuvable. Utilisez 'claude-3-5-haiku-20241022' ou 'claude-3-5-sonnet-20241022'. Erreur : {e}")
            return []
        except anthropic.AuthenticationError as e:
            logger.error(f"Erreur d'authentification API. Vérifiez votre clé API dans les Paramètres. Erreur : {e}")
            return []
        except anthropic.RateLimitError as e:
            logger.error(f"Limite de débit API atteinte. Attendez quelques instants. Erreur : {e}")
            return []

        # Parser la réponse
        response_text = message.content[0].text
        logger.debug(f"Réponse brute de l'IA : {response_text[:200]}...")

        # Extraire le JSON de la réponse
        # La réponse peut contenir du texte avant/après le JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                response_data = json.loads(json_match.group())
                detected_species = response_data.get('species', [])

                logger.info(f"Détection IA : {len(detected_species)} espèce(s) trouvée(s)")
                return detected_species
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de parsing JSON : {e}")
                logger.debug(f"JSON invalide : {json_match.group()[:500]}")
                return []
        else:
            logger.warning("Impossible de trouver du JSON dans la réponse de l'IA")
            logger.debug(f"Réponse complète : {response_text}")
            return []

    except ImportError:
        logger.warning("Module 'anthropic' non installé - analyse IA désactivée")
        return []
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'analyse IA : {type(e).__name__}: {e}")
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


def generate_image_description(image_path: Path) -> Optional[str]:
    """
    Génère une description détaillée d'une image de plongée avec l'IA.

    Cette fonction utilise Claude Vision API pour créer une description narrative
    de la photo de plongée, incluant l'ambiance, les éléments visuels et le contexte.

    Args:
        image_path: Chemin vers l'image à décrire

    Returns:
        Description générée par l'IA, ou None si erreur
    """
    try:
        import anthropic
        import os
        import database

        # Vérifier si la clé API est disponible
        api_key = database.get_setting("anthropic_api_key", "")
        if not api_key:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            logger.warning("Clé API Claude non configurée - génération de description désactivée")
            return None

        # Lire et encoder l'image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Déterminer le type MIME
        import mimetypes
        mime_type = mimetypes.guess_type(str(image_path))[0] or 'image/jpeg'

        # Créer le client Anthropic
        client = anthropic.Anthropic(api_key=api_key)

        # Prompt pour la description
        prompt = """Décris cette photo de plongée sous-marine de manière détaillée et évocatrice.

Inclus dans ta description :
- L'ambiance générale et les couleurs dominantes
- Les éléments marins visibles (espèces, formations, etc.)
- La qualité de l'eau (visibilité, lumière)
- Tout détail intéressant ou remarquable
- Le contexte de la prise de vue si identifiable

Écris une description narrative et captivante en français, d'environ 3-4 phrases.
Réponds UNIQUEMENT avec la description, sans préambule ni formatage spécial."""

        # Récupérer le modèle configuré
        model = database.get_setting("ai_model", "claude-3-5-haiku-20241022")

        logger.info(f"Génération de description avec modèle : {model}")

        # Appeler l'API
        try:
            message = client.messages.create(
                model=model,
                max_tokens=500,
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

            description = message.content[0].text.strip()
            logger.info(f"Description générée avec succès ({len(description)} caractères)")
            return description

        except anthropic.NotFoundError as e:
            logger.error(f"Modèle '{model}' introuvable : {e}")
            return None
        except anthropic.AuthenticationError as e:
            logger.error(f"Erreur d'authentification API : {e}")
            return None
        except anthropic.RateLimitError as e:
            logger.error(f"Limite de débit API atteinte : {e}")
            return None

    except ImportError:
        logger.warning("Module 'anthropic' non installé")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la génération de description : {type(e).__name__}: {e}")
        return None


def get_species_by_id(species_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère une espèce par son ID.

    Args:
        species_id: ID de l'espèce

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
        WHERE id = ?
    """, (species_id,))

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


def get_all_species(limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Récupère toutes les espèces du catalogue avec pagination.

    Args:
        limit: Nombre maximum d'espèces à retourner
        offset: Nombre d'espèces à sauter
        category: Filtrer par catégorie (optionnel)

    Returns:
        Liste d'espèces
    """
    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("""
            SELECT id, scientific_name, common_name_fr, common_name_en, category,
                   description, conservation_status, habitat, depth_range,
                   image_url, created_date
            FROM species
            WHERE category = ?
            ORDER BY scientific_name
            LIMIT ? OFFSET ?
        """, (category, limit, offset))
    else:
        cursor.execute("""
            SELECT id, scientific_name, common_name_fr, common_name_en, category,
                   description, conservation_status, habitat, depth_range,
                   image_url, created_date
            FROM species
            ORDER BY scientific_name
            LIMIT ? OFFSET ?
        """, (limit, offset))

    columns = [desc[0] for desc in cursor.description]
    species_list = []

    for row in cursor.fetchall():
        species_dict = dict(zip(columns, row))
        species_list.append(species_dict)

    conn.close()
    return species_list


def update_species(
    species_id: int,
    scientific_name: str = None,
    common_name_fr: str = None,
    common_name_en: str = None,
    category: str = None,
    description: str = None,
    conservation_status: str = None,
    habitat: str = None,
    depth_range: str = None,
    image_url: str = None
) -> bool:
    """
    Met à jour les informations d'une espèce.

    Args:
        species_id: ID de l'espèce à mettre à jour
        Autres paramètres: Nouvelles valeurs (si None, la valeur actuelle est conservée)

    Returns:
        True si la mise à jour a réussi
    """
    # Récupérer les valeurs actuelles
    current = get_species_by_id(species_id)
    if not current:
        logger.warning(f"Espèce {species_id} introuvable")
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE species
            SET scientific_name = ?,
                common_name_fr = ?,
                common_name_en = ?,
                category = ?,
                description = ?,
                conservation_status = ?,
                habitat = ?,
                depth_range = ?,
                image_url = ?
            WHERE id = ?
        """, (
            scientific_name if scientific_name is not None else current['scientific_name'],
            common_name_fr if common_name_fr is not None else current['common_name_fr'],
            common_name_en if common_name_en is not None else current['common_name_en'],
            category if category is not None else current['category'],
            description if description is not None else current['description'],
            conservation_status if conservation_status is not None else current['conservation_status'],
            habitat if habitat is not None else current['habitat'],
            depth_range if depth_range is not None else current['depth_range'],
            image_url if image_url is not None else current['image_url'],
            species_id
        ))

        conn.commit()
        conn.close()

        logger.info(f"Espèce {species_id} mise à jour : {scientific_name or current['scientific_name']}")
        return True

    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        logger.error(f"Erreur d'intégrité lors de la mise à jour : {e}")
        return False
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Erreur lors de la mise à jour de l'espèce : {e}")
        return False


def delete_species(species_id: int) -> bool:
    """
    Supprime une espèce du catalogue.

    Note: Cette opération supprimera également toutes les associations
    avec les plongées (CASCADE).

    Args:
        species_id: ID de l'espèce à supprimer

    Returns:
        True si la suppression a réussi
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Vérifier si l'espèce existe
        cursor.execute("SELECT scientific_name FROM species WHERE id = ?", (species_id,))
        result = cursor.fetchone()

        if not result:
            logger.warning(f"Espèce {species_id} introuvable")
            conn.close()
            return False

        scientific_name = result[0]

        # Supprimer l'espèce (les associations seront supprimées automatiquement via CASCADE)
        cursor.execute("DELETE FROM species WHERE id = ?", (species_id,))
        conn.commit()
        conn.close()

        logger.info(f"Espèce supprimée : {scientific_name} (ID={species_id})")
        return True

    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Erreur lors de la suppression de l'espèce : {e}")
        return False


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
