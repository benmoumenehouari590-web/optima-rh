import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client, Client
import io
import xlsxwriter

# --- 1. CONFIGURATION & DESIGN 3D GLASSMORPHISM ---
st.set_page_config(page_title="Optima RH - Dashboard", page_icon="🔮", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Typographie */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* 🌌 FOND SOMBRE ET LUMIÈRES VOLUMÉTRIQUES (ORBS 3D) */
        .stApp {
            background-color: #020617 !important; /* Tailwind Slate 950 */
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(14, 165, 233, 0.12), transparent 40%), 
                radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.12), transparent 40%),
                radial-gradient(circle at 50% 100%, rgba(168, 85, 247, 0.12), transparent 40%) !important;
            background-attachment: fixed;
            color: #f8fafc !important;
        }

        /* 💎 EFFET VERRE (GLASSMORPHISM) SUR LES CARTES ET FORMULAIRES */
        [data-testid="stForm"], .glass-card, [data-testid="stExpander"] { 
            background: rgba(30, 41, 59, 0.4) !important; /* Slate 800 avec transparence */
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 16px !important; 
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
            padding: 24px !important; 
            transition: all 0.3s ease-in-out !important;
        }

        [data-testid="stForm"]:hover, .glass-card:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 25px 50px -12px rgba(14, 165, 233, 0.2) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.25) !important;
        }

        /* SIDEBAR (MENU LATÉRAL) */
        [data-testid="stSidebar"] {
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(20px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        /* 🎛️ BOUTONS MODERNES */
        [data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #0ea5e9, #3b82f6) !important;
            color: white !important;
            border: none !important;
            border-top: 1px solid rgba(255,255,255,0.4) !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4) !important;
        }
        [data-testid="baseButton-primary"]:hover {
            transform: scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.6) !important;
        }
        
        [data-testid="baseButton-secondary"] {
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f8fafc !important;
            border-radius: 10px !important;
        }
        [data-testid="baseButton-secondary"]:hover {
            background: rgba(255,255,255,0.1) !important;
            border-color: rgba(255,255,255,0.2) !important;
        }

        /* 📑 ONGLETS ÉPURÉS */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 20px; 
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            background: transparent !important;
        }
        .stTabs [data-baseweb="tab"] { 
            color: #94a3b8 !important; 
            background: transparent !important;
            border: none !important;
            font-weight: 500 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { 
            color: #38bdf8 !important; 
            border-bottom: 2px solid #38bdf8 !important;
            background: transparent !important;
        }

        /* INPUTS & SELECTS */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            background-color: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            color: white !important;
        }
        
        /* METRICS (CARTES DE STATISTIQUES) */
        [data-testid="stMetricValue"] { 
            color: #f8fafc !important; 
            font-size: 2.5rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 1rem !important;
        }
        
        /* DATA FRAMES (TABLEAUX) */
        [data-testid="stDataFrame"] {
            border-radius: 12px !important;
            overflow: hidden !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }
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
    except Exception:
        st.session_state["liste_entreprises"] = [{"nom": "SARL MAINA", "id": 0}]

def charger_employes(entreprise_id):
    try:
        res = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
        st.session_state["liste_employes"] = res.data if res.data else []
    except Exception:
        st.session_state["liste_employes"] = []

def parse_date(date_str, default_year):
    try:
        return datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d').date()
    except:
        return date(default_year, 1, 1)

# --- 4. INITIALISATION ---
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None
if "liste_entreprises" not in st.session_state:
    charger_entreprises()
if "liste_employes" not in st.session_state:
    st.session_state["liste_employes"] = []
if "admin_pwd" not in st.session_state:
    st.session_state["admin_pwd"] = "admin" 

# --- 5. PORTAIL DE CONNEXION ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: white;'>✨ Optima RH</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Espace de gestion ultra-sécurisé</p><br>", unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        noms_soc = [s["nom"] for s in st.session_state["liste_entreprises"]]
        
        with st.form("formulaire_connexion"):
            societe_choisie = st.selectbox("Sélectionnez l'entreprise", noms_soc)
            mot_de_passe = st.text_input("Mot de passe Administrateur", type="password")
            submit_btn = st.form_submit_button("Accéder au Portail", type="primary", use_container_width=True)
            
            if submit_btn:
                if mot_de_passe == st.session_state["admin_pwd"]:
                    compte = next((s for s in st.session_state["liste_entreprises"] if s["nom"] == societe_choisie), None)
                    st.session_state["connected_company"] = compte
                    charger_employes(compte["id"])
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. ESPACE ERP CONNECTÉ ---
entreprise = st.session_state["connected_company"]
societe_nom = entreprise["nom"]
entreprise_id = entreprise.get("id", 0)
employes = st.session_state["liste_employes"]

