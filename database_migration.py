"""
Migration de base de données pour ajouter les fonctionnalités de galerie média et reconnaissance d'espèces.

Tables ajoutées :
- dive_media : Photos et vidéos associées aux plongées
- species : Catalogue d'espèces marines
- dive_species : Liaison plongées-espèces (many-to-many)
"""

import sqlite3
from pathlib import Path

# Déterminer le chemin de la base de données
APP_DIR = Path.home() / "dive-analyzer"
DB_PATH = APP_DIR / "dive_analyzer.db"


def get_connection() -> sqlite3.Connection:
    """Crée et retourne une connexion à la base de données."""
    # Créer le répertoire s'il n'existe pas
    APP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate_add_media_and_species_tables() -> None:
    """
    Ajoute les tables pour la galerie média et la reconnaissance d'espèces.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Table 7 : Médias (photos/vidéos) associés aux plongées
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dive_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dive_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('photo', 'video')),
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                thumbnail_path TEXT,
                file_size_bytes INTEGER,
                mime_type TEXT,
                width INTEGER,
                height INTEGER,
                duration_seconds REAL,
                upload_date TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE
            )
        """)
        print("✓ Table dive_media créée")

        # Index pour accélérer les requêtes par plongée
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dive_media_dive_id
            ON dive_media(dive_id)
        """)
        print("✓ Index idx_dive_media_dive_id créé")

        # Table 8 : Catalogue d'espèces marines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS species (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scientific_name TEXT NOT NULL UNIQUE,
                common_name_fr TEXT,
                common_name_en TEXT,
                category TEXT CHECK(category IN ('poisson', 'corail', 'mollusque',
                    'crustacé', 'échinoderme', 'mammifère', 'reptile', 'autre')),
                description TEXT,
                conservation_status TEXT,
                habitat TEXT,
                depth_range TEXT,
                image_url TEXT,
                created_date TEXT NOT NULL
            )
        """)
        print("✓ Table species créée")

        # Table 9 : Liaison plongées-espèces (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dive_species (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dive_id INTEGER NOT NULL,
                species_id INTEGER NOT NULL,
                media_id INTEGER,
                confidence_score REAL CHECK(confidence_score >= 0 AND confidence_score <= 1),
                quantity INTEGER DEFAULT 1,
                notes TEXT,
                detected_by TEXT CHECK(detected_by IN ('ai', 'manual', 'verified')),
                detection_date TEXT NOT NULL,
                FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE,
                FOREIGN KEY (species_id) REFERENCES species(id) ON DELETE CASCADE,
                FOREIGN KEY (media_id) REFERENCES dive_media(id) ON DELETE SET NULL,
                UNIQUE(dive_id, species_id, media_id)
            )
        """)
        print("✓ Table dive_species créée")

        # Index pour accélérer les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dive_species_dive_id
            ON dive_species(dive_id)
        """)
        print("✓ Index idx_dive_species_dive_id créé")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dive_species_species_id
            ON dive_species(species_id)
        """)
        print("✓ Index idx_dive_species_species_id créé")

        # Insérer quelques espèces communes pour démarrer
        common_species = [
            ('Amphiprion ocellaris', 'Poisson-clown à ocelles', 'Clownfish', 'poisson',
             'Poisson emblématique vivant en symbiose avec les anémones', 'LC', 'Récifs coralliens', '1-12m'),
            ('Chelonia mydas', 'Tortue verte', 'Green sea turtle', 'reptile',
             'Grande tortue marine herbivore', 'EN', 'Eaux côtières et récifs', '0-40m'),
            ('Acropora cervicornis', 'Corail corne de cerf', 'Staghorn coral', 'corail',
             'Corail branchu à croissance rapide', 'CR', 'Récifs peu profonds', '1-30m'),
            ('Manta birostris', 'Raie manta géante', 'Giant manta ray', 'poisson',
             'La plus grande des raies', 'EN', 'Eaux pélagiques et récifs', '0-120m'),
            ('Rhincodon typus', 'Requin-baleine', 'Whale shark', 'poisson',
             'Le plus grand poisson du monde', 'EN', 'Eaux pélagiques', '0-1000m'),
            ('Octopus vulgaris', 'Poulpe commun', 'Common octopus', 'mollusque',
             'Mollusque céphalopode intelligent', 'LC', 'Fonds rocheux et récifs', '0-200m'),
            ('Pterapogon kauderni', 'Poisson cardinal de Banggai', 'Banggai cardinalfish', 'poisson',
             'Petit poisson endémique d\'Indonésie', 'EN', 'Récifs et herbiers', '1-5m'),
            ('Synchiropus splendidus', 'Poisson-mandarin', 'Mandarinfish', 'poisson',
             'Poisson aux couleurs éclatantes', 'LC', 'Récifs coralliens', '1-18m'),
            ('Hippocampus sp.', 'Hippocampe', 'Seahorse', 'poisson',
             'Poisson à la nage verticale caractéristique', 'VU', 'Herbiers et récifs', '0-50m'),
            ('Physeter macrocephalus', 'Cachalot', 'Sperm whale', 'mammifère',
             'Plus grand des cétacés à dents', 'VU', 'Eaux profondes', '0-2000m')
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO species
            (scientific_name, common_name_fr, common_name_en, category,
             description, conservation_status, habitat, depth_range, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, common_species)

        conn.commit()
        print(f"✓ {cursor.rowcount} espèces communes ajoutées au catalogue")
        print("✓ Migration réussie : tables média et espèces créées")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Erreur lors de la migration : {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔄 Démarrage de la migration...")
    migrate_add_media_and_species_tables()
    print("✅ Migration terminée avec succès!")
