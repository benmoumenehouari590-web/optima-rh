import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client, Client
import io
import xlsxwriter

# --- 1. CONFIGURATION & STYLES (DESIGN SAAS PREMIUM - TAILWIND STYLE) ---
st.set_page_config(page_title="Optima RH - ERP", page_icon="🏢", layout="wide")

st.markdown("""
    <style>
        /* Typographie et fond global (Utilise les variables natives de Streamlit) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* 💎 CARTES STYLE SAAS (Minimalistes, bordures fines, ombres douces) */
        [data-testid="stForm"], .login-card, .glass-card { 
            background-color: var(--background-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            border-radius: 12px !important; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05) !important;
            padding: 24px !important; 
            margin-bottom: 24px !important;
            transition: all 0.2s ease-in-out !important;
        }

        [data-testid="stForm"]:hover, .login-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1) !important;
            border-color: rgba(128, 128, 128, 0.3) !important;
        }

        /* 🎛️ BOUTONS MODERNES */
        [data-testid="baseButton-primary"] {
            background-color: #0ea5e9 !important; /* Tailwind Sky 500 */
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="baseButton-primary"]:hover {
            background-color: #0284c7 !important; /* Tailwind Sky 600 */
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.2) !important;
        }
        
        [data-testid="baseButton-secondary"] {
            border: 1px solid rgba(128, 128, 128, 0.3) !important;
            border-radius: 8px !important;
            background-color: transparent !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="baseButton-secondary"]:hover {
            border-color: rgba(128, 128, 128, 0.5) !important;
            background-color: rgba(128, 128, 128, 0.05) !important;
        }

        /* 📑 ONGLETS ÉPURÉS */
        .stTabs [data-baseweb="tab-list"] { 
            gap: 24px; 
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
            padding-bottom: 0 !important;
        }
        .stTabs [data-baseweb="tab"] { 
            height: 45px; 
            font-weight: 500; 
            background: transparent;
            border: none !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-right: 16px !important;
            color: rgba(128, 128, 128, 0.8) !important;
        }
        .stTabs [data-baseweb="tab"]:hover { 
            color: var(--text-color) !important; 
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { 
            color: #0ea5e9 !important; 
            border-bottom: 2px solid #0ea5e9 !important;
            font-weight: 600 !important;
        }

        /* INPUTS & SELECTS */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid rgba(128, 128, 128, 0.2) !important;
            background-color: rgba(128, 128, 128, 0.02) !important;
            transition: all 0.2s ease !important;
        }
        div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
            border-color: #0ea5e9 !important;
            box-shadow: 0 0 0 1px #0ea5e9 !important;
        }

        /* 📊 MÉTRIQUES ET TITRES */
        [data-testid="stMetricValue"] { 
            color: var(--text-color) !important; 
            font-weight: 700 !important;
            font-size: 2rem !important;
            letter-spacing: -0.025em !important;
        }
        h1, h2, h3, h4 { 
            font-weight: 600 !important; 
            letter-spacing: -0.025em !important;
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
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")
        st.session_state["liste_entreprises"] = [{"nom": "SARL MAINA", "id": 0}]

def charger_employes(entreprise_id):
    try:
        res = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
        st.session_state["liste_employes"] = res.data if res.data else []
    except Exception as e:
        st.error(f"Erreur de chargement des employés : {e}")
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
    st.session_state["admin_pwd"] = "admin" 

# --- 5. PORTAIL DE CONNEXION & INSCRIPTION ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🏢 Optima RH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: rgba(128,128,128,0.8);'>Votre espace de gestion RH & Paie.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Connexion", "✨ Inscription"])
        
        with tab_login:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            noms_soc = [s["nom"] for s in st.session_state["liste_entreprises"]]
            
            with st.form("formulaire_connexion"):
                societe_choisie = st.selectbox("Entreprise", noms_soc)
                mot_de_passe = st.text_input("Mot de passe", type="password", help="Défaut : admin")
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
                nouveau_nom = st.text_input("Raison Sociale *")
                nouveau_secteur = st.selectbox("Secteur d'activité", ["BTP", "Services", "Industrie", "Commerce", "Technologie", "Autre"])
                submit_reg = st.form_submit_button("Créer l'espace", type="primary", use_container_width=True)
                
                if submit_reg:
                    if nouveau_nom.strip():
                        try:
                            res = supabase.table("entreprises").insert({"nom": nouveau_nom.strip()}).execute()
                            if res.data:
                                st.session_state["liste_entreprises"].append(res.data[0])
                            st.success("✅ Entreprise créée ! Allez dans 'Connexion'.")
                        except Exception as e:
                            st.error(f"❌ Erreur : {e}")
                    else:
                        st.error("⚠️ Nom obligatoire.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. ESPACE ERP CONNECTÉ ---
entreprise = st.session_state["connected_company"]
societe_nom = entreprise["nom"]
entreprise_id = entreprise.get("id", 0)
employes = st.session_state["liste_employes"]

with st.sidebar:
    st.markdown(f"### 🏢 {societe_nom}")
    st.caption("🟢 Administrateur connecté")
    st.divider()
    st.metric("Salariés Actifs", len(employes))
    st.divider()
    
    with st.expander("⚙️ Paramètres"):
        nouveau_pwd = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Mettre à jour", use_container_width=True):
            if nouveau_pwd:
                st.session_state["admin_pwd"] = nouveau_pwd
                st.success("✅ Modifié !")
            else:
                st.warning("⚠️ Champ vide.")
                
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state["connected_company"] = None
        st.session_state["liste_employes"] = []
        st.rerun()

st.title("Vue d'ensemble")
tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["👥 Salariés", "📅 Pointage & Paie", "📄 Documents", "💰 Simulateur"])

# --- TAB 1: GESTION DES SALARIÉS ---
with tab_emp:
    sub_list, sub_add, sub_edit = st.tabs(["📋 Registre", "➕ Ajouter", "✏️ Modifier"])
    
    with sub_list:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if employes:
            df_emp = pd.DataFrame(employes)
            cols = ['nom_complet', 'poste', 'num_piece', 'num_ss', 'telephone', 'porte_acces', 'salaire_mensuel']
            st.dataframe(df_emp[[c for c in cols if c in df_emp.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Aucun salarié enregistré pour le moment.")
        st.markdown('</div>', unsafe_allow_html=True)

    with sub_add:
        with st.form("form_add_salarie", clear_on_submit=True):
            st.markdown("#### Fiche Salarié")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                nom = st.text_input("Nom *")
                prenom = st.text_input("Prénom(s) *")
                sexe = st.selectbox("Sexe", ["H", "F"])
                date_naiss = st.date_input("Date Naissance", value=date(1990, 1, 1), min_value=date(1940, 1, 1), max_value=date.today())
            with c2:
                type_piece = st.selectbox("Pièce d'identité *", ["CIN", "PASSPORT", "PERMIS DE CONDUIRE"])
                num_piece = st.text_input("N° Pièce *")
                date_deliv = st.date_input("Délivrée le", value=date.today(), min_value=date(1990, 1, 1))
                lieu_deliv = st.text_input("Lieu délivrance *")
            with c3:
                num_ss = st.text_input("N° CNAS")
                telephone = st.text_input("N° Téléphone")
                porte_acces = st.selectbox("Accès", ["P1", "P2", "P3"])
            with c4:
                poste = st.text_input("Fonction *")
                salaire = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
                date_int = st.date_input("Embauche", value=date.today())
                
            if st.form_submit_button("Sauvegarder", type="primary"):
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
                            employe_cree.update({'telephone': telephone, 'porte_acces': porte_acces, 'lieu_deliv': lieu_deliv, 'date_deliv': str(date_deliv)})
                            st.session_state["liste_employes"].append(employe_cree) 
                            st.success("✅ Ajouté avec succès !")
                            st.rerun() 
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                else:
                    st.error("⚠️ Champs (*) obligatoires.")

    with sub_edit:
        if employes:
            emp_a_modifier = st.selectbox("Rechercher un employé :", employes, format_func=lambda x: x.get("nom_complet", "Inconnu"))
            with st.form("form_edit_salarie"):
                st.markdown("#### Mise à jour")
                c1, c2, c3, c4 = st.columns(4)
                
                noms_split = emp_a_modifier.get("nom_complet", "").split(" ", 1)
                m_nom_val, m_prenom_val = noms_split[0], noms_split[1] if len(noms_split) > 1 else ""

                with c1:
                    m_nom = st.text_input("Nom *", value=m_nom_val)
                    m_prenom = st.text_input("Prénom(s) *", value=m_prenom_val)
                    m_sexe = st.selectbox("Sexe", ["H", "F"], index=0 if emp_a_modifier.get("sexe") == "H" else 1)
                    m_date_naiss = st.date_input("Date Naissance", value=parse_date(emp_a_modifier.get("date_naissance"), 1990))
                with c2:
                    options_piece = ["CIN", "PASSPORT", "PERMIS DE CONDUIRE"]
                    val_piece = emp_a_modifier.get("type_piece", "CIN")
                    m_type_piece = st.selectbox("Pièce d'identité *", options_piece, index=options_piece.index(val_piece) if val_piece in options_piece else 0)
                    m_num_piece = st.text_input("N° Pièce *", value=emp_a_modifier.get("num_piece", ""))
                    m_date_deliv = st.date_input("Délivrée le", value=parse_date(emp_a_modifier.get("date_deliv"), 2020))
                    m_lieu_deliv = st.text_input("Lieu délivrance *", value=emp_a_modifier.get("lieu_deliv", ""))
                with c3:
                    m_num_ss = st.text_input("N° CNAS", value=emp_a_modifier.get("num_ss", ""))
                    m_telephone = st.text_input("N° Téléphone", value=emp_a_modifier.get("telephone", ""))
                    options_porte = ["P1", "P2", "P3"]
                    val_porte = emp_a_modifier.get("porte_acces", "P1")
                    m_porte_acces = st.selectbox("Accès", options_porte, index=options_porte.index(val_porte) if val_porte in options_porte else 0)
                with c4:
                    m_poste = st.text_input("Fonction *", value=emp_a_modifier.get("poste", ""))
                    m_salaire = st.number_input("Salaire Base (DA)", value=float(emp_a_modifier.get("salaire_mensuel", 50000.0)), step=5000.0)
                    m_date_int = st.date_input("Embauche", value=parse_date(emp_a_modifier.get("date_integration"), 2023))
                
                col_btn1, col_btn2 = st.columns(2)
                btn_modifier = col_btn1.form_submit_button("Mettre à jour", type="primary", use_container_width=True)
                btn_supprimer = col_btn2.form_submit_button("Supprimer", use_container_width=True)
                
                if btn_modifier and m_nom and m_prenom and m_poste and m_num_piece:
                    try:
                        update_data = {
                            "nom_complet": f"{m_nom.strip().upper()} {m_prenom.strip().capitalize()}", "sexe": m_sexe, 
                            "date_naissance": str(m_date_naiss), "type_piece": m_type_piece, "num_piece": m_num_piece, 
                            "poste": m_poste, "salaire_mensuel": float(m_salaire), "date_integration": str(m_date_int), 
                            "num_ss": m_num_ss
                        }
                        res = supabase.table("employes").update(update_data).eq("id", emp_a_modifier["id"]).execute()
                        if res.data:
                            for i, e in enumerate(st.session_state["liste_employes"]):
                                if e["id"] == emp_a_modifier["id"]:
                                    maj_emp = res.data[0]
                                    maj_emp.update({'telephone': m_telephone, 'porte_acces': m_porte_acces, 'lieu_deliv': m_lieu_deliv, 'date_deliv': str(m_date_deliv)})
                                    st.session_state["liste_employes"][i] = maj_emp
                                    break
                            st.success("✅ Mis à jour !")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
                
                if btn_supprimer:
                    try:
                        supabase.table("employes").delete().eq("id", emp_a_modifier["id"]).execute()
                        st.session_state["liste_employes"] = [e for e in st.session_state["liste_employes"] if e["id"] != emp_a_modifier["id"]]
                        st.success(f"🗑️ Supprimé.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        else:
            st.info("Aucun employé.")

# --- TAB 2: POINTAGE & PAIE ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        c_mois, c_annee = st.columns(2)
        mois_select = c_mois.selectbox("Mois", range(1, 13), index=datetime.now().month - 1, format_func=lambda x: calendar.month_name[x].capitalize())
        annee_select = c_annee.selectbox("Année", range(2020, 2035), index=datetime.now().year - 2020)
        
        _, num_days = calendar.monthrange(annee_select, mois_select)
        jours_fr = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
        jours_feries_fixes = [(1, 1), (1, 12), (5, 1), (7, 5), (11, 1)]
        
        donnees_pointage = [{
            "Employé": e.get('nom_complet', ''),
            "Poste": e.get('poste', ''),
            "Salaire (Base)": float(e.get('salaire_mensuel', 0.0)),
            **{str(j): "F" if (mois_select, j) in jours_feries_fixes else "P" for j in range(1, num_days + 1)}
        } for e in employes]
            
        df_pt = pd.DataFrame(donnees_pointage)
        
        st.markdown("#### Grille de Présence")
        st.caption("P : Présent | P/2 : Demi-journée | AI : Absence Irrégulière | AA : Absence Autorisée | F : Férié")
        
        col_config = {"Employé": st.column_config.TextColumn(disabled=True),
                      "Poste": st.column_config.TextColumn(disabled=True),
                      "Salaire (Base)": None} 
        for jour in range(1, num_days + 1):
            col_config[str(jour)] = st.column_config.SelectboxColumn(options=["P", "P/2", "AI", "AA", "F"], default="P")
            
        df_edit = st.data_editor(df_pt, column_config=col_config, hide_index=True, use_container_width=True)
        
        jours_cols = [str(j) for j in range(1, num_days + 1)]
        
        df_edit["Travaillés (j)"] = df_edit[jours_cols].apply(lambda x: x.isin(["P", "F"]).sum() + (x == "P/2").sum() * 0.5, axis=1)
        df_edit["Absents (j)"] = df_edit[jours_cols].apply(lambda x: x.isin(["AI", "AA"]).sum() + (x == "P/2").sum() * 0.5, axis=1)
        df_edit["Salaire Net (DA)"] = (df_edit["Salaire (Base)"] / 30) * df_edit["Travaillés (j)"]
        
        st.divider()
        c_met1, c_met2 = st.columns(2)
        c_met1.metric("Masse Salariale Nette", f"{df_edit['Salaire Net (DA)'].sum():,.2f} DA")
        c_met2.metric("Effectif Mensuel", len(df_edit))
        
        df_paie_display = df_edit[["Employé", "Poste", "Travaillés (j)", "Absents (j)", "Salaire (Base)", "Salaire Net (DA)"]]
        st.dataframe(df_paie_display, use_container_width=True, hide_index=True)
        
        nom_mois_str = calendar.month_name[mois_select].capitalize()

        # GÉNÉRATION EXCEL POINTAGE
        out_pt = io.BytesIO()
        workbook_pt = xlsxwriter.Workbook(out_pt, {'in_memory': True})
        ws_pt = workbook_pt.add_worksheet(f'Pointage_{nom_mois_str[:3]}-{str(annee_select)[-2:]}')
        
        fmt_bold = workbook_pt.add_format({'bold': True, 'valign': 'vcenter'})
        fmt_center_border = workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook_pt.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#f3f4f6'})
        
        ws_pt.set_row(2, 25)
        ws_pt.write('B3', societe_nom, fmt_bold)
        ws_pt.write('D3', f'POINTAGE {nom_mois_str.upper()} {annee_select}', fmt_bold)

        ws_pt.set_row(3, 16); ws_pt.set_row(4, 20)
        ws_pt.write('A5', 'N°', fmt_header); ws_pt.write('B5', 'Nom Complet', fmt_header); ws_pt.write('C5', 'Poste', fmt_header)
        ws_pt.set_column('A:A', 5); ws_pt.set_column('B:B', 30); ws_pt.set_column('C:C', 20)
        ws_pt.set_column('D:AH', 5)

        for i in range(num_days):
            ws_pt.write(3, 3 + i, i+1, fmt_header)
            ws_pt.write(4, 3 + i, jours_fr[date(annee_select, mois_select, i+1).weekday()], fmt_header)

        fmt_nom = workbook_pt.add_format({'valign': 'vcenter', 'border': 1, 'align': 'left'})
        for row_idx, row in df_edit.iterrows():
            r = 5 + row_idx
            ws_pt.write(r, 0, row_idx + 1, fmt_center_border)
            ws_pt.write(r, 1, row['Employé'], fmt_nom)
            ws_pt.write(r, 2, row['Poste'], fmt_nom)
            for i in range(num_days): ws_pt.write(r, 3 + i, row[str(i+1)], fmt_center_border)

        workbook_pt.close()

        # GÉNÉRATION EXCEL SALAIRES
        out_paie = io.BytesIO()
        workbook_paie = xlsxwriter.Workbook(out_paie, {'in_memory': True})
        ws_paie = workbook_paie.add_worksheet('Salaires')
        
        fmt_titre = workbook_paie.add_format({'bold': True, 'font_size': 14, 'align': 'left'})
        fmt_hdr = workbook_paie.add_format({'bold': True, 'border': 1, 'bg_color': '#f3f4f6', 'align': 'center'})
        fmt_txt = workbook_paie.add_format({'border': 1, 'align': 'left'})
        fmt_num = workbook_paie.add_format({'border': 1, 'align': 'center'})
        fmt_mnt = workbook_paie.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0.00'})

        ws_paie.write(1, 0, f"Salaires : {nom_mois_str.upper()} {annee_select} - {societe_nom}", fmt_titre)
        entetes = ["Employé", "Poste", "Travaillés (j)", "Absents (j)", "Salaire Base", "Net à Payer"]
        for c, h in enumerate(entetes): ws_paie.write(3, c, h, fmt_hdr)

        ws_paie.set_column('A:A', 30); ws_paie.set_column('B:B', 20)
        ws_paie.set_column('C:D', 15); ws_paie.set_column('E:F', 18)

        for row_idx, row in df_paie_display.iterrows():
            r = row_idx + 4
            ws_paie.write(r, 0, row['Employé'], fmt_txt)
            ws_paie.write(r, 1, row['Poste'], fmt_txt)
            ws_paie.write(r, 2, row['Travaillés (j)'], fmt_num)
            ws_paie.write(r, 3, row['Absents (j)'], fmt_num)
            ws_paie.write(r, 4, row['Salaire (Base)'], fmt_mnt)
            ws_paie.write(r, 5, row['Salaire Net (DA)'], fmt_mnt)

        workbook_paie.close()
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_dl1, c_dl2 = st.columns(2)
        c_dl1.download_button("Export Pointage (Excel)", data=out_pt.getvalue(), file_name=f"Pointage_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="secondary", use_container_width=True)
        c_dl2.download_button("Export Salaires (Excel)", data=out_paie.getvalue(), file_name=f"Salaires_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="primary", use_container_width=True)
        
    else:
        st.info("⚠️ Veuillez ajouter des salariés pour gérer le pointage.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3 & 4: AUTRES MODULES ---
with tab_docs:
    st.info("🚧 **Module Documents en cours de finalisation.**")

with tab_paie:
    st.info("🚧 **Simulateur de Paie avancé en développement.**")
