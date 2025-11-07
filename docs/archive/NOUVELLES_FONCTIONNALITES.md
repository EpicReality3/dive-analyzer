# 📸🐠 Nouvelles Fonctionnalités - Galerie Média & Reconnaissance d'Espèces

## Vue d'ensemble

Deux fonctionnalités majeures ont été ajoutées à l'application Dive Analyzer :

1. **📸 Galerie Photos/Vidéos** - Gestion complète des médias associés aux plongées
2. **🐠 Reconnaissance d'Espèces** - Identification IA des espèces marines avec catalogue complet

---

## 📸 Galerie Photos/Vidéos

### Fonctionnalités

- **Upload de médias** : Photos (JPG, PNG, WEBP, HEIC) et vidéos (MP4, MOV, AVI, WEBM)
- **Association aux plongées** : Chaque média est lié à une plongée spécifique
- **Miniatures automatiques** : Génération de thumbnails pour les photos
- **Métadonnées** : Description, tags, dimensions, durée (vidéos)
- **Visualisation** : Galerie avec grille responsive et filtres
- **Statistiques** : Nombre de médias, taille totale, répartition photos/vidéos

### Structure de la base de données

**Table `dive_media`** :
```sql
CREATE TABLE dive_media (
    id INTEGER PRIMARY KEY,
    dive_id INTEGER NOT NULL,
    type TEXT CHECK(type IN ('photo', 'video')),
    filename TEXT,
    filepath TEXT,
    thumbnail_path TEXT,
    file_size_bytes INTEGER,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    duration_seconds REAL,
    upload_date TEXT,
    description TEXT,
    tags TEXT,
    FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE
);
```

### Utilisation

#### 1. Accéder à la galerie
Naviguez vers **📸 Galerie** depuis le menu principal.

#### 2. Uploader des médias
- Onglet **⬆️ Upload**
- Sélectionnez une plongée
- Choisissez un ou plusieurs fichiers
- Ajoutez description et tags (optionnel)
- Cliquez sur **📤 Uploader les fichiers**

#### 3. Visualiser les médias
- Onglet **🖼️ Galerie**
- Filtrez par type (photos/vidéos)
- Utilisez la pagination
- Cliquez sur **ℹ️ Détails** pour plus d'informations

#### 4. Voir les médias d'une plongée
Dans **📖 Journal**, sélectionnez une plongée :
- Les médias s'affichent dans l'onglet **📋 Informations**
- Miniatures en grille avec descriptions

### Module Python : `media_manager.py`

**Fonctions principales** :

```python
# Ajouter un média
media_id = media_manager.add_media_to_dive(
    dive_id=123,
    file_path=Path("/path/to/photo.jpg"),
    file_size=1024000,
    description="Belle rencontre avec un requin",
    tags="requin, pélagique"
)

# Récupérer les médias d'une plongée
media_list = media_manager.get_dive_media(dive_id=123)

# Statistiques
stats = media_manager.get_media_stats()
# {'total_media': 42, 'total_photos': 35, 'total_videos': 7, ...}

# Supprimer un média
media_manager.delete_media(media_id=5)
```

### Stockage des fichiers

```
~/dive-analyzer/media/
├── photos/           # Photos originales
├── videos/           # Vidéos
└── thumbnails/       # Miniatures (300x300px)
```

---

## 🐠 Reconnaissance d'Espèces Marines

### Fonctionnalités

- **Catalogue d'espèces** : Base de données extensible avec 10 espèces pré-chargées
- **Reconnaissance IA** : Analyse automatique d'images avec Claude Vision API
- **Détection manuelle** : Ajout manuel d'observations
- **Score de confiance** : Évaluation de la fiabilité des détections IA (0-1)
- **Catégorisation** : Poisson, corail, mollusque, crustacé, échinoderme, mammifère, reptile
- **Conservation** : Statut IUCN (LC, NT, VU, EN, CR)
- **Statistiques** : Espèces les plus observées, répartition par catégorie

### Structure de la base de données

**Table `species`** :
```sql
CREATE TABLE species (
    id INTEGER PRIMARY KEY,
    scientific_name TEXT UNIQUE NOT NULL,
    common_name_fr TEXT,
    common_name_en TEXT,
    category TEXT CHECK(category IN ('poisson', 'corail', 'mollusque', ...)),
    description TEXT,
    conservation_status TEXT,  -- LC, NT, VU, EN, CR
    habitat TEXT,
    depth_range TEXT,
    image_url TEXT,
    created_date TEXT
);
```

