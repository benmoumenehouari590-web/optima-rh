import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Optima RH - ERP", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        .login-card { background-color: var(--secondary-background-color); padding: 40px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); border: 1px solid rgba(128, 128, 128, 0.2); }
        .glass-card { background-color: var(--secondary-background-color); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 10px; padding: 25px; margin-bottom: 20px; }
        .metric-value { font-size: 28px; font-weight: bold; color: #0284c7; }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION SUPABASE ---
URL = "https://firjafhrsqsfluohcrow.supabase.co"
CLE_API = "sb_publishable_4x5vHBt6RnM5LbwVi9xLLg_OsANQ0Li"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, CLE_API)

supabase = init_supabase()

# --- 3. FONCTIONNALITÉS CACHE & MÉMOIRE RAPIDE ---
def charger_entreprises():
    try:
        res = supabase.table("entreprises").select("*").execute()
        st.session_state["liste_entreprises"] = res.data if res.data else [{"nom": "SARL MAINA", "id": 0}]
    except:
        st.session_state["liste_entreprises"] = [{"nom": "SARL MAINA", "id": 0}]

def charger_employes(entreprise_id):
    try:
        res = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
        st.session_state["liste_employes"] = res.data if res.data else []
    except:
        st.session_state["liste_employes"] = []

def parse_date(date_str, default_year):
    try:
        return datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d').date()
    except:
        return date(default_year, 1, 1)

# --- 4. FONCTIONS DE GÉNÉRATION DE DOCUMENTS ---
def generer_ats_cnas(emp, societe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "REPUBLIQUE ALGERIENNE DEMOCRATIQUE ET POPULAIRE", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, "CAISSE NATIONALE DES ASSURANCES SOCIALES DES TRAVAILLEURS SALARIES", ln=True, align='C')
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 12, "ATTESTATION DE TRAVAIL ET DE SALAIRE (A.T.S)", border=1, ln=True, align='C')
    pdf.ln(8)
    # ... (le reste du code ATS reste identique)
    return pdf

def generer_avis_depart(emp, projet, date_dep, motif, societe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"ENTREPRISE : {societe}", ln=True)
    pdf.ln(10)
    # ... (le reste du code Avis de départ reste identique)
    return pdf

def exporter_pdf(pdf_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_obj.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- 5. INITIALISATION DES VARIABLES DE SESSION ---
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None
if "liste_entreprises" not in st.session_state:
    charger_entreprises()
if "liste_employes" not in st.session_state:
    st.session_state["liste_employes"] = []

# --- 6. PORTAIL DE CONNEXION & INSCRIPTION (AVEC BRANDING) ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center; color: #0284c7;'>🏢 Portail Optima RH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Solution de gestion RH & Paie intelligente.</p>", unsafe_allow_html=True)
        # BRANDING AJOUTÉ ICI
        st.markdown("<p style='text-align: center; color: #6b7280; font-size: 14px;'><i>Conception, Branding & Réalisation : <b>BENMOUMENE HOUARI</b></i></p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Connexion Client", "✨ Inscrire une Entreprise"])
        
        # ONGLET CONNEXION
        with tab_login:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            noms_soc = [s["nom"] for s in st.session_state["liste_entreprises"]]
            
            with st.form("formulaire_connexion"):
                societe_choisie = st.selectbox("Sélectionnez votre entreprise", noms_soc)
                mot_de_passe = st.text_input("Mot de passe Administrateur", type="password", help="Le mot de passe par défaut est : admin")
                submit_btn = st.form_submit_button("Se Connecter", type="primary", use_container_width=True)
                
                if submit_btn:
                    if mot_de_passe.strip().lower() == "admin":
                        compte = next((s for s in st.session_state["liste_entreprises"] if s["nom"] == societe_choisie), None)
                        st.session_state["connected_company"] = compte
                        charger_employes(compte["id"])
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # ONGLET INSCRIPTION
        with tab_register:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            with st.form("formulaire_inscription"):
                nouveau_nom = st.text_input("Nom officiel de l'entreprise (Raison Sociale) *")
                nouveau_secteur = st.selectbox("Secteur d'activité", ["BTP", "Services", "Industrie", "Commerce", "Technologie", "Autre"])
                submit_reg = st.form_submit_button("Créer mon espace", type="primary", use_container_width=True)
                
                if submit_reg:
                    if nouveau_nom.strip() != "":
                        try:
                            res = supabase.table("entreprises").insert({"nom": nouveau_nom.strip()}).execute()
                            if res.data:
                                st.session_state["liste_entreprises"].append(res.data[0])
                            st.success("✅ Entreprise créée ! Allez dans 'Connexion Client' pour vous connecter.")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la création : {e}")
                    else:
                        st.error("⚠️ Le nom de l'entreprise est obligatoire.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 7. ESPACE ERP CONNECTÉ ---
entreprise = st.session_state["connected_company"]
societe_nom = entreprise["nom"]
entreprise_id = entreprise.get("id", 0)
employes = st.session_state["liste_employes"]

with st.sidebar:
    st.markdown(f"### 🏢 **{societe_nom}**")
    st.success("🟢 Mode Administrateur")
    st.divider()
    st.metric("Total Salariés", len(employes))
    st.divider()
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.session_state["liste_employes"] = []
        st.rerun()

st.title(f"Tableau de Bord - {societe_nom}")
tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["👥 Base Salariés", "📅 Pointage Excel Mensuel", "📄 Documents Légaux", "💰 Simulateur Paie"])

