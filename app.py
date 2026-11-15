import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client, Client
import io
import xlsxwriter

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

# --- 3. FONCTIONS CACHE & DONNÉES ---
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

# --- 4. INITIALISATION DES VARIABLES DE SESSION ---
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None
if "liste_entreprises" not in st.session_state:
    charger_entreprises()
if "liste_employes" not in st.session_state:
    st.session_state["liste_employes"] = []
if "admin_pwd" not in st.session_state:
    st.session_state["admin_pwd"] = "admin"  # Mot de passe par défaut modifiable

# --- 5. PORTAIL DE CONNEXION & INSCRIPTION (BRANDING) ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center; color: #0284c7;'>🏢 Portail Optima RH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Solution de gestion RH & Paie intelligente.</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6b7280; font-size: 14px;'><i>Conception, Branding & Réalisation : <b>BENMOUMENE HOUARI</b></i></p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Connexion Client", "✨ Inscrire une Entreprise"])
        
        with tab_login:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            noms_soc = [s["nom"] for s in st.session_state["liste_entreprises"]]
            
            with st.form("formulaire_connexion"):
                societe_choisie = st.selectbox("Sélectionnez votre entreprise", noms_soc)
                mot_de_passe = st.text_input("Mot de passe Administrateur", type="password", help="Le mot de passe par défaut est : admin")
                submit_btn = st.form_submit_button("Se Connecter", type="primary", use_container_width=True)
                
                if submit_btn:
                    if mot_de_passe == st.session_state["admin_pwd"]:
                        compte = next((s for s in st.session_state["liste_entreprises"] if s["nom"] == societe_choisie), None)
                        st.session_state["connected_company"] = compte
                        charger_employes(compte["id"])
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect.")
            st.markdown('</div>', unsafe_allow_html=True)
            
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
                            st.success("✅ Entreprise créée ! Allez dans 'Connexion Client'.")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la création : {e}")
                    else:
                        st.error("⚠️ Le nom de l'entreprise est obligatoire.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. ESPACE ERP CONNECTÉ ---
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
    
    # OPTION CHANGEMENT MOT DE PASSE
    with st.expander("⚙️ Sécurité & Paramètres"):
        nouveau_pwd = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Sauvegarder le mot de passe", use_container_width=True):
            if nouveau_pwd:
                st.session_state["admin_pwd"] = nouveau_pwd
                st.success("✅ Mot de passe modifié !")
            else:
                st.warning("⚠️ Entrez un mot de passe.")
                
    st.divider()
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.session_state["liste_employes"] = []
        st.rerun()

st.title(f"Tableau de Bord - {societe_nom}")
tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["👥 Base Salariés", "📅 Pointage & Paie", "📄 Documents Légaux", "💰 Simulateur Paie"])

