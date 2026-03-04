# components/kg_builder.py

import networkx as nx
from pyvis.network import Network
import pandas as pd
import streamlit as st
import tempfile
import os

class KnowledgeGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.df = None
    
    def load_data(self, df):
        """Charge les données"""
        self.df = df
        return self
    
    def build_patient_graph(self, patient_id):
        """Construit le graphe pour UN patient"""
        self.graph.clear()
        
        if self.df is None:
            return self.graph
            
        patient = self.df[self.df['id_patient'] == patient_id].iloc[0]
        
        # 1. AJOUTE LE PATIENT (NOEUD CENTRAL)
        self.graph.add_node(
            patient_id, 
            type='patient',
            label=f"Patient {patient_id}",
            age=patient['age_mois'],
            sexe=patient['sexe']
        )
        
        # 2. AJOUTE LES SYMPTÔMES
        symptomes = {
            'communication_sociale': 'Communication sociale',
            'interactions_sociales': 'Interactions sociales',
            'comportements_restreints': 'Comportements restreints',
            'langage_expressif': 'Langage expressif',
            'contact_visuel': 'Contact visuel'
        }
        
        for symp_code, symp_name in symptomes.items():
            if symp_code in patient.index and not pd.isna(patient[symp_code]):
                score = patient[symp_code]
                node_id = f"{symp_code}"
                
                if score >= 7:
                    color = '#FF4444'
                    niveau = "Sévère"
                elif score >= 4:
                    color = '#FFA500'
                    niveau = "Modéré"
                else:
                    color = '#4CAF50'
                    niveau = "Léger"
                
                self.graph.add_node(
                    node_id,
                    type='symptome',
                    label=f"{symp_name}\nScore: {score}/10\nNiveau: {niveau}",
                    score=score,
                    color=color
                )
                self.graph.add_edge(patient_id, node_id, relation='présente')
        
        # 3. AJOUTE LES INTERVENTIONS
        interventions = {
            'orthophonie': 'Orthophonie',
            'psychomotricite': 'Psychomotricité',
            'aba': 'ABA',
            'teacch': 'TEACCH',  # NOUVEAU
            'pecs': 'PECS'        # NOUVEAU
        }
        
        for interv_code, interv_name in interventions.items():
            if interv_code in patient.index and patient[interv_code] == 1:
                node_id = f"{interv_code}"
                self.graph.add_node(
                    node_id,
                    type='intervention',
                    label=f"{interv_name}",
                    color='#50E3C2'
                )
                self.graph.add_edge(patient_id, node_id, relation='reçoit')
        
        # 4. AJOUTE LES COMORBIDITÉS
        comorbidites = {
            'tdah': 'TDAH',
            'anxiete': 'Anxiété',
            'trouble_sommeil': 'Trouble du sommeil'
        }
        
        for com_code, com_name in comorbidites.items():
            if com_code in patient.index and patient[com_code] == 1:
                node_id = f"{com_code}"
                self.graph.add_node(
                    node_id,
                    type='comorbidite',
                    label=f"{com_name}",
                    color='#D0021B'
                )
                self.graph.add_edge(patient_id, node_id, relation='diagnostiqué')
        
        return self.graph
    
    def build_comparison_graph(self, patient_ids):
        """Construit un graphe comparant plusieurs patients"""
        self.graph.clear()
        
        # Ajoute tous les patients
        for pid in patient_ids:
            self.build_patient_graph(pid)
        
        return self.graph
    
    def visualize(self, patient_id=None, patient_ids=None):
        """Crée la visualisation interactive - VERSION CORRIGÉE"""
        try:
            # Construit le graphe approprié
            if patient_ids and len(patient_ids) > 1:
                graph = self.build_comparison_graph(patient_ids)
            elif patient_id:
                graph = self.build_patient_graph(patient_id)
            else:
                return None
            
            # Crée le réseau Pyvis
            net = Network(height='600px', width='100%', directed=True, bgcolor='#ffffff', font_color='#333333')
            
            # Configuration physique
            net.set_options("""
            {
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08,
                  "damping": 0.4
                }
              },
              "edges": {
                "smooth": {"type": "continuous"},
                "arrows": {"to": {"enabled": true}},
                "color": {"color": "#666666"},
                "font": {"size": 12}
              },
              "nodes": {
                "font": {"size": 14, "face": "Inter"},
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "shadow": true
              }
            }
            """)
            
            # Ajoute les noeuds
            for node, data in graph.nodes(data=True):
                label = data.get('label', str(node))
                node_type = data.get('type', 'inconnu')
                
                # Couleurs par type
                colors = {
                    'patient': '#4A90E2',
                    'symptome': '#F5A623',
                    'intervention': '#50E3C2',
                    'comorbidite': '#D0021B'
                }
                color = data.get('color', colors.get(node_type, '#AAAAAA'))
                
                # Taille selon le type
                size = 30 if node_type == 'patient' else 25
                
                net.add_node(
                    str(node),
                    label=label,
                    color=color,
                    size=size,
                    title=f"Type: {node_type}"
                )
            
            # Ajoute les arêtes
            for edge in graph.edges(data=True):
                net.add_edge(
                    str(edge[0]),
                    str(edge[1]),
                    label=edge[2].get('relation', ''),
                    arrows='to'
                )
            
            return net
            
        except Exception as e:
            st.error(f"Erreur de construction du graphe: {str(e)}")
            return None
