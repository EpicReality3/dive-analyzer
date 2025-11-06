"""
Module de gestion de la base de données SQLite pour le journal de plongée.

Architecture : Métriques agrégées + références aux fichiers originaux
Tables : sites, buddies, tags, dives, dive_tags
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from config import config
from logger import get_logger

logger = get_logger(__name__)

DB_PATH = config.DB_PATH


def get_connection() -> sqlite3.Connection:
    """
    Crée et retourne une connexion à la base de données.
    Active les foreign keys (important pour l'intégrité).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        logger.debug(f"Connexion établie à la base de données : {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la connexion à la base de données : {e}")
        raise


def init_database() -> None:
    """
    Initialise la base de données avec toutes les tables nécessaires.

    À appeler UNE SEULE FOIS au premier lancement.
    Utilise IF NOT EXISTS pour éviter d'écraser des données existantes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1 : Sites de plongée
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            pays TEXT,
            coordonnees_gps TEXT
        )
    """)

    # Table 2 : Buddies (binômes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buddies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            niveau_certification TEXT
        )
    """)

    # Table 3 : Tags
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            categorie TEXT
        )
    """)

    # Table 4 : Plongées (table principale)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            site_id INTEGER NOT NULL,
            buddy_id INTEGER,
            dive_type TEXT CHECK(dive_type IN ('exploration', 'formation', 'technique')),
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            notes TEXT,

            -- Conditions environnementales
            houle TEXT CHECK(houle IN ('aucune', 'faible', 'moyenne', 'forte')),
            visibilite_metres INTEGER,
            courant TEXT CHECK(courant IN ('aucun', 'faible', 'moyen', 'fort')),

            -- Données techniques du fichier
            profondeur_max REAL,
            duree_minutes REAL,
            temperature_min REAL,
            sac REAL,
            temps_fond_minutes REAL,
            vitesse_remontee_max REAL,

            -- Référence au fichier original
            fichier_original_nom TEXT,
            fichier_original_path TEXT,

            -- Clés étrangères
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (buddy_id) REFERENCES buddies(id)
        )
    """)

    # Table 5 : Liaison plongées-tags (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dive_tags (
            dive_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (dive_id, tag_id),
            FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

    # Table 6 : Cache des données parsées (Phase 2 - Performance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cached_dive_data (
            dive_id INTEGER PRIMARY KEY,
            cached_dataframe BLOB NOT NULL,
            cache_timestamp TEXT NOT NULL,
            file_hash TEXT,
            FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE
        )
    """)

    # ===== INDEX POUR AMÉLIORER LES PERFORMANCES (Phase 2) =====

    # Index sur dives.date pour accélérer les tris et filtres par date
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dives_date
        ON dives(date DESC)
    """)

    # Index sur dives.site_id pour accélérer les JOINs avec sites
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dives_site_id
        ON dives(site_id)
    """)

    # Index sur dives.rating pour accélérer les filtres par note
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dives_rating
        ON dives(rating DESC)
    """)

    # Index composite sur date + site_id pour les requêtes combinées
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_dives_date_site
        ON dives(date DESC, site_id)
    """)

    conn.commit()
    conn.close()
    logger.info("✅ Base de données initialisée avec succès (tables + index + cache)")


def _insert_or_get_entity(
    cursor: sqlite3.Cursor,
    table: str,
    name: str,
    extra_field: Optional[str] = None,
    extra_value: Optional[Any] = None
) -> int:
    """
    Fonction générique pour insérer ou récupérer une entité par nom.

    Cette fonction élimine la duplication de code entre insert_site,
    insert_buddy et insert_tag.

    Args:
        cursor: Curseur de base de données
        table: Nom de la table (sites, buddies, tags)
        name: Nom de l'entité à insérer/récupérer
        extra_field: Nom du champ supplémentaire optionnel (pays, niveau_certification, categorie)
        extra_value: Valeur du champ supplémentaire

    Returns:
        ID de l'entité (existante ou nouvellement créée)
    """
    # Vérifier si l'entité existe déjà
    cursor.execute(f"SELECT id FROM {table} WHERE nom = ?", (name,))
    result = cursor.fetchone()

    if result:
        entity_id = result[0]
        logger.debug(f"{table} existant trouvé : '{name}' (ID: {entity_id})")
        return entity_id

    # Insérer nouvelle entité
    if extra_field and extra_value is not None:
        cursor.execute(
            f"INSERT INTO {table} (nom, {extra_field}) VALUES (?, ?)",
            (name, extra_value)
        )
    else:
        cursor.execute(
            f"INSERT INTO {table} (nom) VALUES (?)",
            (name,)
        )

    entity_id = cursor.lastrowid
    logger.info(f"Nouvelle entrée dans {table} : '{name}' (ID: {entity_id})")
    return entity_id


