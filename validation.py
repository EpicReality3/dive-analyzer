"""
Module de validation pour les fichiers uploadés.

Ce module fournit des fonctions de validation robustes pour garantir
la sécurité et l'intégrité des fichiers uploadés par les utilisateurs.
"""

from pathlib import Path
from typing import Tuple, Optional
from config import config
from logger import get_logger

logger = get_logger(__name__)


# Magic bytes des formats supportés (pour validation stricte)
MAGIC_BYTES = {
    '.fit': [
        b'\x0e\x10',  # FIT header signature (version 1.0)
        b'\x0e\x20',  # FIT header signature (version 2.0)
    ],
    '.xml': [
        b'<?xml',  # XML declaration
        b'<uddf',  # UDDF root
    ],
    '.uddf': [
        b'<?xml',  # UDDF est un format XML
        b'<uddf',
    ],
    # DL7 : format binaire propriétaire OSTC, pas de magic bytes connus
    '.dl7': []
}


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """
    Valide l'extension du fichier.

    Args:
        filename: Nom du fichier

    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si l'extension est supportée
        - error_message: Message d'erreur si invalide, vide sinon
    """
    ext = Path(filename).suffix.lower()

    if not ext:
        return False, "Fichier sans extension"

    if ext not in config.ALLOWED_EXTENSIONS:
        allowed = ', '.join(config.ALLOWED_EXTENSIONS)
        return False, f"Extension '{ext}' non supportée. Formats acceptés : {allowed}"

    return True, ""


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Valide la taille du fichier.

    Args:
        file_size: Taille du fichier en bytes

    Returns:
        Tuple (is_valid, error_message)
    """
    if file_size == 0:
        return False, "Fichier vide (0 bytes)"

    if file_size > config.max_file_size_bytes:
        max_mb = config.MAX_FILE_SIZE_MB
        actual_mb = file_size / (1024 * 1024)
        return False, f"Fichier trop volumineux ({actual_mb:.1f} MB). Taille maximale : {max_mb} MB"

    return True, ""


def validate_file_content(file_content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Valide le contenu du fichier via les magic bytes.

    Cette validation vérifie que le contenu réel du fichier correspond
    à son extension déclarée, pour détecter les tentatives de renommage
    malveillant.

    Args:
        file_content: Contenu brut du fichier
        filename: Nom du fichier

    Returns:
        Tuple (is_valid, error_message)
    """
    ext = Path(filename).suffix.lower()

    # Pas de validation stricte pour DL7 (format propriétaire)
    if ext == '.dl7':
        logger.warning(f"Validation magic bytes ignorée pour {filename} (format DL7 propriétaire)")
        return True, ""

    # Récupérer les magic bytes attendus
    expected_magic = MAGIC_BYTES.get(ext, [])

    if not expected_magic:
        # Si pas de magic bytes définis, on accepte
        return True, ""

    # Vérifier si le fichier commence par l'un des magic bytes attendus
    file_start = file_content[:20]  # Lire les 20 premiers bytes

    for magic in expected_magic:
        if file_start.startswith(magic):
            return True, ""

    # Aucun magic byte ne correspond
    logger.warning(f"Magic bytes invalides pour {filename} (extension {ext})")
    return False, f"Le contenu du fichier ne correspond pas à l'extension {ext}. Fichier potentiellement corrompu ou renommé."


def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """
    Validation complète d'un fichier uploadé (extension, taille, contenu).

    Cette fonction effectue toutes les validations de sécurité nécessaires
    avant de permettre le parsing du fichier.

    Args:
        uploaded_file: Fichier uploadé via Streamlit (avec .name, .size, .read())

    Returns:
        Tuple (is_valid, error_message)
        - is_valid: True si toutes les validations passent
        - error_message: Message d'erreur descriptif si invalide, vide sinon

    Exemple:
        >>> is_valid, error = validate_uploaded_file(uploaded_file)
        >>> if not is_valid:
        >>>     st.error(f"❌ {error}")
        >>>     return
    """
    logger.info(f"Validation du fichier uploadé : {uploaded_file.name}")

    # 1. Valider l'extension
    valid, error = validate_file_extension(uploaded_file.name)
    if not valid:
        logger.error(f"Extension invalide : {error}")
        return False, error

    # 2. Valider la taille
    valid, error = validate_file_size(uploaded_file.size)
    if not valid:
        logger.error(f"Taille invalide : {error}")
        return False, error

    # 3. Valider le contenu (magic bytes)
    # Note: On doit lire le contenu, donc on le retourne à la position 0 après
    file_content = uploaded_file.read()
    uploaded_file.seek(0)  # Remettre le curseur au début

    valid, error = validate_file_content(file_content, uploaded_file.name)
    if not valid:
        logger.error(f"Contenu invalide : {error}")
        return False, error

    # Toutes les validations sont passées
    size_kb = uploaded_file.size / 1024
    logger.info(f"✅ Fichier validé : {uploaded_file.name} ({size_kb:.1f} KB)")
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter les injections path traversal.

    Supprime les caractères dangereux et normalise le nom de fichier.

    Args:
        filename: Nom de fichier original

    Returns:
        Nom de fichier nettoyé et sécurisé

    Exemple:
        >>> sanitize_filename("../../etc/passwd.fit")
        'etc_passwd.fit'
        >>> sanitize_filename("my dive (2024).fit")
        'my_dive_2024.fit'
    """
    # Extraire le nom de base (sans chemin)
    filename = Path(filename).name

    # Remplacer les caractères spéciaux par des underscores
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    sanitized = ''.join(c if c in safe_chars else '_' for c in filename)

    # Éviter les noms de fichiers vides ou ne commençant/finissant par un point
    sanitized = sanitized.strip('._')

    if not sanitized:
        sanitized = "unnamed_dive"

    logger.debug(f"Nom de fichier nettoyé : '{filename}' → '{sanitized}'")
    return sanitized


if __name__ == '__main__':
    # Tests de validation
    print("🧪 Tests de validation de fichiers\n")

    # Test 1 : Extension valide
    print("Test 1 : Extensions")
    print(f"  .fit : {validate_file_extension('test.fit')}")
    print(f"  .exe : {validate_file_extension('test.exe')}")
    print()

    # Test 2 : Taille
    print("Test 2 : Tailles de fichiers")
    print(f"  100 KB : {validate_file_size(100 * 1024)}")
    print(f"  100 MB : {validate_file_size(100 * 1024 * 1024)}")
    print(f"  0 bytes : {validate_file_size(0)}")
    print()

    # Test 3 : Sanitization
    print("Test 3 : Nettoyage noms de fichiers")
    print(f"  '../../etc/passwd.fit' → '{sanitize_filename('../../etc/passwd.fit')}'")
    print(f"  'my dive (2024).fit' → '{sanitize_filename('my dive (2024).fit')}'")
    print(f"  '  .hidden  ' → '{sanitize_filename('  .hidden  ')}'")
    print()

    print("✅ Tests terminés")
