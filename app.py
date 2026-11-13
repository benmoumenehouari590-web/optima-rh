import streamlit as st
import pandas as pd
from datetime import datetime, date
import tempfile
from fpdf import FPDF

# --- 1. CONFIGURATION & STYLES PRO ---
st.set_page_config(page_title="Optima RH - ERP", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #f4f6f9; color: #1e293b; }
        .login-card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); margin-top: 50px;}
        .glass-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;}
        .metric-value { font-size: 28px; font-weight: bold; color: #0284c7; }
        .stButton>button { border-radius: 8px; font-weight: bold; }
        .btn-login>button { background-color: #0f172a; color: white; }
    </style>
""", unsafe_allow_html=True)

# --- 2. FONCTIONS DE GÉNÉRATION DE DOCUMENTS (FPDF) ---
class PDF_RH(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", ln=True, align='C')
        self.ln(5)

def generer_ats_cnas(emp, societe):
    pdf = PDF_RH()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "ATTESTATION DE TRAVAIL ET DE SALAIRE (ATS)", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IDENTIFICATION DE L'EMPLOYEUR", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Raison Sociale : {societe}", ln=True)
    pdf.cell(0, 8, f"N° Adhérent Employeur : A COMPLETER", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IDENTIFICATION DU SALARIE", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Nom et Prénom : {emp.get('nom_complet', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"N° Immatriculation (SS) : {emp.get('num_ss', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Pièce : {emp.get('type_piece', '')} N° {emp.get('num_piece', '')}", ln=True)
    pdf.cell(0, 8, f"Profession : {emp.get('poste', 'N/A')}", ln=True)
    pdf.ln(15)
    pdf.cell(0, 10, "Cachet et Signature de l'Employeur", ln=True, align='R')
    return pdf

def exporter_pdf(pdf_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_obj.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- 3. GESTION DE SESSION (LOGIN & DATA) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "employes_locaux" not in st.session_state:
    st.session_state["employes_locaux"] = []

# ==========================================
# ECRAN DE CONNEXION (PORTAIL ERP)
# ==========================================
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>🏢 Portail RH & Paie</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Veuillez vous identifier pour accéder à l'espace de gestion.</p>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        societe_choisie = st.selectbox("Société / Filiale", ["SARL MAINA", "SOMIZ", "Autre Société..."])
        utilisateur = st.text_input("Identifiant", value="admin")
        mot_de_passe = st.text_input("Mot de passe", type="password", help="Tapez 'admin' pour tester")
        
        st.markdown('<div class="btn-login">', unsafe_allow_html=True)
        if st.button("🔐 Se Connecter à l'ERP", use_container_width=True):
            if mot_de_passe == "admin":
                st.session_state["logged_in"] = True
                st.session_state["societe"] = societe_choisie
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect.")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop() # Arrête l'exécution ici si non connecté

# ==========================================
# ECRAN PRINCIPAL (SI CONNECTÉ)
# ==========================================
societe_actuelle = st.session_state["societe"]

# SIDEBAR (Menu de navigation)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135673.png", width=80)
    st.markdown(f"### Espace : **{societe_actuelle}**")
    st.markdown("---")
    st.success("🟢 Connecté en tant qu'Administrateur")
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

st.title(f"Tableau de Bord RH - {societe_actuelle}")

tab_dash, tab_emp, tab_docs, tab_paie = st.tabs([
    "📊 Dashboard", "👥 Base Salariés & Fiches", "📄 Documents RH", "💰 Gestion Paie"
])

# --- TAB 1: NOUVEAU SALARIÉ (AVEC GESTION DES PIÈCES) ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Fiche de Renseignement Salarié")
    with st.form("form_add_salarie"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Identité**")
            nom = st.text_input("Nom Complet *")
            sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
            date_naiss = st.date_input("Date de Naissance", value=date(1990, 1, 1))
            lieu_naiss = st.text_input("Lieu de Naissance")
            
        with col2:
            st.markdown("**Documents d'Identité**")
            # OPTION AJOUTÉE POUR LE CHOIX DE LA PIÈCE
            type_piece = st.selectbox("Type de Pièce *", [
                "Carte Nationale d'Identité (CIN)", 
                "Permis de Conduire", 
                "Passeport Biométrique"
            ])
            num_piece = st.text_input(f"Numéro de {type_piece.split()[0]} *")
            date_delivrance = st.date_input("Date de Délivrance")
            lieu_delivrance = st.text_input("Lieu de Délivrance")

        with col3:
            st.markdown("**Informations Professionnelles**")
            poste = st.text_input("Poste / Fonction *")
            salaire = st.number_input("Salaire de Base (DA)", value=50000.0, step=5000.0)
            date_int = st.date_input("Date d'intégration")
            num_ss = st.text_input("N° Sécurité Sociale (CNAS)")
            
        if st.form_submit_button("💾 Sauvegarder la Fiche Salarié", use_container_width=True):
            if nom and num_piece and poste:
                nouvel_employe = {
                    "id": len(st.session_state["employes_locaux"]) + 1,
                    "nom_complet": nom, "sexe": sexe, "date_naissance": str(date_naiss), 
                    "type_piece": type_piece, "num_piece": num_piece, "poste": poste, 
                    "salaire_mensuel": salaire, "num_ss": num_ss, "statut": "Actif"
                }
                st.session_state["employes_locaux"].append(nouvel_employe)
                st.success(f"✅ Fiche de l'employé {nom} créée avec succès !")
            else:
                st.error("⚠️ Veuillez remplir les champs obligatoires (*).")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 📋 Registre du Personnel")
    if st.session_state["employes_locaux"]:
        df_emp = pd.DataFrame(st.session_state["employes_locaux"])
        st.dataframe(df_emp, use_container_width=True)
    else:
        st.info("Aucun salarié enregistré pour le moment.")

# --- TAB 2: DOCUMENTS RH ---
with tab_docs:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📄 Générateur Automatique de Documents")
    employes = st.session_state["employes_locaux"]
    if employes:
        c1, c2 = st.columns([1, 2])
        e_doc = c1.selectbox("Sélectionner l'Employé :", employes, format_func=lambda x: x["nom_complet"])
        t_doc = c1.radio("Type de Document :", ["Attestation de Travail (ATS - CNAS)", "Avis de Départ", "Certificat de Travail"])
        
        with c2:
            if st.button(f"Générer {t_doc}"):
                pdf_obj = generer_ats_cnas(e_doc, societe_actuelle) # Utilise la société connectée
                bytes_pdf = exporter_pdf(pdf_obj)
                st.download_button("📥 Télécharger le Document (PDF)", bytes_pdf, file_name=f"{t_doc}_{e_doc['nom_complet']}.pdf", mime="application/pdf")
    else:
        st.warning("Veuillez d'abord enregistrer un salarié.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: PAIE ---
with tab_paie:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 💰 Simulateur & Fiches de Paie")
    if employes:
        e_paie = st.selectbox("Sélectionner un Salarié :", employes, format_func=lambda x: x["nom_complet"], key="paie_emp")
        base = float(e_paie.get('salaire_mensuel', 0.0))
        
        c_p1, c_p2, c_p3 = st.columns(3)
        jours_travailles = c_p1.number_input("Jours Travaillés", min_value=0.0, max_value=30.0, value=30.0, step=0.5)
        primes = c_p2.number_input("Primes (DA)", value=0.0)
        
        salaire_poste = (base * (jours_travailles / 30)) + primes
        cnas = salaire_poste * 0.09
        
        st.divider()
        st.markdown(f"#### NET À PAYER ESTIMÉ : <span class='metric-value'>{salaire_poste - cnas:,.2f} DA</span>", unsafe_allow_html=True)
    else:
        st.warning("Veuillez d'abord enregistrer un salarié.")
    st.markdown('</div>', unsafe_allow_html=True)