with st.sidebar:
    st.markdown(f"### 🏢 {societe_nom}")
    st.caption("🟢 Mode Administrateur")
    st.divider()
    
    with st.expander("⚙️ Paramètres de sécurité"):
        nouveau_pwd = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Mettre à jour", use_container_width=True):
            if nouveau_pwd:
                st.session_state["admin_pwd"] = nouveau_pwd
                st.success("✅ Sécurité mise à jour")
                
    st.divider()
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Conception & Réalisation<br><b>BENMOUMENE HOUARI</b></p>", unsafe_allow_html=True)
    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.session_state["liste_employes"] = []
        st.rerun()

# --- ONGLETS PRINCIPAUX ---
tab_dash, tab_emp, tab_point, tab_docs = st.tabs(["📊 Dashboard", "👥 Salariés", "📅 Pointage & Paie", "📄 Congés & Documents"])

# --- TAB 0 : DASHBOARD (VUE D'ENSEMBLE POUR LE DIRECTEUR) ---
with tab_dash:
    st.markdown("### 📈 Performances Globales")
    st.caption("Aperçu en temps réel des indicateurs de l'entreprise")
    
    # Calcul des métriques dynamiques
    effectif_total = len(employes)
    masse_salariale_base = sum([float(e.get("salaire_mensuel", 0)) for e in employes]) if employes else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.metric("👥 Effectif Total", f"{effectif_total} salariés", delta="En croissance")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.metric("💰 Masse Salariale (Base)", f"{masse_salariale_base:,.2f} DA", delta="Stable")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.metric("📈 Taux de présence", "96%", delta="+2% ce mois")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ⚡ Actions requises aujourd'hui")
    st.info("📌 Sofiane F. a demandé un congé du 12/11 au 15/11. (Module de validation en construction).")

