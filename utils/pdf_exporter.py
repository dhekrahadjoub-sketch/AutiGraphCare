# utils/pdf_exporter.py

import pandas as pd
import streamlit as st
from datetime import datetime
import tempfile
import os

# Correction du conflit PyFPDF/fpdf2
try:
    from fpdf import FPDF  # fpdf2
except ImportError:
    from fpdf import FPDF  # fallback

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(74, 144, 226)  # #4A90E2
        self.cell(0, 10, '🧠 AutiGraphCare', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Rapport patient - IA robuste pour TSA', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} - Généré le {datetime.now().strftime("%d/%m/%Y")}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(74, 144, 226)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)
    
    def section_body(self, text):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, text)
        self.ln(5)

def export_patient_pdf(patient_data, patient_id):
    """Exporte le profil patient en PDF"""
    
    pdf = PDF()
    pdf.add_page()
    
    # Informations patient
    pdf.section_title(f"👤 Patient {patient_id}")
    
    age_ans = patient_data['age_mois'] // 12
    age_mois = patient_data['age_mois'] % 12
    
    info_text = f"""
    Âge: {patient_data['age_mois']} mois ({age_ans} ans {age_mois} mois)
    Sexe: {patient_data['sexe']}
    Âge diagnostic: {patient_data['age_diagnostic']} mois
    """
    pdf.section_body(info_text)
    
    # Scores cliniques
    pdf.section_title("🎯 Scores cliniques")
    
    scores = [
        ("Communication sociale", patient_data['communication_sociale']),
        ("Interactions sociales", patient_data['interactions_sociales']),
        ("Comportements restreints", patient_data['comportements_restreints']),
        ("Langage expressif", patient_data['langage_expressif']),
        ("Langage réceptif", patient_data['langage_receptif']),
        ("Contact visuel", patient_data['contact_visuel']),
        ("Imitation", patient_data['imitation']),
        ("Jeu symbolique", patient_data['jeu_symbolique'])
    ]
    
    for label, score in scores:
        if not pd.isna(score):
            if score >= 7:
                niveau = "Sévère"
            elif score >= 4:
                niveau = "Modéré"
            else:
                niveau = "Léger"
            pdf.cell(0, 8, f"{label}: {score}/10 - {niveau}", 0, 1)
    
    pdf.ln(5)
    
    # Interventions (5 types)
    pdf.section_title("💊 Interventions en cours")
    interventions = []
    if patient_data['orthophonie'] == 1:
        interventions.append("Orthophonie")
    if patient_data['psychomotricite'] == 1:
        interventions.append("Psychomotricité")
    if patient_data['aba'] == 1:
        interventions.append("ABA")
    if patient_data['teacch'] == 1:
        interventions.append("TEACCH")
    if patient_data['pecs'] == 1:
        interventions.append("PECS")
    
    if interventions:
        for interv in interventions:
            pdf.cell(0, 8, f"✓ {interv}", 0, 1)
    else:
        pdf.cell(0, 8, "Aucune intervention en cours", 0, 1)
    
    pdf.ln(5)
    
    # Comorbidités
    pdf.section_title("🏥 Comorbidités")
    comorbidites = []
    if patient_data['tdah'] == 1:
        comorbidites.append("TDAH")
    if patient_data['anxiete'] == 1:
        comorbidites.append("Anxiété")
    if patient_data['trouble_sommeil'] == 1:
        comorbidites.append("Troubles du sommeil")
    
    if comorbidites:
        for comor in comorbidites:
            pdf.cell(0, 8, f"⚠ {comor}", 0, 1)
    else:
        pdf.cell(0, 8, "Aucune comorbidité", 0, 1)
    
    pdf.ln(5)
    
    # Score moyen
    scores_list = [s for _, s in scores if not pd.isna(s)]
    score_moyen = sum(scores_list) / len(scores_list) if scores_list else 0
    
    if score_moyen >= 7:
        profil = "Sévère"
    elif score_moyen >= 4:
        profil = "Modéré"
    else:
        profil = "Léger"
    
    pdf.section_title("📋 Synthèse")
    pdf.section_body(f"""
    Profil global: {profil}
    Score moyen: {score_moyen:.1f}/10
    {len(interventions)} intervention(s) en cours
    {len(comorbidites)} comorbidité(s)
    """)
    
    # Sauvegarder le PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        return tmp.name

def add_export_button(patient_data, patient_id):
    """Ajoute un bouton d'export PDF dans Streamlit"""
    
    if st.button("📄 Exporter le profil en PDF", use_container_width=True):
        with st.spinner("📄 Génération du PDF..."):
            try:
                pdf_path = export_patient_pdf(patient_data, patient_id)
                
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="📥 Télécharger le PDF",
                    data=pdf_bytes,
                    file_name=f"AutiGraphCare_{patient_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Nettoyer
                try:
                    os.unlink(pdf_path)
                except:
                    pass
                    
            except Exception as e:
                st.error(f"Erreur lors de la génération du PDF: {str(e)}")