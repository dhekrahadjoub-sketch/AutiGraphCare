# pages/03_Recommandations.py

import streamlit as st
import pandas as pd
import plotly.express as px
from components.recommender import RecommenderSystem

st.set_page_config(page_title="Recommandations IA", layout="wide")

st.markdown("""
<div class='main-header'>
    <h1 style='color: white;'>🤖 Recommandations Personnalisées</h1>
    <p style='color: white;'>IA robuste basée sur l'analyse de profils similaires</p>
</div>
""", unsafe_allow_html=True)

# Chargement des données
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/dataset_tsa_complet.csv')
        return df
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("❌ Données non trouvées")
    st.stop()

# Initialisation du système de recommandation
@st.cache_resource
def init_recommender():
    recommender = RecommenderSystem()
    recommender.fit(df)
    return recommender

recommender = init_recommender()

# Interface principale
col1, col2 = st.columns([1, 1.5])

with col1:
    st.markdown("### 🎯 Sélection du patient")
    
    # Sélection patient
    patient_id = st.selectbox(
        "Choisir un patient",
        df['id_patient'].values,
        key="rec_patient_select"
    )
    
    if patient_id:
        patient = df[df['id_patient'] == patient_id].iloc[0]
        
        # Carte patient
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
        st.markdown(f"### 👤 Patient {patient_id}")
        
        col_age, col_sex = st.columns(2)
        with col_age:
            st.metric("Âge", f"{patient['age_mois']} mois")
        with col_sex:
            st.metric("Sexe", patient['sexe'])
        
        # Scores rapides
        st.markdown("#### 📊 Scores cliniques")
        scores = {
            "Communication": patient['communication_sociale'],
            "Interactions": patient['interactions_sociales'],
            "Comportements": patient['comportements_restreints']
        }
        
        for label, score in scores.items():
            if not pd.isna(score):
                couleur = "🔴" if score >= 7 else "🟠" if score >= 4 else "🟢"
                st.markdown(f"{couleur} **{label}:** {score}/10")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Patients similaires
        st.markdown("### 👥 Patients similaires")
        similar = recommender.get_similar_patients(patient_id)
        
        if similar:
            for i, p in enumerate(similar, 1):
                st.info(f"**{p['id']}** - Similarité: {p['similarite']}")
        else:
            st.info("Aucun patient similaire trouvé")

with col2:
    if patient_id:
        st.markdown("### 💡 Recommandations IA")
        
        # Obtenir les recommandations
        recommendations = recommender.recommend_interventions(patient_id)
        
        if not recommendations.empty:
            # Afficher les recommandations par priorité
            for _, rec in recommendations.iterrows():
                # Choisir la couleur selon la priorité
                if rec['priorite'] == "Haute":
                    color = "#4CAF50"  # Vert
                    icon = "🔴"  # Rouge pour attirer l'attention
                elif rec['priorite'] == "Moyenne":
                    color = "#FFA500"  # Orange
                    icon = "🟠"
                else:
                    color = "#4A90E2"  # Bleu
                    icon = "🔵"
                
                # Nom d'affichage de l'intervention
                interv_names = {
                    'orthophonie': 'Orthophonie',
                    'psychomotricite': 'Psychomotricité',
                    'aba': 'ABA (Analyse Appliquée du Comportement)',
                    'teacch': 'TEACCH',
                    'pecs': 'PECS (Communication par images)'
                }
                
                interv_name = interv_names.get(rec['intervention'], rec['intervention'])
                
                # Carte de recommandation
                st.markdown(f"""
                <div style='background: white; padding: 1.5rem; border-radius: 10px; 
                        border-left: 5px solid {color}; margin-bottom: 1rem;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                    <div style='display: flex; justify-content: space-between;'>
                        <h3 style='margin: 0; color: {color};'>{icon} {interv_name}</h3>
                        <span style='background: {color}; color: white; padding: 0.3rem 0.8rem; 
                                border-radius: 20px; font-weight: bold;'>
                            {rec['priorite']}
                        </span>
                    </div>
                    <p style='font-size: 1.2rem; margin: 0.5rem 0;'>
                        Confiance: <strong>{rec['confiance']}</strong>
                    </p>
                    <p style='color: #666;'>
                        Basé sur {rec['patients_similaires']} patient(s) similaire(s)
                    </p>
                    <details>
                        <summary style='color: {color}; cursor: pointer;'>🔍 Voir l'explication détaillée</summary>
                        <div style='background: #f8f9fa; padding: 1rem; border-radius: 5px; margin-top: 0.5rem;'>
                """, unsafe_allow_html=True)
                
                # Explication détaillée
                explanation = recommender.explain_recommendation(patient_id, rec['intervention'])
                st.markdown(explanation)
                
                st.markdown("</div></details></div>", unsafe_allow_html=True)
            
            # Graphique de confiance
            st.markdown("### 📊 Niveaux de confiance")
            fig = px.bar(recommendations, 
                        x='intervention', 
                        y=[float(c.strip('%')) for c in recommendations['confiance']],
                        title="Score de confiance par intervention",
                        labels={'x': 'Intervention', 'y': 'Confiance (%)'},
                        color='priorite',
                        color_discrete_map={'Haute': '#4CAF50', 'Moyenne': '#FFA500', 'Faible': '#4A90E2'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("⚠️ Aucune recommandation disponible pour ce patient")
            
            # Recommandations par défaut basées sur les règles
            st.markdown("### 📋 Recommandations basées sur les règles cliniques")
            
            patient = df[df['id_patient'] == patient_id].iloc[0]
            
            if not pd.isna(patient['communication_sociale']) and patient['communication_sociale'] > 6:
                st.success("**Orthophonie** - Score de communication élevé")
            
            if not pd.isna(patient['comportements_restreints']) and patient['comportements_restreints'] > 5:
                st.success("**ABA** - Comportements restreints significatifs")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🤖 Les recommandations sont basées sur l'analyse de patients aux profils similaires + règles cliniques</p>
    <p style='font-size: 0.8rem;'>Confiance: Plus le score est élevé, plus la recommandation est robuste</p>
</div>
""", unsafe_allow_html=True)