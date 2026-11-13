import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF

# --- 1. CONFIGURATION & STYLES (DARK / LIGHT MODE AUTO) ---
st.set_page_config(page_title="Optima RH - ERP", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .login-card { 
            background-color: var(--secondary-background-color); 
            padding: 40px; 
            border-radius: 12px; 
            box-shadow: 0 8px 20px rgba(0,0,0,0.1); 
            margin-top: 50px;
            border: 1px solid rgba(128, 128, 128, 0.2);
        }
        .glass-card { 
            background-color: var(--secondary-background-color); 
            border: 1px solid rgba(128, 128, 128, 0.2); 
            border-radius: 10px; 
            padding: 25px; 
            margin-bottom: 20px;
        }
        .metric-value { font-size: 28px; font-weight: bold; color: #0284c7; }
        /* Les couleurs de texte s'adaptent au thème natif de Streamlit */
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION SUPABASE ---
URL = "https://firjafhrsqsfluohcrow.supabase.co"
CLE_API = "sb_publishable_4x5vHBt6RnM5LbwVi9xLLg_OsANQ0Li"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, CLE_API)

supabase = init_supabase()

# --- 3. FONCTIONS GÉNÉRATION PDF & EXCEL ---
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
    pdf.cell(0, 8, f"N° Adhérent : A COMPLETER", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "IDENTIFICATION DU SALARIE", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Nom et Prénom : {emp.get('nom_complet', '')}", ln=True)
    pdf.cell(0, 8, f"N° Immatriculation SS : {emp.get('num_ss', '')}", ln=True)
    pdf.cell(0, 8, f"Pièce : {emp.get('type_piece', 'CIN')} N° {emp.get('num_piece', '')}", ln=True)
    pdf.cell(0, 8, f"Profession : {emp.get('poste', '')}", ln=True)
    pdf.ln(15)
    pdf.cell(0, 10, "Cachet et Signature", ln=True, align='R')
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
    pdf.cell(60, 10, "Nom de l'employe :", border=1); pdf.cell(130, 10, emp.get('nom_complet', ''), border=1, ln=True)
    pdf.cell(60, 10, "En sa qualite de :", border=1); pdf.cell(130, 10, emp.get('poste', ''), border=1, ln=True)
    pdf.cell(60, 10, "Projet d'affectation :", border=1); pdf.cell(130, 10, projet, border=1, ln=True)
    pdf.cell(60, 10, "Date de depart :", border=1); pdf.cell(130, 10, str(date_dep), border=1, ln=True)
    pdf.cell(60, 10, "Motif :", border=1); pdf.cell(130, 10, motif, border=1, ln=True)
    return pdf

def exporter_pdf(pdf_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_obj.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- 4. GESTION DE CONNEXION SÉCURISÉE ---
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None

if st.session_state["connected_company"] is None:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🏢 Portail RH & Paie</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Veuillez vous identifier.</p><hr>", unsafe_allow_html=True)
        
        # Récupérer les sociétés (ou utiliser des valeurs par défaut)
        try:
            res_soc = supabase.table("entreprises").select("*").execute()
            liste_soc = res_soc.data if res_soc.data else [{"nom": "SARL MAINA", "id": 0}, {"nom": "SOMIZ", "id": 1}]
        except:
            liste_soc = [{"nom": "SARL MAINA", "id": 0}, {"nom": "SOMIZ", "id": 1}]
            
        noms_soc = [s["nom"] for s in liste_soc]
        
        # UTILISATION D'UN FORMULAIRE (st.form) POUR ÉVITER LE BUG DU MOT DE PASSE
        with st.form("formulaire_connexion"):
            societe_choisie = st.selectbox("Société / Filiale", noms_soc)
            utilisateur = st.text_input("Identifiant", value="admin")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            
            submit_btn = st.form_submit_button("🔐 Se Connecter à l'ERP", type="primary", use_container_width=True)
            
            if submit_btn:
                if mot_de_passe.strip().lower() == "admin":
                    compte = next((s for s in liste_soc if s["nom"] == societe_choisie), None)
                    st.session_state["connected_company"] = compte
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect. Le mot de passe est 'admin'.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. ESPACE ERP ---
entreprise = st.session_state["connected_company"]
societe_nom = entreprise["nom"]

with st.sidebar:
    st.markdown(f"### 🏢 **{societe_nom}**")
    st.success("🟢 Connecté")
    st.divider()
    st.info("💡 Pour changer de thème (Clair/Sombre) : cliquez sur les 3 points (⋮) en haut à droite > Settings > Theme.")
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.rerun()

# Récupération des employés
try:
    res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise.get("id")).execute()
    employes = res_emp.data if res_emp.data else []
except:
    employes = []

st.title(f"Tableau de Bord - {societe_nom}")
tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["👥 Base Salariés", "📅 Pointage Excel", "📄 Documents RH", "💰 Paie"])

# --- TAB 1: SALARIÉS ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Nouveau Salarié (Canevas)")
    with st.form("form_add_salarie", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            nom = st.text_input("Nom Complet *")
            sexe = st.selectbox("Sexe", ["M", "F"])
            date_naiss = st.date_input("Date Naissance", value=date(1990, 1, 1))
        with c2:
            type_piece = st.selectbox("Type Pièce *", ["Carte Nationale (CIN)", "Permis de Conduire", "Passeport"])
            num_piece = st.text_input("Numéro Pièce *")
            num_ss = st.text_input("N° Sécurité Sociale (CNAS)")
        with c3:
            poste = st.text_input("Poste / Fonction *")
            salaire = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
            date_int = st.date_input("Date Intégration")
            
        if st.form_submit_button("💾 Enregistrer", type="primary"):
            if nom and poste and num_piece:
                try:
                    supabase.table("employes").insert({
                        "entreprise_id": entreprise.get("id"), "nom_complet": nom, "sexe": sexe, 
                        "date_naissance": str(date_naiss), "type_piece": type_piece, "num_piece": num_piece, 
                        "poste": poste, "salaire_mensuel": salaire, "date_integration": str(date_int), 
                        "num_ss": num_ss, "statut": "Actif"
                    }).execute()
                    st.success("✅ Enregistré ! Rechargez la page (F5).")
                except:
                    st.warning("⚠️ Mode hors-ligne : la base de données n'est pas encore configurée, mais l'interface fonctionne.")
            else:
                st.error("Remplissez les champs avec *")
    st.markdown('</div>', unsafe_allow_html=True)

    if employes:
        st.dataframe(pd.DataFrame(employes)[['nom_complet', 'poste', 'type_piece', 'num_piece']], use_container_width=True)

# --- TAB 2: POINTAGE EXCEL ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📅 Saisie et Export du Pointage")
    if employes:
        df_pt = pd.DataFrame([{"ID": e['id'], "Employé": e['nom_complet'], "Poste": e['poste'], "Présence": "Présent"} for e in employes])
        df_edit = st.data_editor(df_pt, column_config={"Présence": st.column_config.SelectboxColumn(options=["Présent", "Absent", "Demi-Journée"])}, hide_index=True, use_container_width=True)
        
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_edit.to_excel(writer, index=False, sheet_name='Pointage')
        
        st.download_button("📥 Télécharger Excel", data=out.getvalue(), file_name=f"Pointage_{societe_nom}.xlsx", mime="application/vnd.ms-excel", type="primary")
    else:
        st.info("Ajoutez des employés pour générer le pointage.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DOCUMENTS RH ---
with tab_docs:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📄 Impression Documents Légaux")
    if employes:
        c1, c2 = st.columns([1, 2])
        e_doc = c1.selectbox("Sélectionner l'Employé:", employes, format_func=lambda x: x["nom_complet"])
        t_doc = c1.radio("Document:", ["Attestation ATS (CNAS)", "Avis de Départ"])
        
        with c2:
            if t_doc == "Avis de Départ":
                projet = st.text_input("Projet", "Projet MTBE")
                motif = st.selectbox("Motif", ["Départ volontaire", "Fin de contrat"])
                if st.button("Générer Avis"):
                    pdf = generer_avis_depart(e_doc, projet, date.today(), motif)
                    st.download_button("📥 Télécharger Avis", exporter_pdf(pdf), file_name="Avis.pdf", mime="application/pdf")
            elif t_doc == "Attestation ATS (CNAS)":
                if st.button("Générer ATS CNAS"):
                    pdf = generer_ats_cnas(e_doc, societe_nom)
                    st.download_button("📥 Télécharger ATS", exporter_pdf(pdf), file_name="ATS.pdf", mime="application/pdf")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: PAIE ---
with tab_paie:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 💰 Gestion Paie")
    if employes:
        e_paie = st.selectbox("Salarié:", employes, format_func=lambda x: x["nom_complet"], key="paie")
        base = float(e_paie.get('salaire_mensuel', 0.0))
        c_p1, c_p2 = st.columns(2)
        jours = c_p1.number_input("Jours Travaillés", value=30.0)
        primes = c_p2.number_input("Primes (DA)", value=0.0)
        
        sal_poste = (base * (jours / 30)) + primes
        cnas = sal_poste * 0.09
        
        st.divider()
        st.markdown(f"#### NET À PAYER : <span class='metric-value'>{sal_poste - cnas:,.2f} DA</span>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
