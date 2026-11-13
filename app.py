import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Optima RH - ERP Algérie", page_icon="🇩🇿", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 20px;}
        .metric-value { font-size: 24px; font-weight: bold; color: #38bdf8; }
        div.stButton > button { background: linear-gradient(90deg, #16a34a, #15803d); color: white; border: none; border-radius: 8px; font-weight: bold; }
        div.stButton > button:hover { box-shadow: 0 5px 15px rgba(22, 163, 74, 0.4); }
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
    pdf.cell(0, 8, f"Né(e) le : {emp.get('date_naissance', 'N/A')} à {emp.get('lieu_naissance', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Profession : {emp.get('poste', 'N/A')}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date de recrutement : {emp.get('date_integration', 'N/A')}", ln=True)
    pdf.ln(15)
    pdf.cell(0, 10, "Cachet et Signature de l'Employeur", ln=True, align='R')
    return pdf

def generer_avis_depart(emp, projet, date_dep, motif):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "AVIS DE DEPART", ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Date : {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, "Nous vous avisons du depart de :", ln=True)
    pdf.ln(10)
    pdf.cell(60, 10, "Nom de l'employe :", border=1)
    pdf.cell(130, 10, emp.get('nom_complet', ''), border=1, ln=True)
    pdf.cell(60, 10, "En sa qualite de :", border=1)
    pdf.cell(130, 10, emp.get('poste', ''), border=1, ln=True)
    pdf.cell(60, 10, "Projet d'affectation :", border=1)
    pdf.cell(130, 10, projet, border=1, ln=True)
    pdf.cell(60, 10, "Date effective du depart :", border=1)
    pdf.cell(130, 10, str(date_dep), border=1, ln=True)
    pdf.cell(60, 10, "Motif de depart :", border=1)
    pdf.cell(130, 10, motif, border=1, ln=True)
    pdf.ln(20)
    pdf.cell(0, 10, "Signature de l'Administration", ln=True, align='R')
    return pdf

def generer_fiche_renseignements(emp, societe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "FICHE DE RENSEIGNEMENTS SOUS-TRAITANT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 11)
    
    infos = [
        f"NOM ET PRENOM : {emp.get('nom_complet', '')}",
        f"DATE ET LIEU DE NAISSANCE : {emp.get('date_naissance', '')} à {emp.get('lieu_naissance', '')}",
        f"FILIATION : {emp.get('filiation', '')}",
        f"PIECE D'IDENTITE : {emp.get('type_piece', '')} N° {emp.get('num_piece', '')}",
        f"DELIVREE LE : {emp.get('date_delivrance', '')} à {emp.get('lieu_delivrance', '')}",
        f"TELEPHONE : {emp.get('num_tel', '')}",
        f"FONCTION : {emp.get('poste', '')}",
        f"RAISON SOCIALE EMPLOYEUR : {societe}",
        f"N° SECURITE SOCIALE (CNAS) : {emp.get('num_ss', '')}"
    ]
    for info in infos:
        pdf.cell(0, 10, info, ln=True)
    return pdf

def exporter_pdf(pdf_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_obj.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

def calculer_irg_2020(base_imposable):
    if base_imposable <= 30000: return 0
    irg_brut = (base_imposable - 30000) * 0.30 if base_imposable <= 120000 else (120000 - 30000) * 0.30 + (base_imposable - 120000) * 0.35
    abattement = max(1000, min(1500, irg_brut * 0.40))
    return max(0, irg_brut - abattement)

# --- 3. GESTION DES DONNÉES (Session State & Supabase) ---
# (Intégration transparente pour éviter les erreurs si la BDD n'est pas encore à jour)
if "employes_locaux" not in st.session_state:
    st.session_state["employes_locaux"] = []

# MOCK SOCIETE (A remplacer par votre connexion Supabase habituelle si besoin)
societe = "SARL MAINA"

st.sidebar.title("🇩🇿 Optima RH")
st.sidebar.write(f"Entreprise : **{societe}**")

tab_dash, tab_emp, tab_point, tab_docs, tab_paie = st.tabs([
    "📊 Dashboard", "👥 Base Salariés & Canevas", "📅 Pointage Mensuel", "📄 Documents RH", "💰 Gestion Paie"
])

# --- TAB 2: NOUVEAU SALARIÉ (LE CANEVAS COMPLET) ---
with tab_emp:
    st.markdown("### 📝 Intégration d'un Nouveau Salarié (Canevas Détaillé)")
    with st.form("form_add_salarie"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Identité**")
            nom = st.text_input("Nom Complet")
            sexe = st.selectbox("Sexe", ["M", "F"])
            date_naiss = st.date_input("Date de Naissance", min_value=date(1950, 1, 1), value=date(1990, 1, 1))
            lieu_naiss = st.text_input("Lieu de Naissance")
            filiation = st.text_input("Fils/Fille de... et de...")
            
        with col2:
            st.markdown("**Documents & Contacts**")
            type_piece = st.selectbox("Type Pièce d'Identité", ["Carte Nationale (CIN)", "Permis de Conduire", "Passeport"])
            num_piece = st.text_input("Numéro de Pièce")
            date_delivrance = st.date_input("Date de Délivrance")
            lieu_delivrance = st.text_input("Lieu de Délivrance")
            num_tel = st.text_input("N° de Téléphone")

        with col3:
            st.markdown("**Informations Professionnelles**")
            poste = st.text_input("Poste / Fonction (ex: CHAUDRONNIER)")
            salaire = st.number_input("Salaire de Base (DA)", value=50000.0, step=5000.0)
            date_int = st.date_input("Date d'intégration")
            num_ss = st.text_input("N° Sécurité Sociale (CNAS)")
            
        if st.form_submit_button("💾 Enregistrer l'Employé dans la Base", use_container_width=True):
            nouvel_employe = {
                "id": len(st.session_state["employes_locaux"]) + 1,
                "nom_complet": nom, "sexe": sexe, "date_naissance": str(date_naiss), "lieu_naissance": lieu_naiss,
                "filiation": filiation, "type_piece": type_piece, "num_piece": num_piece, 
                "date_delivrance": str(date_delivrance), "lieu_delivrance": lieu_delivrance,
                "num_tel": num_tel, "poste": poste, "salaire_mensuel": salaire, 
                "date_integration": str(date_int), "num_ss": num_ss, "statut": "Actif"
            }
            st.session_state["employes_locaux"].append(nouvel_employe)
            st.success(f"✅ {nom} ajouté avec succès avec toutes ses informations détaillées !")

    st.markdown("### 📋 Base de Données Actuelle")
    if st.session_state["employes_locaux"]:
        df_emp = pd.DataFrame(st.session_state["employes_locaux"])
        st.dataframe(df_emp, use_container_width=True)

# --- TAB 4: DOCUMENTS RH (ATS, AVIS DE DÉPART, ETC) ---
with tab_docs:
    st.markdown("### 📄 Générateur de Documents Administratifs Algériens")
    employes = st.session_state["employes_locaux"]
    if employes:
        col_doc1, col_doc2 = st.columns([1, 2])
        e_doc = col_doc1.selectbox("Sélectionner l'Employé :", employes, format_func=lambda x: x["nom_complet"])
        t_doc = col_doc1.selectbox("Type de Document :", [
            "Fiche de Renseignements (Format SOMIZ)", 
            "Attestation de Travail (ATS - CNAS)", 
            "Avis de Départ (Projet)",
            "Certificat de Travail Classique"
        ])
        
        with col_doc2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if t_doc == "Avis de Départ (Projet)":
                projet = st.text_input("Projet d'affectation", "Projet MTBE")
                date_dep = st.date_input("Date effective du départ")
                motif = st.selectbox("Motif de départ", ["Départ volontaire", "Fin de contrat", "Licenciement"])
                
                if st.button("Générer Avis de Départ"):
                    pdf_obj = generer_avis_depart(e_doc, projet, date_dep, motif)
                    bytes_pdf = exporter_pdf(pdf_obj)
                    st.download_button("📥 Télécharger PDF", bytes_pdf, file_name=f"Avis_Depart_{e_doc['nom_complet']}.pdf", mime="application/pdf")
            
            elif t_doc == "Attestation de Travail (ATS - CNAS)":
                st.info("💡 Ce document génère l'entête officielle CNAS pour la déclaration des salaires.")
                if st.button("Générer ATS CNAS"):
                    pdf_obj = generer_ats_cnas(e_doc, societe)
                    bytes_pdf = exporter_pdf(pdf_obj)
                    st.download_button("📥 Télécharger ATS", bytes_pdf, file_name=f"ATS_{e_doc['nom_complet']}.pdf", mime="application/pdf")
                    
            elif t_doc == "Fiche de Renseignements (Format SOMIZ)":
                if st.button("Générer Fiche de Renseignements"):
                    pdf_obj = generer_fiche_renseignements(e_doc, societe)
                    bytes_pdf = exporter_pdf(pdf_obj)
                    st.download_button("📥 Télécharger Fiche", bytes_pdf, file_name=f"Fiche_{e_doc['nom_complet']}.pdf", mime="application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Ajoutez d'abord des employés dans la base.")

# --- TAB 5: GESTION DE LA PAIE ---
with tab_paie:
    st.markdown("### 💰 Édition des Bulletins de Paie (CNAS/IRG)")
    if employes:
        e_paie = st.selectbox("Sélectionner un Salarié pour la paie :", employes, format_func=lambda x: x["nom_complet"])
        base = float(e_paie.get('salaire_mensuel', 0.0))
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c_p1, c_p2, c_p3 = st.columns(3)
        jours_travailles = c_p1.number_input("Jours Travaillés", min_value=0.0, max_value=30.0, value=30.0, step=0.5)
        primes_imposables = c_p2.number_input("Primes Imposables (DA)", value=0.0)
        primes_non_imposables = c_p3.number_input("Primes Non-Imposables (Panier, Transport)", value=0.0)
        
        # Calculs Paie DZ
        salaire_base_calcule = base * (jours_travailles / 30)
        salaire_poste = salaire_base_calcule + primes_imposables
        cnas = salaire_poste * 0.09
        base_irg = salaire_poste - cnas
        irg = calculer_irg_2020(base_irg)
        net_a_payer = base_irg - irg + primes_non_imposables
        
        st.divider()
        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.markdown(f"**Salaire de Poste :** <br><span class='metric-value'>{salaire_poste:,.2f} DA</span>", unsafe_allow_html=True)
        c_r2.markdown(f"**Retenues (CNAS 9% + IRG) :** <br><span style='color:#ef4444; font-size:24px; font-weight:bold;'>-{(cnas + irg):,.2f} DA</span>", unsafe_allow_html=True)
        c_r3.markdown(f"**NET À PAYER :** <br><span style='color:#22c55e; font-size:26px; font-weight:bold;'>{net_a_payer:,.2f} DA</span>", unsafe_allow_html=True)
        
        if st.button("Générer Fiche de Paie Complète (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, f"BULLETIN DE PAIE - {societe}", ln=True, align='C')
            pdf.set_font("Arial", '', 11)
            pdf.ln(10)
            pdf.cell(0, 8, f"Employé : {e_paie['nom_complet']} | Poste : {e_paie['poste']}", ln=True)
            pdf.cell(0, 8, f"N° SS : {e_paie.get('num_ss', 'N/A')} | Jours Travaillés : {jours_travailles} j", ln=True)
            pdf.line(10, 50, 200, 50)
            pdf.ln(10)
            pdf.cell(100, 8, "Salaire de Base", border=1); pdf.cell(90, 8, f"{salaire_base_calcule:,.2f} DA", border=1, ln=True)
            if primes_imposables > 0:
                pdf.cell(100, 8, "Primes Imposables", border=1); pdf.cell(90, 8, f"{primes_imposables:,.2f} DA", border=1, ln=True)
            pdf.cell(100, 8, "SALAIRE DE POSTE", border=1); pdf.cell(90, 8, f"{salaire_poste:,.2f} DA", border=1, ln=True)
            pdf.cell(100, 8, "Retenue SS (CNAS 9%)", border=1); pdf.cell(90, 8, f"-{cnas:,.2f} DA", border=1, ln=True)
            pdf.cell(100, 8, "Retenue IRG", border=1); pdf.cell(90, 8, f"-{irg:,.2f} DA", border=1, ln=True)
            if primes_non_imposables > 0:
                pdf.cell(100, 8, "Primes Non Imposables (Panier/Transp.)", border=1); pdf.cell(90, 8, f"+{primes_non_imposables:,.2f} DA", border=1, ln=True)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "NET A PAYER", border=1); pdf.cell(90, 10, f"{net_a_payer:,.2f} DA", border=1, ln=True)
            
            bytes_paie = exporter_pdf(pdf)
            st.download_button("📥 Télécharger le Bulletin de Paie", bytes_paie, file_name=f"Paie_{e_paie['nom_complet']}.pdf", mime="application/pdf")
        st.markdown('</div>', unsafe_allow_html=True)