# pages/02_Knowledge_Graph.py

import streamlit as st
import pandas as pd
from components.kg_builder import KnowledgeGraphBuilder
import streamlit.components.v1 as components
import tempfile
import os

st.set_page_config(page_title="Knowledge Graph TSA", layout="wide")

st.markdown("""
<div class='main-header'>
    <h1 style='color: white;'>🕸️ Knowledge Graph Dynamique</h1>
    <p style='color: white;'>Visualisation des relations patients - symptômes - interventions</p>
</div>
""", unsafe_allow_html=True)

# Initialisation
@st.cache_resource
def init_kg():
    return KnowledgeGraphBuilder()

kg = init_kg()

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
    st.error("❌ Données non trouvées. Vérifie que le dataset est généré.")
    st.stop()

kg.load_data(df)

# Interface principale
tab1, tab2, tab3 = st.tabs(["👤 Patient unique", "🔄 Comparaison", "📊 Statistiques KG"])

with tab1:
    st.markdown("### 👤 Visualisation d'un patient")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        patient_id = st.selectbox(
            "Choisir un patient",
            df['id_patient'].values,
            key="kg_patient_select"
        )
        
        if patient_id:
            patient = df[df['id_patient'] == patient_id].iloc[0]
            
            st.markdown("#### 📋 Informations patient")
            st.write(f"**Âge:** {patient['age_mois']} mois ({patient['age_mois']//12} ans)")
            st.write(f"**Sexe:** {patient['sexe']}")
            
            st.markdown("#### 🎯 Scores")
            scores = {
                "Communication": patient['communication_sociale'],
                "Interactions": patient['interactions_sociales'],
                "Comportements": patient['comportements_restreints']
            }
            
            for label, score in scores.items():
                if not pd.isna(score):
                    if score >= 7:
                        couleur = "🔴 Sévère"
                    elif score >= 4:
                        couleur = "🟠 Modéré"
                    else:
                        couleur = "🟢 Léger"
                    st.write(f"{label}: {score}/10 - {couleur}")
    
    with col2:
        if patient_id:
            st.markdown("#### 🕸️ Graphe des connaissances")
            
            try:
                net = kg.visualize(patient_id=patient_id)
                
                if net:
                    # Sauvegarde dans un fichier temporaire
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                        net.save_graph(f.name)
                        f.flush()
                        
                        # Lire le fichier HTML
                        with open(f.name, 'r', encoding='utf-8') as html_file:
                            html_content = html_file.read()
                        
                        # Afficher
                        components.html(html_content, height=600, width='stretch')
                    
                    # Nettoyer
                    try:
                        os.unlink(f.name)
                    except:
                        pass
                    
                    st.caption("💡 Astuce: Tu peux zoomer, déplacer les noeuds, et survoler pour plus d'infos")
                else:
                    st.error("Impossible de générer le graphe")
                    
            except Exception as e:
                st.error(f"Erreur de visualisation: {str(e)}")

with tab2:
    st.markdown("### 🔄 Comparaison de patients")
    
    patients_list = df['id_patient'].values
    selected_patients = st.multiselect(
        "Choisir 2-3 patients à comparer",
        patients_list,
        default=patients_list[:2] if len(patients_list) >= 2 else [],
        max_selections=3
    )
    
    if len(selected_patients) >= 2:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 🕸️ Graphe comparatif")
            try:
                net = kg.visualize(patient_ids=selected_patients)
                
                if net:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                        net.save_graph(f.name)
                        f.flush()
                        
                        with open(f.name, 'r', encoding='utf-8') as html_file:
                            html_content = html_file.read()
                        
                        components.html(html_content, height=500, width='stretch')
                    
                    try:
                        os.unlink(f.name)
                    except:
                        pass
                else:
                    st.error("Impossible de générer le graphe")
                    
            except Exception as e:
                st.error(f"Erreur: {str(e)}")
        
        with col2:
            st.markdown("#### 📊 Points communs")
            patients_data = df[df['id_patient'].isin(selected_patients)]
            
            st.write("**Interventions partagées:**")
            interv_communes = []
            if all(patients_data['orthophonie'] == 1):
                interv_communes.append("Orthophonie")
            if all(patients_data['psychomotricite'] == 1):
                interv_communes.append("Psychomotricité")
            if all(patients_data['aba'] == 1):
                interv_communes.append("ABA")
            
            if interv_communes:
                for i in interv_communes:
                    st.write(f"✅ {i}")
            else:
                st.write("❌ Aucune")
    else:
        st.info("👆 Sélectionne au moins 2 patients pour la comparaison")

with tab3:
    st.markdown("### 📊 Statistiques du Knowledge Graph")
    
    col1, col2, col3, col4 = st.columns(4)
    
    n_patients = len(df)
    
    # Compter les interventions
    count_ortho = (df['orthophonie'] == 1).sum()
    count_psycho = (df['psychomotricite'] == 1).sum()
    count_aba = (df['aba'] == 1).sum()
    
    n_interventions = int(count_ortho + count_psycho + count_aba)
    
    with col1:
        st.metric("👤 Patients", n_patients)
    with col2:
        st.metric("📊 Relations", n_patients * 8)
    with col3:
        st.metric("💊 Interventions", n_interventions)
    with col4:
        st.metric("🎯 Symptômes", 6)
    
    # Distribution des scores
    st.markdown("#### 📈 Distribution des scores cliniques")
    
    scores_df = df[['communication_sociale', 'interactions_sociales', 'comportements_restreints']].copy()
    scores_long = scores_df.melt(var_name='Symptôme', value_name='Score')
    scores_long = scores_long.dropna()
    
    nom_symptomes = {
        'communication_sociale': 'Communication',
        'interactions_sociales': 'Interactions',
        'comportements_restreints': 'Comportements'
    }
    scores_long['Symptôme'] = scores_long['Symptôme'].map(nom_symptomes)
    
    if not scores_long.empty:
        import plotly.express as px
        fig = px.box(scores_long, x='Symptôme', y='Score', 
                     title='Distribution des scores par symptôme',
                     color='Symptôme',
                     color_discrete_sequence=['#4A90E2', '#50E3C2', '#F5A623'])
        fig.update_layout(showlegend=False, plot_bgcolor='white', paper_bgcolor='white')
        fig.update_yaxes(range=[0, 10])
        st.plotly_chart(fig, width='stretch')

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🕸️ Légende: 🟦 Patient | 🟠 Symptôme | 🟢 Intervention | 🔴 Comorbidité</p>
</div>
""", unsafe_allow_html=True)