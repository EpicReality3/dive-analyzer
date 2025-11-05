"""
Configuration centralisée pour l'application Dive Analyzer.

Ce module définit toutes les constantes, paramètres et chemins utilisés
dans l'application. Centraliser la configuration facilite la maintenance
et évite les valeurs hardcodées dispersées dans le code.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Set
import logging


@dataclass
class Config:
    """
    Configuration centralisée de l'application Dive Analyzer.

    Cette classe utilise le pattern Singleton via une instance globale
    pour garantir une configuration cohérente dans toute l'application.
    """

    # ===== CHEMINS =====
    APP_DIR: Path = field(default_factory=lambda: Path.home() / "dive-analyzer")
    UPLOADS_DIR: Path = field(init=False)
    BACKUP_DIR: Path = field(init=False)
    DB_PATH: Path = field(init=False)
    LOG_FILE: Path = field(init=False)

    # ===== LIMITES FICHIERS =====
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: Set[str] = field(
        default_factory=lambda: {'.fit', '.xml', '.uddf', '.dl7'}
    )

    # ===== PARAMÈTRES PHYSIQUE PLONGÉE =====
    # Profondeur
    MAX_DEPTH_M: float = 200.0
    DEPTH_THRESHOLD_M: float = 3.0  # Seuil pour calcul temps de fond

    # Vitesses (m/min)
    MAX_SAFE_ASCENT_SPEED_M_MIN: float = 10.0
    WARNING_ASCENT_SPEED_M_MIN: float = 15.0
    MAX_REASONABLE_SPEED_M_MIN: float = 30.0  # Clipper au-delà

    # Décompression (modèle simplifié)
    COMPARTMENT_HALF_TIME_MIN: float = 40.0  # Demi-vie compartiment N₂
    SURFACE_INTERVAL_MULTIPLIER: float = 3.0  # Nombre de demi-vies recommandées

    # Détection paliers
    SAFETY_STOP_DEPTH_TOLERANCE_M: float = 1.5
    SAFETY_STOP_MIN_DURATION_S: int = 30

    # ===== BASE DE DONNÉES =====
    DB_BACKUP_COUNT: int = 10  # Nombre de backups à conserver
    ENABLE_AUTO_BACKUP: bool = True

    # ===== LOGGING =====
    LOG_LEVEL: int = logging.INFO
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # ===== INTERFACE UTILISATEUR =====
    DIVES_PER_PAGE: int = 25  # Pagination du journal
    DEFAULT_TANK_VOLUME_L: float = 12.0  # Volume bouteille par défaut

    # ===== TAGS STANDARDS =====
    STANDARD_TAGS: list = field(default_factory=lambda: [
        "Épave", "Grotte", "Tombant", "Nuit", "Dérivante",
        "Formation", "Technique", "Faune", "Flore", "Photo",
        "Plongée profonde", "Nitrox", "Trimix", "Recycleur"
    ])

    # ===== COULEURS GRAPHIQUES =====
    COLOR_SAFE: str = '#1f77b4'  # Bleu
    COLOR_WARNING: str = '#ff7f0e'  # Orange
    COLOR_DANGER: str = '#d62728'  # Rouge
    COLOR_SAFETY_STOP: str = 'rgba(144, 238, 144, 0.2)'  # Vert transparent

    def __post_init__(self):
        """
        Initialise les chemins dérivés et crée les répertoires nécessaires.

        Cette méthode est appelée automatiquement après __init__ par dataclass.
        """
        # Définir les chemins dérivés
        self.UPLOADS_DIR = self.APP_DIR / "uploads"
        self.BACKUP_DIR = self.APP_DIR / "backups"
        self.DB_PATH = self.APP_DIR / "dive_log.db"
        self.LOG_FILE = self.APP_DIR / "dive_analyzer.log"

        # Créer tous les répertoires nécessaires
        self._create_directories()

    def _create_directories(self) -> None:
        """Crée les répertoires de l'application s'ils n'existent pas."""
        directories = [
            self.APP_DIR,
            self.UPLOADS_DIR,
            self.BACKUP_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def max_file_size_bytes(self) -> int:
        """Retourne la taille maximale de fichier en bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    def validate_depth(self, depth_m: float) -> bool:
        """
        Valide qu'une profondeur est dans les limites raisonnables.

        Args:
            depth_m: Profondeur en mètres

        Returns:
            True si la profondeur est valide, False sinon
        """
        return 0 <= depth_m <= self.MAX_DEPTH_M

    def get_ascent_speed_category(self, speed_m_min: float) -> str:
        """
        Catégorise une vitesse de remontée.

        Args:
            speed_m_min: Vitesse de remontée en m/min

        Returns:
            'safe', 'warning' ou 'danger'
        """
        if speed_m_min < self.MAX_SAFE_ASCENT_SPEED_M_MIN:
            return 'safe'
        elif speed_m_min < self.WARNING_ASCENT_SPEED_M_MIN:
            return 'warning'
        else:
            return 'danger'

    def get_color_for_speed(self, speed_m_min: float) -> str:
        """
        Retourne la couleur associée à une vitesse de remontée.

        Args:
            speed_m_min: Vitesse de remontée en m/min

        Returns:
            Code couleur hexadécimal
        """
        category = self.get_ascent_speed_category(speed_m_min)

        color_map = {
            'safe': self.COLOR_SAFE,
            'warning': self.COLOR_WARNING,
            'danger': self.COLOR_DANGER
        }

        return color_map[category]

    def __repr__(self) -> str:
        """Représentation lisible de la configuration."""
        return (
            f"Config(\n"
            f"  APP_DIR={self.APP_DIR},\n"
            f"  DB_PATH={self.DB_PATH},\n"
            f"  MAX_FILE_SIZE_MB={self.MAX_FILE_SIZE_MB},\n"
            f"  LOG_LEVEL={logging.getLevelName(self.LOG_LEVEL)}\n"
            f")"
        )


# Instance globale de configuration (Singleton)
config = Config()


if __name__ == '__main__':
    # Test de la configuration
    print("🔧 Configuration Dive Analyzer")
    print("=" * 50)
    print(config)
    print("\n📁 Répertoires créés :")
    print(f"  - {config.APP_DIR}")
    print(f"  - {config.UPLOADS_DIR}")
    print(f"  - {config.BACKUP_DIR}")
    print("\n✅ Configuration initialisée avec succès")

    # Test des méthodes de validation
    print("\n🧪 Tests de validation :")
    print(f"  Profondeur 42m valide : {config.validate_depth(42.0)}")
    print(f"  Profondeur 250m valide : {config.validate_depth(250.0)}")
    print(f"  Vitesse 8 m/min : {config.get_ascent_speed_category(8.0)}")
    print(f"  Vitesse 12 m/min : {config.get_ascent_speed_category(12.0)}")
    print(f"  Vitesse 18 m/min : {config.get_ascent_speed_category(18.0)}")
