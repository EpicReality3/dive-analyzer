# 🤝 Guide de Contribution - Dive Analyzer

Merci de votre intérêt pour contribuer à Dive Analyzer ! Ce guide vous aidera à démarrer.

---

## 📋 Table des Matières

- [Code de Conduite](#code-de-conduite)
- [Comment Contribuer](#comment-contribuer)
- [Architecture du Projet](#architecture-du-projet)
- [Configuration de l'Environnement](#configuration-de-lenvironnement)
- [Standards de Code](#standards-de-code)
- [Tests](#tests)
- [Processus de Pull Request](#processus-de-pull-request)

---

## 🤲 Code de Conduite

Ce projet suit un code de conduite basé sur le respect mutuel :

- Soyez respectueux et inclusif
- Acceptez les critiques constructives
- Concentrez-vous sur ce qui est meilleur pour la communauté
- Faites preuve d'empathie envers les autres

---

## 💡 Comment Contribuer

### Types de Contributions

Nous acceptons plusieurs types de contributions :

1. **🐛 Rapports de Bugs**
   - Utilisez les GitHub Issues
   - Décrivez le problème en détail
   - Incluez les étapes pour reproduire
   - Précisez votre environnement (OS, Python version)

2. **✨ Nouvelles Fonctionnalités**
   - Proposez d'abord via une Issue
   - Discutez de l'implémentation
   - Suivez les standards du projet

3. **📚 Documentation**
   - Améliorations de README
   - Commentaires de code
   - Tutoriels et guides

4. **🧪 Tests**
   - Ajout de tests unitaires
   - Amélioration de la couverture
   - Tests d'intégration

---

## 🏗️ Architecture du Projet

```
dive-analyzer/
├── app.py                      # Page d'accueil Streamlit
├── pages/                      # Pages multi-pages Streamlit
│   ├── 1_📤_Analyse.py         # Page d'analyse de fichiers
│   └── 2_📖_Journal.py         # Journal de plongée
├── database.py                 # Module SQLite (CRUD + cache)
├── parser.py                   # Parsers FIT/UDDF/XML/DL7
├── analyzer.py                 # Calculs physique plongée
├── visualizer.py               # Graphiques Plotly
├── validation.py               # Validation fichiers
├── config.py                   # Configuration centralisée
├── logger.py                   # Système de logging
├── tests/                      # Tests unitaires (pytest)
│   ├── test_validation.py
│   ├── test_parser.py
│   └── test_database.py
└── requirements.txt            # Dépendances Python
```

### Modules Principaux

- **database.py** : Gestion SQLite avec 5 tables (sites, buddies, tags, dives, dive_tags) + cache
- **parser.py** : Architecture extensible avec `BaseDiveParser` (FIT, UDDF, XML, DL7)
- **validation.py** : Validation multi-niveaux (extension, taille, magic bytes)
- **config.py** : Pattern Singleton pour configuration globale
- **logger.py** : Logging rotatif avec double sortie (console + fichier)

---

## ⚙️ Configuration de l'Environnement

### Prérequis

- **Python 3.8+**
- **pip** et **virtualenv**
- **Git**

### Installation

```bash
# 1. Cloner le repository
git clone https://github.com/votre-user/dive-analyzer.git
cd dive-analyzer

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer les dépendances de développement
pip install pytest pytest-cov black flake8

# 5. Lancer l'application
streamlit run app.py
```

### Structure de la Base de Données

La base est initialisée automatiquement au premier lancement.

```sql
-- Tables principales
CREATE TABLE sites (id, nom, pays, coordonnees_gps)
CREATE TABLE buddies (id, nom, niveau_certification)
CREATE TABLE tags (id, nom, categorie)
CREATE TABLE dives (id, date, site_id, buddy_id, ...)
CREATE TABLE dive_tags (dive_id, tag_id)
CREATE TABLE cached_dive_data (dive_id, cached_dataframe, ...)

-- Index (Phase 2)
CREATE INDEX idx_dives_date ON dives(date DESC)
CREATE INDEX idx_dives_site_id ON dives(site_id)
CREATE INDEX idx_dives_rating ON dives(rating DESC)
```

---

## 📝 Standards de Code

### Style Python

Nous suivons **PEP 8** avec quelques ajustements :

- **Longueur de ligne** : 100 caractères max
- **Indentation** : 4 espaces (pas de tabs)
- **Quotes** : Simple quotes `'` (sauf docstrings avec `"""`)
- **Imports** : Ordre alphabétique par groupe (stdlib, third-party, local)

### Formatage avec Black

```bash
# Formater tout le code
black .

# Vérifier sans modifier
black --check .
```

### Linting avec Flake8

```bash
# Vérifier le code
flake8 . --max-line-length=100 --ignore=E203,W503
```

### Docstrings

Utilisez le format **Google Style** :

```python
def calculate_sac(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcule le Surface Air Consumption (SAC).

    Args:
        df: DataFrame avec colonnes 'profondeur_metres', 'pression_bouteille_bar'

    Returns:
        Dictionnaire avec 'sac' (L/min) et 'rmv' (L/min)

    Raises:
        ValueError: Si les colonnes nécessaires sont absentes

    Example:
        >>> df = pd.DataFrame(...)
        >>> result = calculate_sac(df)
        >>> print(f"SAC: {result['sac']:.1f} L/min")
    """
    pass
```

### Nommage

- **Variables/Fonctions** : `snake_case`
- **Classes** : `PascalCase`
- **Constants** : `UPPER_SNAKE_CASE`
- **Modules** : `lowercase`

---

## 🧪 Tests

### Exécution des Tests

```bash
# Tous les tests
pytest tests/

# Avec couverture
pytest tests/ --cov=. --cov-report=html

# Tests spécifiques
pytest tests/test_validation.py -v

# Tests avec output détaillé
pytest tests/ -vv --tb=short
```

### Objectif de Couverture

- **Minimum** : 80%
- **Cible** : 90%+

### Structure des Tests

Chaque test doit :

1. **Arranger** : Préparer les données
2. **Agir** : Exécuter la fonction
3. **Asserter** : Vérifier les résultats

```python
def test_validate_file_extension():
    """Test de validation d'extension valide"""
    # Arrange
    filename = "dive.fit"

    # Act
    is_valid, error = validate_file_extension(filename)

    # Assert
    assert is_valid is True
    assert error == ""
```

### Fixtures

Utilisez les fixtures pytest pour les ressources partagées :

```python
@pytest.fixture
def temp_db():
    """Crée une base de données temporaire pour les tests"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db_path = Path(temp_file.name)
    temp_file.close()

    yield temp_db_path

    if temp_db_path.exists():
        temp_db_path.unlink()
```

---

## 🔀 Processus de Pull Request

### Avant de Soumettre

1. **Créer une branche** depuis `main`
   ```bash
   git checkout -b feature/ma-nouvelle-fonctionnalite
   ```

2. **Faire vos changements**
   - Code clair et documenté
   - Tests unitaires ajoutés
   - Documentation mise à jour

3. **Vérifier la qualité**
   ```bash
   # Tests
   pytest tests/ --cov=. --cov-report=term

   # Formatage
   black .

   # Linting
   flake8 .
   ```

4. **Commit avec message clair**
   ```bash
   git add .
   git commit -m "feat: Ajout du parser DL7 complet

   - Implémente le parsing du format OSTC DL7
   - Ajoute tests unitaires avec couverture 95%
   - Met à jour la documentation README"
   ```

### Format des Commits

Utilisez **Conventional Commits** :

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation seule
- `test:` Ajout/modification de tests
- `refactor:` Refactorisation sans changement fonctionnel
- `perf:` Amélioration des performances
- `chore:` Tâches diverses (dépendances, config, etc.)

### Soumettre la Pull Request

1. **Push vers votre fork**
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```

2. **Créer la PR sur GitHub**
   - Titre clair et descriptif
   - Description détaillée des changements
   - Référence aux issues liées

3. **Template de PR**
   ```markdown
   ## Description
   Brève description des changements

   ## Type de changement
   - [ ] Bug fix
   - [ ] Nouvelle fonctionnalité
   - [ ] Breaking change
   - [ ] Documentation

   ## Tests
   - [ ] Tests unitaires ajoutés
   - [ ] Tous les tests passent
   - [ ] Couverture > 80%

   ## Checklist
   - [ ] Code formaté (black)
   - [ ] Code linté (flake8)
   - [ ] Documentation mise à jour
   - [ ] CHANGELOG.md mis à jour
   ```

---

## 📚 Ressources Additionnelles

### Documentation Technique

- **Streamlit** : https://docs.streamlit.io
- **Pandas** : https://pandas.pydata.org/docs
- **Plotly** : https://plotly.com/python
- **SQLite** : https://www.sqlite.org/docs.html
- **FitParse** : https://github.com/dtcooper/python-fitparse

### Standards de Plongée

- **UDDF Format** : https://www.streit.cc/extern/uddf_v321/en/index.html
- **FIT SDK** : https://developer.garmin.com/fit/overview/
- **Bühlmann ZH-L16** : Modèle de décompression

---

## 🙋 Questions ?

- **Issues GitHub** : Pour bugs et features
- **Discussions GitHub** : Pour questions générales
- **Email** : [maintainer@example.com](mailto:maintainer@example.com)

---

## 📜 Licence

En contribuant, vous acceptez que vos contributions soient sous la même licence MIT que le projet.

---

**Merci de contribuer à Dive Analyzer ! 🤿**
