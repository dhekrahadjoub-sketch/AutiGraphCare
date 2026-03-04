# components/recommender.py

import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import streamlit as st

pd.set_option('future.no_silent_downcasting', True)

class RecommenderSystem:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.df = None
        self.feature_cols = []
    
    def fit(self, df):
        """Entraîne le système de recommandation"""
        self.df = df
        
        # Sélection des features numériques
        self.feature_cols = [
            'communication_sociale', 'interactions_sociales',
            'comportements_restreints', 'langage_expressif',
            'langage_receptif', 'contact_visuel', 'imitation', 'jeu_symbolique'
        ]
        
        # Ne garder que les colonnes existantes
        self.feature_cols = [col for col in self.feature_cols if col in df.columns]
        
        # Préparer les données
        X = df[self.feature_cols].copy()
        X = X.fillna(X.mean())  # Remplacer les NaN par la moyenne
        
        # Standardiser
        X_scaled = self.scaler.fit_transform(X.values)
        
        # Entraîner le modèle KNN
        self.model = NearestNeighbors(n_neighbors=5, metric='euclidean')
        self.model.fit(X_scaled)
        
        return self
    
    def get_similar_patients(self, patient_id, n_neighbors=5):
        """Trouve les patients similaires"""
        if self.model is None or self.df is None:
            return []
        
        # Trouver l'index du patient
        patient_idx = self.df[self.df['id_patient'] == patient_id].index[0]
        
        # Préparer ses features
        patient_features = self.df.loc[patient_idx, self.feature_cols].fillna(
            self.df[self.feature_cols].mean()
        ).values.reshape(1, -1)
        
        # Standardiser
        patient_scaled = self.scaler.transform(patient_features)
        
        # Trouver les voisins
        distances, indices = self.model.kneighbors(patient_scaled, n_neighbors=n_neighbors+1)
        
        # Retourner les patients similaires (sans le patient lui-même)
        similar_patients = []
        for i, idx in enumerate(indices[0]):
            if idx != patient_idx:
                similar_patients.append({
                    'id': self.df.iloc[idx]['id_patient'],
                    'distance': distances[0][i],
                    'similarite': f"{100 - distances[0][i]*10:.0f}%"
                })
        
        return similar_patients[:n_neighbors]
    
    def recommend_interventions(self, patient_id):
        """Recommande des interventions basées sur les patients similaires"""
        if self.model is None:
            return pd.DataFrame()
        
        # Trouver les patients similaires
        similar_patients = self.get_similar_patients(patient_id, n_neighbors=5)
        
        if not similar_patients:
            return pd.DataFrame()
        
        # Interventions disponibles (5 types)
        interventions = ['orthophonie', 'psychomotricite', 'aba', 'teacch', 'pecs']
        
        # Analyser les interventions des patients similaires
        recommendations = []
        
        for interv in interventions:
            # Vérifier si la colonne existe
            if interv not in self.df.columns:
                continue
                
            # Compter combien de patients similaires ont cette intervention
            count = 0
            patients_avec_intervention = []
            
            for sp in similar_patients:
                patient = self.df[self.df['id_patient'] == sp['id']].iloc[0]
                try:
                    if patient[interv] == 1:
                        count += 1
                        patients_avec_intervention.append(sp['id'])
                except:
                    continue
            
            # Calculer le score de confiance
            if count > 0:
                confiance = (count / len(similar_patients)) * 100
                
                # Déterminer la priorité
                if confiance >= 80:
                    priorite = "Haute"
                elif confiance >= 50:
                    priorite = "Moyenne"
                else:
                    priorite = "Faible"
                
                recommendations.append({
                    'intervention': interv,
                    'confiance': f"{confiance:.0f}%",
                    'priorite': priorite,
                    'patients_similaires': count,
                    'exemples': ', '.join(patients_avec_intervention[:2])
                })
        
        # Trier par confiance
        df_rec = pd.DataFrame(recommendations)
        if not df_rec.empty:
            df_rec = df_rec.sort_values('confiance', ascending=False)
        
        return df_rec
    
    def explain_recommendation(self, patient_id, intervention):
        """Génère une explication détaillée pour une recommandation"""
        similar_patients = self.get_similar_patients(patient_id, n_neighbors=5)
        patient = self.df[self.df['id_patient'] == patient_id].iloc[0]
        
        # Base de connaissances avec 5 interventions
        expert_knowledge = {
            'orthophonie': {
                'nom': 'Orthophonie',
                'indications': ['Troubles du langage', 'Difficultés de communication'],
                'seuil': 5.5,
                'benefices': ['Amélioration du langage expressif', 'Meilleure communication sociale']
            },
            'psychomotricite': {
                'nom': 'Psychomotricité',
                'indications': ['Difficultés motrices', "Troubles de l'imitation"],
                'seuil': 4.5,
                'benefices': ['Meilleure coordination', 'Intégration sensorielle']
            },
            'aba': {
                'nom': 'ABA',
                'indications': ['Comportements restreints', 'Autisme sévère'],
                'seuil': 6.0,
                'benefices': ['Réduction des comportements problématiques', 'Apprentissage structuré']
            },
            'teacch': {
                'nom': 'TEACCH',
                'indications': ["Troubles de l'organisation", 'Besoin de structure'],
                'seuil': 4.0,
                'benefices': ['Autonomie', 'Organisation visuelle', 'Routines']
            },
            'pecs': {
                'nom': 'PECS',
                'indications': ['Langage expressif très faible', 'Communication non-verbale'],
                'seuil': 3.5,
                'benefices': ['Communication par images', 'Réduction frustration', 'Initiation communication']
            }
        }
        
        # Vérifier si l'intervention est dans notre base
        if intervention not in expert_knowledge:
            return f"### 🧠 Pourquoi recommander **{intervention}** ?\n\nDonnées insuffisantes pour une explication détaillée."
        
        # Construire l'explication
        expert = expert_knowledge[intervention]
        explanation = f"### 🧠 Pourquoi recommander **{expert['nom']}** ?\n\n"
        
        # 1. RAISON CLINIQUE
        explanation += f"**🔬 Indications cliniques :**\n"
        for ind in expert['indications']:
            explanation += f"- {ind}\n"
        
        # Score du patient
        if intervention == 'orthophonie':
            score_col = 'langage_expressif'
        elif intervention == 'psychomotricite':
            score_col = 'imitation'
        elif intervention == 'aba':
            score_col = 'comportements_restreints'
        elif intervention == 'teacch':
            score_col = 'jeu_symbolique'
        elif intervention == 'pecs':
            score_col = 'langage_expressif'
        else:
            score_col = None
        
        if score_col and score_col in patient.index and not pd.isna(patient[score_col]):
            score = patient[score_col]
            seuil = expert['seuil']
            
            if score >= seuil:
                explanation += f"\n**📊 Score patient :** {score:.1f}/10 (au-dessus du seuil de {seuil}/10)\n"
            else:
                explanation += f"\n**📊 Score patient :** {score:.1f}/10 (préventif, seuil à {seuil}/10)\n"
        
        # 2. PREUVES PAR SIMILARITÉ
        explanation += f"\n**👥 Preuves par similarité :**\n"
        
        patients_avec = []
        for sp in similar_patients:
            p = self.df[self.df['id_patient'] == sp['id']].iloc[0]
            try:
                if p[intervention] == 1:
                    patients_avec.append(sp['id'])
            except:
                continue
        
        if patients_avec:
            explanation += f"- {len(patients_avec)}/5 patients similaires bénéficient de cette intervention\n"
            for pid in patients_avec[:2]:
                p = self.df[self.df['id_patient'] == pid].iloc[0]
                age = p['age_mois'] // 12
                explanation += f"  - {pid} ({age} ans) - Amélioration documentée\n"
        else:
            explanation += f"- Aucun patient similaire avec cette intervention\n"
        
        # 3. BÉNÉFICES ATTENDUS
        explanation += f"\n**✨ Bénéfices attendus :**\n"
        for b in expert['benefices']:
            explanation += f"- {b}\n"
        
        # 4. RECOMMANDATION FINALE
        explanation += f"\n**💡 Conclusion :** "
        if len(patients_avec) >= 3:
            explanation += f"Recommandation FORTE basée sur {len(patients_avec)} profils similaires"
        elif len(patients_avec) >= 1:
            explanation += f"Recommandation MODÉRÉE, quelques profils similaires"
        else:
            explanation += f"Recommandation EXPLORATOIRE, basée sur les critères cliniques"
        
        return explanation
