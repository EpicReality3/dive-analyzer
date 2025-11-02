# 🔬 Physique Avancée de Décompression

## Vue d'ensemble

Cette fonctionnalité ajoute des calculs de physique de décompression avancés à l'analyseur de plongée, basés sur le modèle de Haldane simplifié.

## Fonctionnalités implémentées

### 1. Pressions Partielles (PP)

**Fonction:** `calculate_partial_pressures(df, fO2=0.21, fN2=0.79)`

Calcule les pressions partielles d'oxygène (O₂) et d'azote (N₂) à chaque point du profil.

**Formule:**
```
PP_gaz = Fraction_gaz × P_absolue
où P_absolue = (Profondeur/10 + 1) bar
```

**Sorties:**
- `pression_absolue`: Pression absolue en bar
- `PP_O2`: Pression partielle d'oxygène en bar
- `PP_N2`: Pression partielle d'azote en bar

**Exemple:**
- À 30m de profondeur avec de l'air (21% O₂, 79% N₂):
  - P_absolue = 4 bar
  - PP_O2 = 0.84 bar
  - PP_N2 = 3.16 bar

### 2. Saturation Tissulaire

**Fonction:** `calculate_tissue_saturation(df, compartment_half_time=40.0)`

Modélise l'absorption et la désorption d'azote dans les tissus corporels selon le modèle de Haldane.

**Modèle:**
- Utilise UN SEUL compartiment tissulaire avec demi-vie de 40 minutes (compartiment "moyen")
- Le modèle Bühlmann complet utilise 16 compartiments (demi-vies de 2.5 à 635 min)

**Équation de Haldane:**
```
P_tissue(t) = P_alv + (P_tissue(t-1) - P_alv) × e^(-k×Δt)
où k = ln(2) / demi-vie
```

**Sorties:**
- `tissue_N2_pressure`: Pression d'azote dans le tissu (bar)
- `N2_gradient`: Différence entre pression tissulaire et ambiante (bar)
  - Gradient positif = sursaturation (risque de formation de bulles)

### 3. Azote Résiduel Post-Plongée

**Fonction:** `calculate_residual_nitrogen(df, compartment_half_time=40.0)`

Calcule l'azote résiduel après la plongée et recommande un intervalle de surface.

**Métriques retournées:**
- `residual_N2_pressure`: Pression N₂ résiduelle en surface (bar)
- `residual_percentage`: Sursaturation par rapport à la normale (%)
- `recommended_surface_interval_min`: Intervalle recommandé (3 × demi-vie = 120 min)
- `time_to_90_percent_desaturation_min`: Temps pour revenir à 90% de la normale

### 4. Résumé Physique Complet

**Fonction:** `get_advanced_physics_summary(df)`

Génère un résumé complet avec toutes les métriques physiques.

**Retourne:**
- `df_enriched`: DataFrame avec toutes les colonnes calculées
- `max_tissue_N2_pressure`: Pression tissulaire maximale + timestamp
- `max_N2_gradient`: Gradient maximal + timestamp
- `residual_nitrogen`: Dictionnaire complet de l'azote résiduel

## Interface Utilisateur (Streamlit)

La section "🔬 Physique Avancée de Décompression" affiche:

### Saturation Tissulaire (🧬)
- Pression N₂ max dans le tissu (bar) avec timestamp
- Gradient N₂ max (bar) avec timestamp

### Azote Résiduel Post-Plongée (💨)
- Sursaturation résiduelle (%)
- Intervalle de surface recommandé (min)
- Temps de désaturation à 90% (min)

### Graphique Interactif (📈)
Dans un expander, affiche l'évolution temporelle de:
- PP_N2 alvéolaire (ambiant) - ligne bleue
- Pression N₂ tissulaire - ligne rouge pointillée

## Exemple de Résultats

Pour une plongée à 30m pendant 20 minutes:

```
📊 Saturation Tissulaire
   Pression N₂ max : 1.70 bar (à 36.0 min)
   Gradient N₂ max : 0.84 bar (à 39.8 min)

💨 Azote Résiduel
   Sursaturation : 111.8%
   Intervalle recommandé : 120 min
   Temps retour à 90% : 139 min
```

## Limitations et Avertissements

⚠️ **IMPORTANT:** Ce modèle est PÉDAGOGIQUE uniquement.

- Utilise UN SEUL compartiment (vs 16 dans Bühlmann)
- Demi-vie fixe de 40 minutes (compartiment "moyen")
- Ne remplace PAS un ordinateur de plongée
- NE PAS utiliser pour planifier des plongées réelles

## Tests

Un script de test est fourni: `test_physics.py`

Exécution:
```bash
source venv/bin/activate
python3 test_physics.py
```

Validations effectuées:
- PP_N2 dans la plage attendue (0.79-4 bar)
- Pression tissulaire initiale = 0.79 bar (surface)
- Augmentation pendant la descente
- Sursaturation résiduelle positive

## Références Théoriques

1. **Modèle de Haldane:** Absorption/désorption exponentielle de gaz inertes
2. **Équation de décompression:** P(t) = P₀ + (P_alv - P₀) × (1 - e^(-kt))
3. **Demi-vie (half-time):** Temps pour atteindre 50% de la nouvelle pression d'équilibre
4. **Gradient:** Différence entre pression tissulaire et ambiante (risque de bulles)

## Fichiers Modifiés

- `analyzer.py`: Nouvelles fonctions de calcul physique
- `app.py`: Nouvelle section UI "Physique Avancée"
- `test_physics.py`: Script de validation
- `PHYSIQUE_AVANCEE.md`: Cette documentation

## Auteur

Implémenté le 2025-11-02