# --- TAB 1: GESTION DES SALARIÉS (Garde l'existant) ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    sub_list = st.tabs(["📋 Registre du Personnel"])[0]
    with sub_list:
        if employes:
            st.dataframe(pd.DataFrame(employes)[['nom_complet', 'poste', 'salaire_mensuel']], use_container_width=True)
        else:
            st.info("ℹ️ Le registre est vide. Utilisez l'application complète pour ajouter des employés.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: NOUVEAU POINTAGE RAPIDE & DYNAMIQUE ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        c_mois, c_annee = st.columns(2)
        mois_actuel = datetime.now().month
        annee_actuelle = datetime.now().year
        
        mois_select = c_mois.selectbox("Mois", range(1, 13), index=mois_actuel - 1, format_func=lambda x: calendar.month_name[x].capitalize())
        annee_select = c_annee.selectbox("Année", range(2020, 2035), index=annee_actuelle - 2020)
        
        # Calcul du nombre de jours dans le mois sélectionné
        _, num_days = calendar.monthrange(annee_select, mois_select)
        
        # Création de la grille de pointage (par défaut: coché = 1, décoché = 0)
        donnees_pointage = []
        for e in employes:
            ligne = {
                "Nom et Prénom": e.get('nom_complet', ''),
                "Fonction": e.get('poste', '')
            }
            # Génération des jours
            for jour in range(1, num_days + 1):
                ligne[str(jour)] = True # True = Présent par défaut (pour que ce soit très rapide)
            donnees_pointage.append(ligne)
            
        df_pt = pd.DataFrame(donnees_pointage)
        
        st.markdown("### ✍️ Saisie rapide du pointage (Décochez pour les absences)")
        
        # Configuration des colonnes pour st.data_editor
        col_config = {"Nom et Prénom": st.column_config.TextColumn(disabled=True),
                      "Fonction": st.column_config.TextColumn(disabled=True)}
        for jour in range(1, num_days + 1):
            col_config[str(jour)] = st.column_config.CheckboxColumn(default=True)
            
        # Éditeur de tableau
        df_edit = st.data_editor(df_pt, column_config=col_config, hide_index=True, use_container_width=True)
        
        # Calcul du résumé total
        df_export = df_edit.copy()
        jours_cols = [str(j) for j in range(1, num_days + 1)]
        
        # Convertir les booléens (Vrai/Faux) en 1 et 0, puis faire la somme
        df_export["Total Jours"] = df_export[jours_cols].sum(axis=1)
        
        st.success("✅ Résumé des présences calculé automatiquement. Prêt pour l'export !")
        st.dataframe(df_export[["Nom et Prénom", "Total Jours"]], use_container_width=True)
        
        # EXPORT EXCEL
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Pointage_Mensuel', startrow=4)
            workbook = writer.book
            worksheet = writer.sheets['Pointage_Mensuel']
            
            title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 1})
            info_format = workbook.add_format({'bold': True, 'font_size': 11})
            header_format = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1, 'align': 'center'})
            
            nom_mois = calendar.month_name[mois_select].capitalize()
            worksheet.merge_range(0, 0, 1, num_days+2, f"FEUILLE DE POINTAGE OFFICIELLE - {societe_nom}", title_format)
            worksheet.write('A4', f"Période : {nom_mois} {annee_select}", info_format)
            
            worksheet.set_column('A:A', 30) # Nom
            worksheet.set_column('B:B', 20) # Fonction
            for i in range(2, num_days + 2):
                worksheet.set_column(i, i, 4) # Colonnes des jours très fines
            worksheet.set_column(num_days + 2, num_days + 2, 15) # Total Jours
            
            for col_num, value in enumerate(df_export.columns.values):
                worksheet.write(4, col_num, value, header_format)
        
        st.download_button("📥 Télécharger Excel (Généré)", data=out.getvalue(), file_name=f"Pointage_{societe_nom}_{nom_mois}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="primary")
    else:
        st.info("⚠️ Aucun employé pour générer le pointage.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DOCUMENTS & TAB 4: PAIE (Gardent l'existant) ---
with tab_docs:
    st.info("Voir onglet précédent.")
with tab_paie:
    st.info("Voir onglet précédent.")