def insert_site(nom: str, pays: Optional[str] = None) -> int:
    """
    Insère un nouveau site de plongée ou retourne l'ID existant.

    Args:
        nom: Nom du site (ex: "Port-Cros")
        pays: Pays optionnel (ex: "France")

    Returns:
        ID du site (existant ou nouvellement créé)
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        site_id = _insert_or_get_entity(cursor, 'sites', nom, 'pays', pays)
        conn.commit()
        return site_id
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de l'insertion du site '{nom}' : {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_buddy(nom: str, niveau: Optional[str] = None) -> int:
    """
    Insère un nouveau buddy ou retourne l'ID existant.

    Args:
        nom: Nom du buddy
        niveau: Niveau de certification optionnel (ex: "Niveau 2 FFESSM")

    Returns:
        ID du buddy
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        buddy_id = _insert_or_get_entity(cursor, 'buddies', nom, 'niveau_certification', niveau)
        conn.commit()
        return buddy_id
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de l'insertion du buddy '{nom}' : {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_tag(nom: str, categorie: Optional[str] = None) -> int:
    """
    Insère un nouveau tag ou retourne l'ID existant.

    Args:
        nom: Nom du tag (ex: "Épave", "Nuit")
        categorie: Catégorie optionnelle (ex: "environnement", "faune")

    Returns:
        ID du tag
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        tag_id = _insert_or_get_entity(cursor, 'tags', nom, 'categorie', categorie)
        conn.commit()
        return tag_id
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de l'insertion du tag '{nom}' : {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def insert_dive(dive_data: Dict[str, Any]) -> int:
    """
    Insère une plongée complète dans la base de données.

    Args:
        dive_data: Dictionnaire contenant toutes les données de la plongée

    Structure attendue de dive_data :
    {
        'date': '2025-11-02 14:30:00',
        'site_nom': 'Port-Cros',
        'buddy_nom': 'Marie',
        'dive_type': 'exploration',
        'rating': 5,
        'notes': 'Magnifique plongée...',
        'houle': 'faible',
        'visibilite_metres': 15,
        'courant': 'aucun',
        'tags': ['Épave', 'Poissons'],  # Liste de tags

        # Données techniques
        'profondeur_max': 42.3,
        'duree_minutes': 40.0,
        'temperature_min': 16.2,
        'sac': 14.5,
        'temps_fond_minutes': 35.2,
        'vitesse_remontee_max': 8.5,
        'fichier_original_nom': 'dive_2025-11-02.fit',
        'fichier_original_path': '/home/user/dive-analyzer/uploads/dive_2025-11-02.fit'
    }

    Returns:
        ID de la plongée créée
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Insérer/récupérer site
        site_id = _insert_or_get_entity(cursor, 'sites', dive_data['site_nom'])

        # 2. Insérer/récupérer buddy (optionnel)
        buddy_id = None
        if dive_data.get('buddy_nom'):
            buddy_id = _insert_or_get_entity(cursor, 'buddies', dive_data['buddy_nom'])

        # 3. Insérer la plongée
        cursor.execute("""
            INSERT INTO dives (
                date, site_id, buddy_id, dive_type, rating, notes,
                houle, visibilite_metres, courant,
                profondeur_max, duree_minutes, temperature_min, sac,
                temps_fond_minutes, vitesse_remontee_max,
                fichier_original_nom, fichier_original_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dive_data['date'],
            site_id,
            buddy_id,
            dive_data.get('dive_type'),
            dive_data.get('rating'),
            dive_data.get('notes'),
            dive_data.get('houle'),
            dive_data.get('visibilite_metres'),
            dive_data.get('courant'),
            dive_data['profondeur_max'],
            dive_data['duree_minutes'],
            dive_data.get('temperature_min'),
            dive_data.get('sac'),
            dive_data.get('temps_fond_minutes'),
            dive_data.get('vitesse_remontee_max'),
            dive_data.get('fichier_original_nom'),
            dive_data.get('fichier_original_path')
        ))

        dive_id = cursor.lastrowid

        # 4. Insérer les tags (many-to-many)
        if dive_data.get('tags'):
            for tag_nom in dive_data['tags']:
                # Insérer ou récupérer le tag
                tag_id = _insert_or_get_entity(cursor, 'tags', tag_nom)

                # Lier tag à plongée
                cursor.execute(
                    "INSERT INTO dive_tags (dive_id, tag_id) VALUES (?, ?)",
                    (dive_id, tag_id)
                )

        conn.commit()
        logger.info(f"Plongée insérée avec succès (ID: {dive_id})")
        return dive_id

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion de la plongée : {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_dives() -> pd.DataFrame:
    """
    Récupère toutes les plongées avec JOIN pour avoir les noms.

    Returns:
        DataFrame pandas avec toutes les plongées
    """
    conn = get_connection()

    query = """
        SELECT
            dives.id,
            dives.date,
            sites.nom AS site,
            buddies.nom AS buddy,
            dives.dive_type,
            dives.rating,
            dives.profondeur_max,
            dives.duree_minutes,
            dives.sac,
            dives.temperature_min,
            dives.notes
        FROM dives
        LEFT JOIN sites ON dives.site_id = sites.id
        LEFT JOIN buddies ON dives.buddy_id = buddies.id
        ORDER BY dives.date DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def get_dive_by_id(dive_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère une plongée complète par son ID avec tous les détails.

    Args:
        dive_id: ID de la plongée

    Returns:
        Dictionnaire avec toutes les données ou None si non trouvée
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Requête principale avec JOINs
    cursor.execute("""
        SELECT
            dives.*,
            sites.nom AS site_nom,
            buddies.nom AS buddy_nom
        FROM dives
        LEFT JOIN sites ON dives.site_id = sites.id
        LEFT JOIN buddies ON dives.buddy_id = buddies.id
        WHERE dives.id = ?
    """, (dive_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Convertir en dictionnaire
    columns = [description[0] for description in cursor.description]
    dive_data = dict(zip(columns, row))

    # Récupérer les tags
    cursor.execute("""
        SELECT tags.nom
        FROM dive_tags
        JOIN tags ON dive_tags.tag_id = tags.id
        WHERE dive_tags.dive_id = ?
    """, (dive_id,))

    tags = [row[0] for row in cursor.fetchall()]
    dive_data['tags'] = tags

    conn.close()
    return dive_data


def update_dive(dive_id: int, dive_data: Dict[str, Any]) -> bool:
    """
    Met à jour les annotations d'une plongée existante.

    Args:
        dive_id: ID de la plongée à modifier
        dive_data: Dictionnaire avec les nouvelles valeurs

    Structure attendue de dive_data :
    {
        'site_nom': 'Port-Cros',
        'buddy_nom': 'Marie',
        'dive_type': 'exploration',
        'rating': 5,
        'notes': 'Mise à jour...',
        'houle': 'faible',
        'visibilite_metres': 15,
        'courant': 'aucun',
        'tags': ['Épave', 'Poissons']
    }

    Returns:
        True si succès, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Insérer/récupérer site
        site_id = _insert_or_get_entity(cursor, 'sites', dive_data['site_nom'])

        # 2. Insérer/récupérer buddy (optionnel)
        buddy_id = None
        if dive_data.get('buddy_nom'):
            buddy_id = _insert_or_get_entity(cursor, 'buddies', dive_data['buddy_nom'])

        # 3. Mettre à jour la plongée
        cursor.execute("""
            UPDATE dives SET
                site_id = ?,
                buddy_id = ?,
                dive_type = ?,
                rating = ?,
                notes = ?,
                houle = ?,
                visibilite_metres = ?,
                courant = ?
            WHERE id = ?
        """, (
            site_id,
            buddy_id,
            dive_data.get('dive_type'),
            dive_data.get('rating'),
            dive_data.get('notes'),
            dive_data.get('houle'),
            dive_data.get('visibilite_metres'),
            dive_data.get('courant'),
            dive_id
        ))

        # 4. Mettre à jour les tags (supprimer anciens, ajouter nouveaux)
        cursor.execute("DELETE FROM dive_tags WHERE dive_id = ?", (dive_id,))

        if dive_data.get('tags'):
            for tag_nom in dive_data['tags']:
                # Insérer ou récupérer le tag
                tag_id = _insert_or_get_entity(cursor, 'tags', tag_nom)

                cursor.execute(
                    "INSERT INTO dive_tags (dive_id, tag_id) VALUES (?, ?)",
                    (dive_id, tag_id)
                )

        conn.commit()
        logger.info(f"Plongée {dive_id} mise à jour avec succès")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la plongée {dive_id} : {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_dive(dive_id: int) -> bool:
    """
    Supprime une plongée de la base de données.

    Args:
        dive_id: ID de la plongée à supprimer

    Returns:
        True si succès, False sinon
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Les tags seront supprimés automatiquement (CASCADE)
        cursor.execute("DELETE FROM dives WHERE id = ?", (dive_id,))

        conn.commit()
        conn.close()

        logger.info(f"Plongée {dive_id} supprimée avec succès")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la plongée {dive_id} : {e}", exc_info=True)
        return False


def get_all_tags() -> List[str]:
    """
    Récupère tous les tags existants dans la base de données.

    Returns:
        Liste des noms de tags (triés par ordre alphabétique)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT nom FROM tags ORDER BY nom")
    tags = [row[0] for row in cursor.fetchall()]

    conn.close()
    return tags


def save_dive_cache(dive_id: int, dataframe: pd.DataFrame, file_hash: Optional[str] = None) -> bool:
    """
    Sauvegarde le DataFrame parsé dans le cache pour améliorer les performances.

    Args:
        dive_id: ID de la plongée
        dataframe: DataFrame à mettre en cache
        file_hash: Hash optionnel du fichier pour détection de modification

    Returns:
        True si succès, False sinon
    """
    try:
        import pickle
        from datetime import datetime

        conn = get_connection()
        cursor = conn.cursor()

        # Sérialiser le DataFrame avec pickle
        cached_data = pickle.dumps(dataframe)
        cache_timestamp = datetime.now().isoformat()

        # Utiliser INSERT OR REPLACE pour gérer les updates
        cursor.execute("""
            INSERT OR REPLACE INTO cached_dive_data
            (dive_id, cached_dataframe, cache_timestamp, file_hash)
            VALUES (?, ?, ?, ?)
        """, (dive_id, cached_data, cache_timestamp, file_hash))

        conn.commit()
        conn.close()

        logger.info(f"DataFrame mis en cache pour la plongée {dive_id}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la mise en cache de la plongée {dive_id} : {e}", exc_info=True)
        return False


def get_dive_cache(dive_id: int) -> Optional[pd.DataFrame]:
    """
    Récupère le DataFrame mis en cache pour une plongée.

    Args:
        dive_id: ID de la plongée

    Returns:
        DataFrame mis en cache ou None si absent/expiré
    """
    try:
        import pickle

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cached_dataframe, cache_timestamp
            FROM cached_dive_data
            WHERE dive_id = ?
        """, (dive_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            logger.debug(f"Pas de cache trouvé pour la plongée {dive_id}")
            return None

        # Désérialiser le DataFrame
        cached_dataframe = pickle.loads(result[0])
        cache_timestamp = result[1]

        logger.info(f"Cache récupéré pour la plongée {dive_id} (créé le {cache_timestamp})")
        return cached_dataframe

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du cache pour la plongée {dive_id} : {e}", exc_info=True)
        return None


def invalidate_dive_cache(dive_id: int) -> bool:
    """
    Invalide le cache d'une plongée (à appeler en cas de modification du fichier).

    Args:
        dive_id: ID de la plongée

    Returns:
        True si succès, False sinon
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cached_dive_data WHERE dive_id = ?", (dive_id,))

        conn.commit()
        conn.close()

        logger.info(f"Cache invalidé pour la plongée {dive_id}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'invalidation du cache pour la plongée {dive_id} : {e}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """
    Récupère les statistiques du cache.

    Returns:
        Dictionnaire avec les statistiques du cache
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Nombre d'entrées en cache
        cursor.execute("SELECT COUNT(*) FROM cached_dive_data")
        cache_count = cursor.fetchone()[0]

        # Taille totale du cache (approximative)
        cursor.execute("SELECT SUM(LENGTH(cached_dataframe)) FROM cached_dive_data")
        cache_size_bytes = cursor.fetchone()[0] or 0
        cache_size_mb = cache_size_bytes / (1024 * 1024)

        # Nombre total de plongées
        cursor.execute("SELECT COUNT(*) FROM dives")
        total_dives = cursor.fetchone()[0]

        conn.close()

        return {
            'cached_dives': cache_count,
            'total_dives': total_dives,
            'cache_hit_rate': (cache_count / total_dives * 100) if total_dives > 0 else 0,
            'cache_size_mb': round(cache_size_mb, 2)
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats du cache : {e}")
        return {}


def get_all_sites_with_stats() -> List[Dict[str, Any]]:
    """
    Récupère tous les sites de plongée avec leurs statistiques agrégées.

    Returns:
        Liste de dictionnaires contenant les informations et statistiques de chaque site
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                sites.id,
                sites.nom,
                sites.pays,
                sites.coordonnees_gps,
                COUNT(dives.id) AS nombre_plongees,
                MAX(dives.profondeur_max) AS profondeur_max,
                AVG(dives.profondeur_max) AS profondeur_moyenne,
                AVG(dives.duree_minutes) AS duree_moyenne,
                AVG(dives.temperature_min) AS temperature_moyenne,
                AVG(dives.sac) AS sac_moyen,
                AVG(dives.rating) AS note_moyenne,
                MIN(dives.date) AS premiere_plongee,
                MAX(dives.date) AS derniere_plongee
            FROM sites
            LEFT JOIN dives ON sites.id = dives.site_id
            GROUP BY sites.id, sites.nom, sites.pays, sites.coordonnees_gps
            ORDER BY nombre_plongees DESC
        """

        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        sites = []
        for row in rows:
            site_dict = dict(zip(columns, row))
            sites.append(site_dict)

        conn.close()
        logger.debug(f"Récupération de {len(sites)} sites avec statistiques")
        return sites

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des sites avec stats : {e}", exc_info=True)
        return []


def update_site_coordinates(site_id: int, coordonnees_gps: str) -> bool:
    """
    Met à jour les coordonnées GPS d'un site de plongée.

    Args:
        site_id: ID du site
        coordonnees_gps: Coordonnées au format "latitude,longitude" (ex: "43.0242,5.5485")

    Returns:
        True si succès, False sinon
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE sites SET coordonnees_gps = ? WHERE id = ?",
            (coordonnees_gps, site_id)
        )

        conn.commit()
        conn.close()

        logger.info(f"Coordonnées GPS mises à jour pour le site {site_id}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des coordonnées du site {site_id} : {e}", exc_info=True)
        return False


def get_site_by_name(site_name: str) -> Optional[Dict[str, Any]]:
    """
    Récupère un site par son nom.

    Args:
        site_name: Nom du site

    Returns:
        Dictionnaire avec les informations du site ou None si non trouvé
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, nom, pays, coordonnees_gps FROM sites WHERE nom = ?",
            (site_name,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'nom': row[1],
            'pays': row[2],
            'coordonnees_gps': row[3]
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du site '{site_name}' : {e}", exc_info=True)
        return None


# Initialiser la base au premier import (seulement si elle n'existe pas)
if not DB_PATH.exists():
    init_database()
