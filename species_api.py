"""
Module d'intégration avec les API publiques pour la validation des espèces marines.

Utilise principalement WoRMS (World Register of Marine Species) pour :
- Valider les noms scientifiques
- Récupérer des informations taxonomiques
- Obtenir des données de conservation
- Comparer avec les détections IA
"""

import requests
from typing import Optional, Dict, List, Any
from logger import get_logger
import time

logger = get_logger(__name__)

# API WoRMS (World Register of Marine Species)
WORMS_BASE_URL = "https://www.marinespecies.org/rest"
WORMS_TIMEOUT = 10  # secondes

# Cache pour éviter les requêtes répétées
_species_cache: Dict[str, Dict[str, Any]] = {}


def search_worms_species(scientific_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Recherche une espèce dans WoRMS par nom scientifique.

    Args:
        scientific_name: Nom scientifique de l'espèce (ex: "Amphiprion ocellaris")
        use_cache: Utiliser le cache pour éviter les requêtes répétées

    Returns:
        Dictionnaire avec les informations de l'espèce, ou None si non trouvée

    Exemple de retour:
    {
        'aphia_id': 275717,
        'scientific_name': 'Amphiprion ocellaris',
        'authority': 'Cuvier, 1830',
        'status': 'accepted',
        'rank': 'Species',
        'valid_name': 'Amphiprion ocellaris',
        'kingdom': 'Animalia',
        'phylum': 'Chordata',
        'class': 'Actinopteri',
        'order': 'Perciformes',
        'family': 'Pomacentridae',
        'genus': 'Amphiprion',
        'isMarine': True,
        'isBrackish': False,
        'isFreshwater': False,
        'isTerrestrial': False,
        'isExtinct': False,
        'match_type': 'exact',
        'common_names': ['clown anemonefish', 'poisson-clown à trois bandes']
    }
    """
    if not scientific_name or not scientific_name.strip():
        logger.warning("Nom scientifique vide fourni")
        return None

    scientific_name = scientific_name.strip()

    # Vérifier le cache
    if use_cache and scientific_name in _species_cache:
        logger.debug(f"Espèce trouvée dans le cache : {scientific_name}")
        return _species_cache[scientific_name]

    try:
        logger.info(f"Recherche WoRMS pour : {scientific_name}")

        # Endpoint pour recherche par nom
        url = f"{WORMS_BASE_URL}/AphiaRecordsByName/{scientific_name}"
        params = {
            'like': 'false',  # Correspondance exacte
            'marine_only': 'true'  # Uniquement espèces marines
        }

        response = requests.get(url, params=params, timeout=WORMS_TIMEOUT)
        response.raise_for_status()

        results = response.json()

        if not results or len(results) == 0:
            logger.info(f"Aucun résultat WoRMS pour : {scientific_name}")
            return None

        # Prendre le premier résultat (correspondance exacte)
        species_data = results[0]

        # Enrichir avec les noms communs
        aphia_id = species_data.get('AphiaID')
        if aphia_id:
            common_names = get_worms_common_names(aphia_id)
            species_data['common_names'] = common_names
        else:
            species_data['common_names'] = []

        # Formater les données
        formatted_data = {
            'aphia_id': species_data.get('AphiaID'),
            'scientific_name': species_data.get('scientificname'),
            'authority': species_data.get('authority'),
            'status': species_data.get('status'),  # accepted, unaccepted, etc.
            'rank': species_data.get('rank'),  # Species, Genus, etc.
            'valid_name': species_data.get('valid_name'),  # Si synonyme, le nom valide
            'kingdom': species_data.get('kingdom'),
            'phylum': species_data.get('phylum'),
            'class': species_data.get('class'),
            'order': species_data.get('order'),
            'family': species_data.get('family'),
            'genus': species_data.get('genus'),
            'isMarine': species_data.get('isMarine', False),
            'isBrackish': species_data.get('isBrackish', False),
            'isFreshwater': species_data.get('isFreshwater', False),
            'isTerrestrial': species_data.get('isTerrestrial', False),
            'isExtinct': species_data.get('isExtinct', False),
            'match_type': species_data.get('match_type', 'exact'),
            'common_names': species_data.get('common_names', []),
            'url': species_data.get('url', f"https://www.marinespecies.org/aphia.php?p=taxdetails&id={aphia_id}")
        }

        # Mettre en cache
        _species_cache[scientific_name] = formatted_data

        logger.info(f"Espèce trouvée dans WoRMS : {formatted_data['scientific_name']} "
                   f"(AphiaID: {formatted_data['aphia_id']})")

        return formatted_data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout lors de la recherche WoRMS pour {scientific_name}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau lors de la recherche WoRMS : {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la recherche WoRMS : {e}")
        return None


def get_worms_common_names(aphia_id: int) -> List[str]:
    """
    Récupère les noms communs d'une espèce depuis WoRMS.

    Args:
        aphia_id: Identifiant AphiaID de l'espèce

    Returns:
        Liste des noms communs
    """
    try:
        url = f"{WORMS_BASE_URL}/AphiaVernacularsByAphiaID/{aphia_id}"
        response = requests.get(url, timeout=WORMS_TIMEOUT)
        response.raise_for_status()

        vernaculars = response.json()

        if not vernaculars:
            return []

        # Extraire les noms (priorité aux noms français et anglais)
        names = []
        for vernacular in vernaculars:
            name = vernacular.get('vernacular')
            language = vernacular.get('language_code', '').lower()

            # Priorité : français, puis anglais, puis autres
            if language == 'fra' and name:
                names.insert(0, name)
            elif language == 'eng' and name:
                names.append(name)
            elif name:
                names.append(name)

        # Dédupliquer tout en gardant l'ordre
        seen = set()
        unique_names = []
        for name in names:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique_names.append(name)

        return unique_names[:5]  # Limiter à 5 noms

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des noms communs : {e}")
        return []


def fuzzy_search_worms(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Recherche floue dans WoRMS (pour suggestions/autocomplétion).

    Args:
        query: Terme de recherche (nom scientifique ou commun)
        limit: Nombre maximum de résultats

    Returns:
        Liste de dictionnaires avec les résultats
    """
    if not query or len(query) < 3:
        return []

    try:
        url = f"{WORMS_BASE_URL}/AphiaRecordsByName/{query}"
        params = {
            'like': 'true',  # Recherche floue
            'marine_only': 'true',
            'offset': 1
        }

        response = requests.get(url, params=params, timeout=WORMS_TIMEOUT)
        response.raise_for_status()

        results = response.json()

        if not results:
            return []

        # Formater et limiter les résultats
        formatted_results = []
        for item in results[:limit]:
            formatted_results.append({
                'aphia_id': item.get('AphiaID'),
                'scientific_name': item.get('scientificname'),
                'authority': item.get('authority'),
                'status': item.get('status'),
                'rank': item.get('rank'),
                'family': item.get('family'),
            })

        return formatted_results

    except Exception as e:
        logger.error(f"Erreur lors de la recherche floue WoRMS : {e}")
        return []


def validate_species_name(scientific_name: str) -> Dict[str, Any]:
    """
    Valide un nom d'espèce et retourne des informations de validation.

    Args:
        scientific_name: Nom scientifique à valider

    Returns:
        Dictionnaire avec les informations de validation:
        {
            'is_valid': bool,
            'is_marine': bool,
            'status': str,  # 'accepted', 'synonym', 'invalid', 'not_found'
            'correct_name': str,  # Si synonyme, le nom accepté
            'aphia_id': int,
            'confidence': str,  # 'high', 'medium', 'low'
            'details': dict
        }
    """
    worms_data = search_worms_species(scientific_name)

    if not worms_data:
        return {
            'is_valid': False,
            'is_marine': False,
            'status': 'not_found',
            'correct_name': None,
            'aphia_id': None,
            'confidence': 'low',
            'details': {}
        }

    is_accepted = worms_data['status'] == 'accepted'
    correct_name = worms_data['valid_name'] if worms_data['valid_name'] else worms_data['scientific_name']

    # Déterminer la confiance
    confidence = 'high'
    if worms_data['status'] == 'unaccepted':
        confidence = 'medium'
    elif worms_data['status'] not in ['accepted', 'unaccepted']:
        confidence = 'low'

    return {
        'is_valid': True,
        'is_marine': worms_data.get('isMarine', False),
        'status': 'accepted' if is_accepted else 'synonym',
        'correct_name': correct_name,
        'aphia_id': worms_data['aphia_id'],
        'confidence': confidence,
        'details': worms_data
    }


def compare_with_ai_detection(ai_species_name: str, confidence_score: float = 0.0) -> Dict[str, Any]:
    """
    Compare une détection IA avec la base de données WoRMS.

    Args:
        ai_species_name: Nom scientifique détecté par l'IA
        confidence_score: Score de confiance de l'IA (0-1)

    Returns:
        Dictionnaire avec la comparaison et recommandations:
        {
            'ai_name': str,
            'ai_confidence': float,
            'worms_found': bool,
            'worms_status': str,
            'recommended_name': str,
            'match_quality': str,  # 'perfect', 'synonym', 'uncertain', 'not_found'
            'should_verify': bool,
            'details': dict
        }
    """
    validation = validate_species_name(ai_species_name)

    # Déterminer la qualité de correspondance
    match_quality = 'not_found'
    recommended_name = ai_species_name
    should_verify = True

    if validation['is_valid']:
        if validation['status'] == 'accepted':
            match_quality = 'perfect'
            should_verify = confidence_score < 0.7  # Vérifier si confiance IA < 70%
        elif validation['status'] == 'synonym':
            match_quality = 'synonym'
            recommended_name = validation['correct_name']
            should_verify = True
        else:
            match_quality = 'uncertain'
    else:
        match_quality = 'not_found'
        should_verify = True

    return {
        'ai_name': ai_species_name,
        'ai_confidence': confidence_score,
        'worms_found': validation['is_valid'],
        'worms_status': validation['status'],
        'recommended_name': recommended_name,
        'match_quality': match_quality,
        'should_verify': should_verify,
        'details': validation
    }


def get_species_info_summary(scientific_name: str) -> Optional[str]:
    """
    Génère un résumé textuel des informations d'une espèce.

    Args:
        scientific_name: Nom scientifique de l'espèce

    Returns:
        Résumé formaté en texte, ou None si non trouvé
    """
    worms_data = search_worms_species(scientific_name)

    if not worms_data:
        return None

    summary_parts = []

    # Nom et autorité
    if worms_data['authority']:
        summary_parts.append(f"**{worms_data['scientific_name']}** {worms_data['authority']}")
    else:
        summary_parts.append(f"**{worms_data['scientific_name']}**")

    # Statut
    status_emoji = "✅" if worms_data['status'] == 'accepted' else "⚠️"
    summary_parts.append(f"{status_emoji} Statut: {worms_data['status']}")

    # Taxonomie
    taxonomy = []
    if worms_data['family']:
        taxonomy.append(f"Famille: {worms_data['family']}")
    if worms_data['order']:
        taxonomy.append(f"Ordre: {worms_data['order']}")
    if worms_data['class']:
        taxonomy.append(f"Classe: {worms_data['class']}")

    if taxonomy:
        summary_parts.append(" | ".join(taxonomy))

    # Noms communs
    if worms_data['common_names']:
        names_str = ", ".join(worms_data['common_names'])
        summary_parts.append(f"Noms communs: {names_str}")

    # Habitat
    habitat_tags = []
    if worms_data.get('isMarine'):
        habitat_tags.append("🌊 Marin")
    if worms_data.get('isBrackish'):
        habitat_tags.append("💧 Saumâtre")
    if worms_data.get('isFreshwater'):
        habitat_tags.append("🏞️ Eau douce")

    if habitat_tags:
        summary_parts.append(" ".join(habitat_tags))

    return "\n\n".join(summary_parts)
