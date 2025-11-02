# 🤿 Dive Analyzer

Analyseur de fichiers de plongée sous-marine avec interface Streamlit et journal de bord SQLite.

## Description

Application web complète pour analyser vos plongées et gérer votre journal de bord. Supporte les formats FIT, XML, UDDF et DL7 provenant des ordinateurs de plongée.

## Fonctionnalités

### 📤 Analyse de Plongée
- Upload de fichiers de plongée (FIT, UDDF, XML, DL7)
- Graphique interactif du profil de plongée (Plotly)
- Calcul automatique des métriques :
  - Profondeur max, durée, température
  - SAC (Surface Air Consumption)
  - Vitesse de remontée
  - Temps de fond
  - Détection des paliers de sécurité
- Analyse de saturation azote (Bühlmann ZH-L16C)
- Alertes de sécurité automatiques
- Formulaire d'annotation avec conditions de plongée

### 📖 Journal de Plongée
- Base de données SQLite locale
- Statistiques globales (plongées totales, prof max, SAC médian, etc.)
- Filtres avancés (site, date, profondeur)
- Visualisation détaillée par plongée :
  - **📋 Informations** : Vue complète en lecture seule
  - **📊 Profil Graphique** : Rechargement du fichier original
  - **✏️ Éditer** : Modification des annotations et suppression
- Tags personnalisables et dynamiques

## Installation

### Prérequis
- Python 3.8+
- pip

### Installation des dépendances

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

### Lancement de l'application

```bash
# Avec le script de démarrage
./start.sh

# Ou manuellement
streamlit run app.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

### Navigation

1. **Page d'accueil** : Choix entre Analyse ou Journal
2. **Analyse** : Uploadez un fichier de plongée → Analysez → Annotez → Sauvegardez
3. **Journal** : Consultez, filtrez, visualisez et éditez vos plongées

## Architecture

```
dive-analyzer/
├── app.py                   # Page d'accueil
├── pages/
│   ├── 1_📤_Analyse.py      # Page d'analyse
│   └── 2_📖_Journal.py      # Journal de plongée
├── database.py              # Module SQLite (CRUD)
├── parser.py                # Parsers FIT/UDDF/XML/DL7
├── visualizer.py            # Graphiques Plotly
├── analyzer.py              # Calculs physique plongée
├── requirements.txt         # Dépendances Python
└── README.md
```

### Base de données

5 tables relationnelles :
- **dives** : Plongées principales (métriques + référence fichier)
- **sites** : Sites de plongée (nom, pays, GPS)
- **buddies** : Binômes/palanquées
- **tags** : Tags personnalisables
- **dive_tags** : Relation many-to-many

Chemin DB : `~/dive-analyzer/dive_log.db`

## Technologies

- **Streamlit** : Interface web
- **Plotly** : Graphiques interactifs
- **Pandas** : Manipulation de données
- **SQLite** : Base de données locale
- **FitParse** : Parser FIT (Garmin, Suunto, etc.)
- **NumPy** : Calculs physique plongée

## Formats supportés

| Format | Extension | Source typique |
|--------|-----------|----------------|
| FIT    | .fit      | Garmin Descent, Suunto EON |
| UDDF   | .uddf, .xml | Subsurface, Universal format |
| XML    | .xml      | Divers ordinateurs |
| DL7    | .dl7      | OSTC (HeinrichsWeikamp) |

## Licence

MIT License - Libre d'utilisation et modification

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Roadmap

- [ ] Export PDF du journal
- [ ] Statistiques avancées (graphes progression)
- [ ] Support Bluetooth ordinateur de plongée
- [ ] Mode multi-utilisateurs
- [ ] Intégration API météo marine