**Table `dive_species`** (associations) :
```sql
CREATE TABLE dive_species (
    id INTEGER PRIMARY KEY,
    dive_id INTEGER NOT NULL,
    species_id INTEGER NOT NULL,
    media_id INTEGER,  -- Photo/vidéo de référence
    confidence_score REAL,  -- 0.0 à 1.0
    quantity INTEGER DEFAULT 1,
    notes TEXT,
    detected_by TEXT CHECK(detected_by IN ('ai', 'manual', 'verified')),
    detection_date TEXT,
    FOREIGN KEY (dive_id) REFERENCES dives(id) ON DELETE CASCADE,
    FOREIGN KEY (species_id) REFERENCES species(id),
    FOREIGN KEY (media_id) REFERENCES dive_media(id)
);
```

### Utilisation

#### 1. Reconnaissance automatique (IA)

**Via la page Galerie** :
- Uploadez une photo
- Cochez **🤖 Activer la reconnaissance d'espèces par IA**
- Les espèces détectées avec score > 70% sont ajoutées automatiquement

**Configuration requise** :
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

#### 2. Ajout manuel d'espèces

**Ajouter au catalogue** :
- Page **🐠 Espèces** → Onglet **📚 Catalogue**
- Cliquez sur **➕ Ajouter une nouvelle espèce**
- Remplissez les informations :
  - Nom scientifique (obligatoire)
  - Noms communs FR/EN
  - Catégorie
  - Statut de conservation
  - Habitat, profondeur, description

**Enregistrer une observation** :
- Page **🐠 Espèces** → Onglet **👁️ Observations**
- Sélectionnez une plongée
- Cliquez sur **➕ Ajouter une observation**
- Recherchez l'espèce
- Indiquez quantité et notes

#### 3. Visualiser les espèces

**Par plongée** :
- **📖 Journal** → Sélectionnez une plongée
- Section **🐠 Espèces Observées**
- Affiche : nom, quantité, source de détection (🤖 IA / 👤 Manuel / ✓ Vérifié)

**Statistiques globales** :
- **🐠 Espèces** → Onglet **📊 Statistiques**
- Répartition par catégorie
- Top 10 des espèces les plus observées
- Statistiques par source de détection

### Module Python : `species_recognition.py`

**Fonctions principales** :

```python
# Ajouter une espèce au catalogue
species_id = species_recognition.add_species(
    scientific_name="Amphiprion ocellaris",
    common_name_fr="Poisson-clown à ocelles",
    common_name_en="Clownfish",
    category="poisson",
    conservation_status="LC",
    habitat="Récifs coralliens",
    depth_range="1-12m"
)

# Rechercher une espèce
species = species_recognition.get_species_by_name("Amphiprion ocellaris")
results = species_recognition.search_species("clown", category="poisson")

# Associer une espèce à une plongée
association_id = species_recognition.add_species_to_dive(
    dive_id=123,
    species_id=42,
    quantity=2,
    notes="Couple dans une anémone",
    detected_by='manual'
)

# Récupérer les espèces d'une plongée
dive_species = species_recognition.get_dive_species(dive_id=123)

# Analyse IA d'une image
detections = species_recognition.analyze_image_with_ai(
    image_path=Path("/path/to/photo.jpg")
)
# Retourne : [{'scientific_name': '...', 'confidence': 0.95, ...}]

# Traitement complet (analyse + ajout automatique)
results = species_recognition.process_image_and_add_species(
    image_path=Path("/path/to/photo.jpg"),
    dive_id=123,
    media_id=456,
    auto_add=True,
    confidence_threshold=0.7
)

# Statistiques
stats = species_recognition.get_species_stats()
# {
#     'total_species': 50,
#     'total_observations': 200,
#     'category_stats': {'poisson': 30, 'corail': 15, ...},
#     'top_species': [...]
# }
```

### Reconnaissance IA - Détails techniques

**Modèle utilisé** : Claude 3.5 Sonnet (vision)

**Prompt système** :
- Analyse d'image de plongée sous-marine
- Identification d'espèces marines visibles
- Retour au format JSON structuré

**Réponse JSON** :
```json
{
  "species": [
    {
      "scientific_name": "Amphiprion ocellaris",
      "common_name_fr": "Poisson-clown à ocelles",
      "common_name_en": "Clownfish",
      "category": "poisson",
      "confidence": 0.95
    }
  ]
}
```

**Gestion des résultats** :
- Espèces avec confiance ≥ 70% : ajout automatique
- Espèces avec confiance < 70% : suggestion (ajout manuel requis)
- Nouvelles espèces détectées : ajout automatique au catalogue

---

## 🆕 Pages Streamlit

### 4_📸_Galerie.py

**3 onglets** :

1. **🖼️ Galerie** : Visualisation en grille avec pagination
2. **⬆️ Upload** : Upload de médias avec reconnaissance IA optionnelle
3. **🐠 Espèces** : Stats et recherche rapide

### 5_🐠_Espèces.py

**3 onglets** :