# --- TAB 1: GESTION DES SALARIÉS ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        st.dataframe(pd.DataFrame(employes)[['nom_complet', 'poste', 'salaire_mensuel', 'date_integration']], use_container_width=True)
    else:
        st.info("ℹ️ Le registre est vide. Utilisez la version complète pour ajouter des employés.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: POINTAGE & PAIE (AVEC CALCULE AUTO ET EXCEL FIDÈLE) ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        c_mois, c_annee = st.columns(2)
        mois_actuel = datetime.now().month
        annee_actuelle = datetime.now().year
        
        mois_select = c_mois.selectbox("Mois", range(1, 13), index=mois_actuel - 1, format_func=lambda x: calendar.month_name[x].capitalize())
        annee_select = c_annee.selectbox("Année", range(2020, 2035), index=annee_actuelle - 2020)
        
        _, num_days = calendar.monthrange(annee_select, mois_select)
        jours_fr = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
        
        # Données initiales
        donnees_pointage = []
        for e in employes:
            ligne = {
                "Nom et Prénom": e.get('nom_complet', ''),
                "Fonction": e.get('poste', ''),
                "Salaire Base": float(e.get('salaire_mensuel', 0.0))
            }
            for jour in range(1, num_days + 1):
                ligne[str(jour)] = "P" # "P" par défaut
            donnees_pointage.append(ligne)
            
        df_pt = pd.DataFrame(donnees_pointage)
        
        st.markdown("### ✍️ Saisie du pointage")
        st.markdown("**Légende :** `P` (Présent) | `P/2` (Demi-journée) | `AI` (Absence Irrégulière) | `AA` (Absence Autorisée)")
        
        col_config = {"Nom et Prénom": st.column_config.TextColumn(disabled=True),
                      "Fonction": st.column_config.TextColumn(disabled=True),
                      "Salaire Base": None} # Masquer salaire base dans la grille de saisie
        
        for jour in range(1, num_days + 1):
            col_config[str(jour)] = st.column_config.SelectboxColumn(options=["P", "P/2", "AI", "AA"], default="P")
            
        df_edit = st.data_editor(df_pt, column_config=col_config, hide_index=True, use_container_width=True)
        
        # --- CALCULS DE LA PAIE & PRÉSENCE ---
        jours_cols = [str(j) for j in range(1, num_days + 1)]
        df_export = df_edit.copy()
        
        def calc_jours_travailles(row):
            return sum(1 for c in jours_cols if row[c] == "P") + sum(0.5 for c in jours_cols if row[c] == "P/2")
            
        def calc_jours_absents(row):
            return sum(1 for c in jours_cols if row[c] in ["AI", "AA"]) + sum(0.5 for c in jours_cols if row[c] == "P/2")
            
        df_export["Jours Travaillés"] = df_export.apply(calc_jours_travailles, axis=1)
        df_export["Jours Absents"] = df_export.apply(calc_jours_absents, axis=1)
        df_export["Salaire Net Estimé"] = (df_export["Salaire Base"] / 30) * df_export["Jours Travaillés"]
        
        st.divider()
        st.markdown("### 💰 État des Salaires & Coût de l'Entreprise (Mois en cours)")
        st.metric("Total Masse Salariale Nette", f"{df_export['Salaire Net Estimé'].sum():,.2f} DA")
        
        df_paie_display = df_export[["Nom et Prénom", "Fonction", "Jours Travaillés", "Jours Absents", "Salaire Base", "Salaire Net Estimé"]]
        st.dataframe(df_paie_display, use_container_width=True)
        
        # --- GÉNÉRATION EXCEL 1 : POINTAGE EXACT (Identique au fichier Pointage_Novembre-2026.xlsx) ---
        out_pt = io.BytesIO()
        workbook = xlsxwriter.Workbook(out_pt, {'in_memory': True})
        ws = workbook.add_worksheet('Pointage générale')
        
        fmt_bold = workbook.add_format({'bold': True})
        fmt_border = workbook.add_format({'border': 1})
        fmt_center_border = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter'})
        
        # Légendes Row 1
        ws.write('D1', 'P', fmt_center_border)
        ws.write('E1', 'Present')
        ws.write('G1', 'P/2', fmt_center_border)
        ws.write('H1', 'Present Demi journée')
        ws.write('J1', 'AA', fmt_center_border)
        ws.write('K1', 'Absence Autorisé')
        ws.write('M1', 'AI', fmt_center_border)
        ws.write('N1', 'Absence Irreguliere')
        
        nom_mois_str = calendar.month_name[mois_select].capitalize()
        # Titres Row 3
        ws.write('B3', societe_nom, fmt_bold)
        ws.write('D3', 'POINTAGE MOIS DE :', fmt_bold)
        ws.write('H3', nom_mois_str, fmt_bold)
        ws.write('K3', annee_select, fmt_bold)
        ws.write('AI3', 'NB. JRS OUVR', fmt_bold)
        ws.write('AJ3', num_days, fmt_bold)
        
        # Headers Row 4 et 5
        ws.write('A5', 'N°', fmt_header)
        ws.write('B5', 'NOM Prenom', fmt_header)
        ws.write('C5', 'Fonction', fmt_header)
        
        for i in range(num_days):
            col = 3 + i
            dt = date(annee_select, mois_select, i+1)
            ws.write(3, col, i+1, fmt_center_border)
            ws.write(4, col, jours_fr[dt.weekday()], fmt_header)
            ws.set_column(col, col, 4)
            
        end_col = 3 + num_days
        ws.write(4, end_col, 'Presence', fmt_header)
        ws.write(4, end_col+1, 'Absence', fmt_header)
        
        ws.set_column('A:A', 5)
        ws.set_column('B:B', 30)
        ws.set_column('C:C', 25)
        ws.set_column(end_col, end_col+1, 12)
        
        # Données Employés
        for row_idx, row in df_export.iterrows():
            r = 5 + row_idx
            ws.write(r, 0, f"{row_idx + 1:02d}", fmt_center_border)
            ws.write(r, 1, row['Nom et Prénom'], fmt_border)
            ws.write(r, 2, row['Fonction'], fmt_border)
            
            for i in range(num_days):
                ws.write(r, 3 + i, row[str(i+1)], fmt_center_border)
                
            ws.write(r, end_col, row['Jours Travaillés'], fmt_center_border)
            ws.write(r, end_col+1, row['Jours Absents'], fmt_center_border)
            
        workbook.close()
        
        # --- GÉNÉRATION EXCEL 2 : ETAT DES SALAIRES ---
        out_paie = io.BytesIO()
        with pd.ExcelWriter(out_paie, engine='xlsxwriter') as writer:
            df_paie_display.to_excel(writer, index=False, sheet_name='Salaires', startrow=2)
            ws_paie = writer.sheets['Salaires']
            ws_paie.merge_range("A1:F1", f"ÉTAT DES SALAIRES - {nom_mois_str} {annee_select} - {societe_nom}", workbook.add_format({'bold': True, 'align': 'center', 'font_size': 14}))
            ws_paie.set_column('A:A', 30)
            ws_paie.set_column('B:B', 25)
            ws_paie.set_column('C:F', 15)
        
        c_dl1, c_dl2 = st.columns(2)
        c_dl1.download_button("📥 Fichier 1 : Télécharger Pointage (Format Exact)", data=out_pt.getvalue(), file_name=f"Pointage_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="primary", use_container_width=True)
        c_dl2.download_button("📥 Fichier 2 : Télécharger État des Salaires", data=out_paie.getvalue(), file_name=f"Salaires_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="secondary", use_container_width=True)
        
    else:
        st.info("⚠️ Aucun employé pour générer le pointage.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DOCUMENTS (EN COURS) ---
with tab_docs:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.info("🚧 **Module 'Documents Légaux' en cours de réalisation (Mise à jour imminente).**\n\nDes améliorations sont en cours de développement par nos équipes pour vous offrir des documents encore plus robustes et conformes aux normes.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: SIMULATEUR PAIE (EN COURS) ---
with tab_paie:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.warning("🚧 **Module 'Simulateur Paie Avancé' en cours de réalisation (Mise à jour imminente).**\n\nBientôt, vous pourrez simuler avec précision l'IRG, la sécurité sociale et générer des fiches de paie détaillées directement depuis cet onglet.")
    st.markdown('</div>', unsafe_allow_html=True)
