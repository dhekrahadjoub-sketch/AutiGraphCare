# data/generate_dataset.py

import pandas as pd
import numpy as np
import random

print("🚀 GÉNÉRATION DU DATASET TSA AVEC 5 INTERVENTIONS...")

np.random.seed(42)
random.seed(42)
NOMBRE_ENFANTS = 150

data = []

for i in range(NOMBRE_ENFANTS):
    id_patient = f'P{str(i+1).zfill(4)}'
    age_mois = random.randint(24, 144)
    sexe = random.choice(['M', 'F'])
    age_diagnostic = random.randint(24, 72)
    
    # Score de sévérité de base
    base_score = np.random.normal(5.5, 1.8)
    base_score = np.clip(base_score, 1, 10)
    
    # Scores cliniques (1-10)
    communication_sociale = np.clip(base_score + np.random.normal(0, 1), 1, 10)
    interactions_sociales = np.clip(base_score + np.random.normal(0, 1.2), 1, 10)
    comportements_restreints = np.clip(base_score * 0.9 + np.random.normal(0, 1), 1, 10)
    langage_expressif = np.clip(base_score * 0.85 + np.random.normal(0, 1.3), 1, 10)
    langage_receptif = np.clip(base_score * 0.8 + np.random.normal(0, 1.2), 1, 10)
    contact_visuel = np.clip(base_score * 0.7 + np.random.normal(0, 1.5), 1, 10)
    imitation = np.clip(base_score * 0.75 + np.random.normal(0, 1.4), 1, 10)
    jeu_symbolique = np.clip(base_score * 0.65 + np.random.normal(0, 1.6), 1, 10)
    
    # Comorbidités (0/1)
    tdah = 1 if random.random() < 0.25 else 0
    anxiete = 1 if random.random() < 0.2 else 0
    trouble_sommeil = 1 if random.random() < 0.2 else 0
    
    # INTERVENTIONS - 5 types avec conditions cliniques
    orthophonie = 1 if (age_mois > 30 or base_score > 5 or langage_expressif < 5) else 0
    psychomotricite = 1 if (base_score > 5 or imitation < 5) else 0
    aba = 1 if (base_score > 6 or comportements_restreints > 6) else 0
    teacch = 1 if (base_score > 4 and age_mois > 48 and random.random() < 0.4) else 0
    pecs = 1 if (langage_expressif < 5 and communication_sociale > 5 and random.random() < 0.5) else 0
    
    # Ajouter un peu d'aléatoire
    if random.random() < 0.2:
        orthophonie = 1
    if random.random() < 0.15:
        psychomotricite = 1
    if random.random() < 0.1:
        aba = 1
    if random.random() < 0.1:
        teacch = 1
    if random.random() < 0.1:
        pecs = 1
    
    data.append([
        id_patient, age_mois, sexe, age_diagnostic,
        round(communication_sociale, 1), round(interactions_sociales, 1),
        round(comportements_restreints, 1), round(langage_expressif, 1),
        round(langage_receptif, 1), round(contact_visuel, 1),
        round(imitation, 1), round(jeu_symbolique, 1),
        tdah, anxiete, trouble_sommeil,
        orthophonie, psychomotricite, aba, teacch, pecs
    ])

columns = [
    'id_patient', 'age_mois', 'sexe', 'age_diagnostic',
    'communication_sociale', 'interactions_sociales', 'comportements_restreints',
    'langage_expressif', 'langage_receptif', 'contact_visuel',
    'imitation', 'jeu_symbolique',
    'tdah', 'anxiete', 'trouble_sommeil',
    'orthophonie', 'psychomotricite', 'aba', 'teacch', 'pecs'
]

df = pd.DataFrame(data, columns=columns)

# Forcer le type entier pour toutes les colonnes binaires
for col in ['orthophonie', 'psychomotricite', 'aba', 'teacch', 'pecs',
            'tdah', 'anxiete', 'trouble_sommeil']:
    df[col] = df[col].astype(int)

# Ajout de données manquantes (5%) pour tester la robustesse
for col in ['communication_sociale', 'langage_expressif', 'contact_visuel']:
    idx = np.random.choice(df.index, size=int(len(df)*0.05), replace=False)
    df.loc[idx, col] = np.nan

# Sauvegarde
df.to_csv('data/dataset_tsa_complet.csv', index=False)

print("✅ Dataset créé avec SUCCÈS!")
print(f"📊 Nombre de patients: {len(df)}")
print(f"📁 Fichier: data/dataset_tsa_complet.csv")
print(f"\n📈 STATISTIQUES DES INTERVENTIONS:")
print(f"   Orthophonie:    {df['orthophonie'].sum():3d} patients ({df['orthophonie'].mean()*100:.0f}%)")
print(f"   Psychomotricité: {df['psychomotricite'].sum():3d} patients ({df['psychomotricite'].mean()*100:.0f}%)")
print(f"   ABA:            {df['aba'].sum():3d} patients ({df['aba'].mean()*100:.0f}%)")
print(f"   TEACCH:         {df['teacch'].sum():3d} patients ({df['teacch'].mean()*100:.0f}%)")
print(f"   PECS:           {df['pecs'].sum():3d} patients ({df['pecs'].mean()*100:.0f}%)")
print(f"\n🎯 Aperçu des 3 premiers patients:")
print(df[['id_patient', 'orthophonie', 'psychomotricite', 'aba', 'teacch', 'pecs']].head(3))