# --- TAB 1 : GESTION DES SALARIÉS ---
with tab_emp:
    sub_list, sub_add, sub_edit = st.tabs(["📋 Registre du personnel", "➕ Nouveau Salarié", "✏️ Mise à jour"])
    
    with sub_list:
        if employes:
            df_emp = pd.DataFrame(employes)
            cols = ['nom_complet', 'poste', 'num_piece', 'num_ss', 'salaire_mensuel']
            st.dataframe(df_emp[[c for c in cols if c in df_emp.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Aucun salarié enregistré dans la base de données.")

    with sub_add:
        with st.form("form_add_salarie", clear_on_submit=True):
            st.markdown("#### Création de Fiche Salarié")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                nom = st.text_input("Nom *")
                prenom = st.text_input("Prénom(s) *")
                sexe = st.selectbox("Sexe", ["H", "F"])
                date_naiss = st.date_input("Date Naissance", value=date(1990, 1, 1), min_value=date(1940, 1, 1))
            with c2:
                type_piece = st.selectbox("Pièce d'identité", ["CIN", "PASSPORT", "PERMIS"])
                num_piece = st.text_input("N° Pièce *")
                date_deliv = st.date_input("Délivrée le", value=date.today())
                lieu_deliv = st.text_input("Lieu délivrance *")
            with c3:
                num_ss = st.text_input("N° CNAS")
                telephone = st.text_input("N° Téléphone")
                porte_acces = st.selectbox("Niveau d'accès", ["P1 (Base)", "P2 (Intermédiaire)", "P3 (Total)"])
            with c4:
                poste = st.text_input("Fonction *")
                salaire = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
                date_int = st.date_input("Date Embauche", value=date.today())
                
            if st.form_submit_button("💾 Sauvegarder le profil", type="primary"):
                if nom and prenom and num_piece and lieu_deliv and poste:
                    try:
                        nom_complet = f"{nom.strip().upper()} {prenom.strip().capitalize()}"
                        new_data = {
                            "entreprise_id": entreprise_id, "nom_complet": nom_complet, "sexe": sexe, 
                            "date_naissance": str(date_naiss), "type_piece": type_piece, "num_piece": num_piece, 
                            "poste": poste, "salaire_mensuel": float(salaire), "date_integration": str(date_int), 
                            "num_ss": num_ss, "statut": "Actif"
                        }
                        res = supabase.table("employes").insert(new_data).execute()
                        if res.data:
                            employe_cree = res.data[0]
                            st.session_state["liste_employes"].append(employe_cree) 
                            st.success("✅ Salarié ajouté avec succès !")
                            st.rerun() 
                    except Exception as e:
                        st.error(f"Erreur technique : {e}")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs obligatoires (*).")

    with sub_edit:
        if employes:
            emp_a_modifier = st.selectbox("Rechercher un profil à modifier :", employes, format_func=lambda x: f"{x.get('nom_complet', 'Inconnu')} - {x.get('poste', '')}")
            if emp_a_modifier and st.button("🗑️ Supprimer ce profil", type="secondary"):
                supabase.table("employes").delete().eq("id", emp_a_modifier["id"]).execute()
                st.session_state["liste_employes"] = [e for e in st.session_state["liste_employes"] if e["id"] != emp_a_modifier["id"]]
                st.success("Profil supprimé.")
                st.rerun()
        else:
            st.info("Aucun profil disponible.")

# --- TAB 2 : POINTAGE & PAIE ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        c_mois, c_annee = st.columns(2)
        mois_select = c_mois.selectbox("Mois de traitement", range(1, 13), index=datetime.now().month - 1)
        annee_select = c_annee.selectbox("Année fiscale", range(2020, 2035), index=datetime.now().year - 2020)
        
        _, num_days = calendar.monthrange(annee_select, mois_select)
        jours_feries_fixes = [(1, 1), (1, 12), (5, 1), (7, 5), (11, 1)]
        
        donnees_pointage = [{
            "Employé": e.get('nom_complet', ''),
            "Poste": e.get('poste', ''),
            "Salaire (Base)": float(e.get('salaire_mensuel', 0.0)),
            **{str(j): "F" if (mois_select, j) in jours_feries_fixes else "P" for j in range(1, num_days + 1)}
        } for e in employes]
            
        df_pt = pd.DataFrame(donnees_pointage)
        
        st.markdown("#### 📅 Matrice de Pointage Mensuelle")
        st.caption("P : Présent | P/2 : Demi-journée | AI : Absence Irrégulière | AA : Absence Autorisée | F : Férié")
        
        col_config = {"Employé": st.column_config.TextColumn(disabled=True), "Poste": st.column_config.TextColumn(disabled=True), "Salaire (Base)": None} 
        for jour in range(1, num_days + 1):
            col_config[str(jour)] = st.column_config.SelectboxColumn(options=["P", "P/2", "AI", "AA", "F"], default="P")
            
        df_edit = st.data_editor(df_pt, column_config=col_config, hide_index=True, use_container_width=True)
        
        jours_cols = [str(j) for j in range(1, num_days + 1)]
        df_edit["Jours Travaillés"] = df_edit[jours_cols].apply(lambda x: x.isin(["P", "F"]).sum() + (x == "P/2").sum() * 0.5, axis=1)
        df_edit["Net à Payer (DA)"] = (df_edit["Salaire (Base)"] / 30) * df_edit["Jours Travaillés"]
        
        st.markdown("---")
        st.markdown("#### 💰 Synthèse des Salaires")
        df_paie_display = df_edit[["Employé", "Poste", "Jours Travaillés", "Salaire (Base)", "Net à Payer (DA)"]]
        st.dataframe(df_paie_display, use_container_width=True, hide_index=True)
        
        nom_mois_str = calendar.month_name[mois_select].capitalize()

        # EXPORT EXCEL
        out_paie = io.BytesIO()
        workbook_paie = xlsxwriter.Workbook(out_paie, {'in_memory': True})
        ws_paie = workbook_paie.add_worksheet('Salaires')
        ws_paie.write(1, 0, f"Salaires : {nom_mois_str} {annee_select} - {societe_nom}")
        entetes = ["Employé", "Poste", "Travaillés (j)", "Salaire Base", "Net à Payer"]
        for c, h in enumerate(entetes): ws_paie.write(3, c, h)
        for row_idx, row in df_paie_display.iterrows():
            r = row_idx + 4
            ws_paie.write(r, 0, row['Employé'])
            ws_paie.write(r, 1, row['Poste'])
            ws_paie.write(r, 2, row['Jours Travaillés'])
            ws_paie.write(r, 3, row['Salaire (Base)'])
            ws_paie.write(r, 4, row['Net à Payer (DA)'])
        workbook_paie.close()
        
        st.download_button("📥 Exporter la Paie (Excel)", data=out_paie.getvalue(), file_name=f"Salaires_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="primary")
        
    else:
        st.warning("⚠️ Veuillez intégrer des salariés pour activer le module de paie.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_docs:
    st.info("🚧 Module de Gestion des Congés et Portail Salarié en cours d'intégration (Étape 2).")