1. **📚 Catalogue** : Recherche et ajout d'espèces
2. **👁️ Observations** : Gestion des observations par plongée
3. **📊 Statistiques** : Graphiques et top espèces

---

## 🔄 Migration de la base de données

### Exécution de la migration

```bash
python database_migration.py
```

**Ce qui est créé** :
- 3 nouvelles tables : `dive_media`, `species`, `dive_species`
- 3 nouveaux index pour optimiser les requêtes
- 10 espèces marines pré-chargées

### Espèces pré-chargées

1. Amphiprion ocellaris (Poisson-clown)
2. Chelonia mydas (Tortue verte)
3. Acropora cervicornis (Corail corne de cerf)
4. Manta birostris (Raie manta géante)
5. Rhincodon typus (Requin-baleine)
6. Octopus vulgaris (Poulpe commun)
7. Pterapogon kauderni (Poisson cardinal de Banggai)
8. Synchiropus splendidus (Poisson-mandarin)
9. Hippocampus sp. (Hippocampe)
10. Physeter macrocephalus (Cachalot)

---

## 🧪 Tests

### Exécuter les tests

```bash
pytest test_species_media.py -v
```

**Couverture** :
- ✅ 16 tests pour `species_recognition.py`
- ✅ 8 tests pour `media_manager.py`
- ✅ 1 test d'intégration

**Tests inclus** :
- Ajout/recherche/suppression d'espèces
- Associations plongées-espèces
- Validation de fichiers média
- Création de miniatures
- Statistiques

---

## 📦 Dépendances supplémentaires

Ajoutez à `requirements.txt` :

```
Pillow>=10.0.0          # Manipulation d'images (miniatures)
anthropic>=0.18.0       # API Claude pour reconnaissance IA (optionnel)
```

Installation :
```bash
pip install Pillow anthropic
```

---

## 🎯 Cas d'usage

### Scénario 1 : Upload après plongée

1. Retour de plongée avec 20 photos
2. **📸 Galerie** → **⬆️ Upload**
3. Sélectionner la plongée du jour
4. Upload des 20 photos avec reconnaissance IA activée
5. L'IA détecte automatiquement : 2 tortues, 5 raies, 1 murène
6. Vérification manuelle et ajout de tags personnalisés

### Scénario 2 : Recherche d'espèce

1. Observation d'un poisson inconnu
2. **🐠 Espèces** → **📚 Catalogue**
3. Recherche par mot-clé : "mandarin"
4. Consultation de la fiche espèce
5. Ajout de l'observation à la plongée

### Scénario 3 : Analyse d'historique

1. **🐠 Espèces** → **📊 Statistiques**
2. Top 10 des espèces observées
3. Répartition par catégorie
4. Identification des sites les plus riches en biodiversité

---

## 🔐 Sécurité

### Validation des fichiers

- ✅ Vérification de l'extension
- ✅ Limite de taille (200 MB)
- ✅ Détection du type MIME
- ✅ Validation des dimensions (images)
- ✅ Sanitization des noms de fichiers

### Gestion des erreurs

- Transactions SQL avec rollback
- Nettoyage automatique en cas d'échec
- Logs détaillés pour le debugging

---

## 📈 Performance

### Optimisations

- **Index de base de données** : 3 nouveaux index sur les clés étrangères
- **Miniatures** : Thumbnails 300x300px pour chargement rapide
- **Cache** : Pas de re-parsing des médias
- **Pagination** : Limite de 50 médias par page

### Stockage

- Photos : ~2-5 MB/photo (JPEG qualité standard)
- Miniatures : ~50-100 KB/thumbnail
- Vidéos : Variable (limite 200 MB/fichier)

---

## 🔮 Évolutions futures

### Améliorations possibles

1. **IA améliorée**
   - Support de modèles locaux (YOLOv8, etc.)
   - Fine-tuning sur espèces spécifiques
   - Détection de comportements

2. **Fonctionnalités médias**
   - Édition d'images (rotation, crop)
   - Extraction de frames de vidéos
   - Géolocalisation via EXIF

3. **Espèces**
   - Import de catalogues externes (FishBase, WoRMS)
   - Graphiques de répartition géographique
   - Alertes pour espèces rares/protégées

4. **Partage**
   - Export de galeries photo
   - Rapport PDF avec espèces observées
   - Intégration avec réseaux sociaux

---

## 📞 Support

Pour toute question ou problème :

1. Consultez les logs : `~/dive-analyzer/dive_analyzer.log`
2. Vérifiez la documentation : `CODEBASE_OVERVIEW.md`
3. Lancez les tests : `pytest test_species_media.py -v`
4. Créez une issue sur GitHub

---

**Version** : 1.0.0
**Date** : Novembre 2024
**Auteur** : Claude Code
