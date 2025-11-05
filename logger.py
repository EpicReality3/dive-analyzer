"""
Module de logging centralisé pour l'application Dive Analyzer.

Ce module fournit une configuration de logging professionnelle avec :
- Logs fichiers rotatifs (évite la croissance infinie)
- Logs console pour le développement
- Formatage structuré avec timestamps
- Niveaux de log configurables
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Configure et retourne un logger avec handlers fichier et console.

    Args:
        name: Nom du logger (généralement __name__ du module)
        log_file: Chemin du fichier de log (par défaut ~/dive-analyzer/dive_analyzer.log)
        level: Niveau de log minimum (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Taille maximale du fichier de log avant rotation
        backup_count: Nombre de fichiers de backup à conserver

    Returns:
        Logger configuré

    Exemple:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application démarrée")
        >>> logger.error("Erreur lors du parsing", exc_info=True)
    """
    # Créer le logger
    logger = logging.getLogger(name)

    # Éviter de reconfigurer un logger déjà configuré
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Format du log : [2025-11-05 14:30:25] [INFO] [parser.FitParser] Message
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler 1 : Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler 2 : Fichier rotatif (si chemin fourni)
    if log_file is None:
        log_dir = Path.home() / "dive-analyzer"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "dive_analyzer.log"

    # S'assurer que le répertoire existe
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Ne pas propager aux loggers parents (évite la duplication)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger existant ou en crée un nouveau.

    Args:
        name: Nom du logger (généralement __name__ du module)

    Returns:
        Logger configuré

    Note:
        Cette fonction est un raccourci pour obtenir un logger
        avec la configuration par défaut.
    """
    # Si le logger existe déjà et est configuré, le retourner
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Sinon, le configurer avec les paramètres par défaut
        return setup_logger(name)

    return logger


# Logger principal de l'application
app_logger = setup_logger('dive_analyzer')


if __name__ == '__main__':
    # Test du système de logging
    test_logger = setup_logger('test', level=logging.DEBUG)

    test_logger.debug("Message de débogage")
    test_logger.info("Message d'information")
    test_logger.warning("Message d'avertissement")
    test_logger.error("Message d'erreur")

    try:
        1 / 0
    except ZeroDivisionError:
        test_logger.error("Erreur avec stack trace", exc_info=True)

    print(f"\n✅ Logs écrits dans : {Path.home() / 'dive-analyzer' / 'dive_analyzer.log'}")
