"""
Script de test pour les fonctions de physique avancée
"""

import pandas as pd
import numpy as np
import analyzer

# Créer un profil de plongée simulé
# Descente à 30m, palier, remontée
temps = []
profondeur = []

# Descente progressive (0 à 10 min -> 0 à 30m)
for t in range(0, 600, 10):
    temps.append(t)
    profondeur.append(min(t / 20, 30))  # Descente progressive

# Phase de fond (10 à 30 min -> 30m constant)
for t in range(600, 1800, 10):
    temps.append(t)
    profondeur.append(30)

# Remontée progressive (30 à 40 min -> 30m à 0m)
for t in range(1800, 2400, 10):
    temps.append(t)
    profondeur.append(30 - (t - 1800) / 20)

df = pd.DataFrame({
    'temps_secondes': temps,
    'profondeur_metres': profondeur
})

print("🧪 Test des fonctions de physique avancée\n")
print(f"📊 Profil de plongée : {len(df)} points")
print(f"⏱️ Durée totale : {df['temps_secondes'].max() / 60:.1f} min")
print(f"⬇️ Profondeur max : {df['profondeur_metres'].max():.1f} m\n")

# Test 1: Pressions partielles
print("=" * 60)
print("Test 1: Calcul des pressions partielles")
print("=" * 60)
df_pp = analyzer.calculate_partial_pressures(df)
print(f"✅ Colonnes ajoutées : {[col for col in df_pp.columns if col not in df.columns]}")
print(f"   PP_O2 max : {df_pp['PP_O2'].max():.3f} bar")
print(f"   PP_N2 max : {df_pp['PP_N2'].max():.3f} bar")
print()

# Test 2: Saturation tissulaire
print("=" * 60)
print("Test 2: Calcul de la saturation tissulaire")
print("=" * 60)
df_sat = analyzer.calculate_tissue_saturation(df)
print(f"✅ Colonnes ajoutées : {[col for col in df_sat.columns if col not in df.columns]}")
print(f"   Pression N2 tissulaire initiale : {df_sat['tissue_N2_pressure'].iloc[0]:.3f} bar")
print(f"   Pression N2 tissulaire max : {df_sat['tissue_N2_pressure'].max():.3f} bar")
print(f"   Gradient N2 max : {df_sat['N2_gradient'].max():.3f} bar")
print()

# Test 3: Azote résiduel
print("=" * 60)
print("Test 3: Calcul de l'azote résiduel")
print("=" * 60)
residual = analyzer.calculate_residual_nitrogen(df)
print(f"✅ Résultats :")
print(f"   Pression N2 résiduelle : {residual['residual_N2_pressure']:.3f} bar")
print(f"   Sursaturation : {residual['residual_percentage']:.1f}%")
print(f"   Intervalle de surface recommandé : {residual['recommended_surface_interval_min']:.0f} min")
print(f"   Temps retour à 90% normal : {residual['time_to_90_percent_desaturation_min']:.0f} min")
print()

# Test 4: Résumé complet
print("=" * 60)
print("Test 4: Résumé physique complet")
print("=" * 60)
physics = analyzer.get_advanced_physics_summary(df)
print(f"✅ Clés du dictionnaire : {list(physics.keys())}")
print(f"   Pression N2 tissulaire max : {physics['max_tissue_N2_pressure']:.3f} bar à {physics['max_tissue_N2_time']:.1f} min")
print(f"   Gradient N2 max : {physics['max_N2_gradient']:.3f} bar à {physics['max_N2_gradient_time']:.1f} min")
print()

# Validation des résultats
print("=" * 60)
print("🔬 Validation des résultats")
print("=" * 60)

validations = []

# PP_N2 doit être entre 0.79 (surface) et ~4 bar (30m)
pp_n2_ok = 0.79 <= df_pp['PP_N2'].min() <= 1.0 and 3.0 <= df_pp['PP_N2'].max() <= 4.0
validations.append(("PP_N2 dans plage attendue (0.79-4 bar)", pp_n2_ok))

# Pression tissulaire doit commencer à 0.79
tissue_start_ok = abs(df_sat['tissue_N2_pressure'].iloc[0] - 0.79) < 0.01
validations.append(("Pression tissulaire initiale = 0.79 bar", tissue_start_ok))

# La pression tissulaire doit augmenter pendant la descente
tissue_increases = df_sat['tissue_N2_pressure'].iloc[100] > df_sat['tissue_N2_pressure'].iloc[0]
validations.append(("Pression tissulaire augmente pendant descente", tissue_increases))

# Azote résiduel positif
residual_positive = residual['residual_percentage'] > 0
validations.append(("Sursaturation résiduelle positive", residual_positive))

# Afficher les validations
for test, passed in validations:
    status = "✅" if passed else "❌"
    print(f"{status} {test}")

all_passed = all(passed for _, passed in validations)
print()
if all_passed:
    print("🎉 Tous les tests sont passés avec succès !")
else:
    print("⚠️ Certains tests ont échoué")

print()
print("=" * 60)
print("✅ Tests terminés")
print("=" * 60)
