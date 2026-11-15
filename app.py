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
    st.session_state["admin_pwd"] = "admin" 

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

# --- TAB 1: GESTION DES SALARIÉS (INTÉGRATION DU CANEVAS) ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    sub_add, sub_edit, sub_list = st.tabs(["➕ Nouveau Salarié", "✏️ Gérer les Profils", "📋 Registre du Personnel"])
    
    with sub_add:
        with st.form("form_add_salarie", clear_on_submit=True):
            st.markdown("#### Informations Personnelles & Identification (Canevas)")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                nom = st.text_input("Nom *")
                prenom = st.text_input("Prénom(s) *")
                sexe = st.selectbox("Sexe", ["H", "F"])
                date_naiss = st.date_input("Date Naissance", value=date(1990, 1, 1), min_value=date(1940, 1, 1), max_value=date.today())
            with c2:
                type_piece = st.selectbox("Type pièce d'identité *", ["CIN", "PASSPORT", "PERMIS DE CONDUIRE"])
                num_piece = st.text_input("Numéro pièce d'identité *")
                date_deliv = st.date_input("Date de délivrance", value=date.today(), min_value=date(1990, 1, 1))
                lieu_deliv = st.text_input("Lieu de délivrance *")
            with c3:
                num_ss = st.text_input("N° Assurance (CNAS)")
                telephone = st.text_input("N° Téléphone")
                porte_acces = st.selectbox("Porte d'entrée (Accès)", ["P1", "P2", "P3"])
            with c4:
                poste = st.text_input("Poste / Fonction *")
                salaire = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
                date_int = st.date_input("Date Intégration", value=date.today())
                
            if st.form_submit_button("💾 Ajouter à la base de données", type="primary"):
                if nom and prenom and num_piece and lieu_deliv and poste:
                    try:
                        nom_complet = f"{nom.strip().upper()} {prenom.strip().upper()}"
                        new_data = {
                            "entreprise_id": entreprise_id, "nom_complet": nom_complet, "sexe": sexe, 
                            "date_naissance": str(date_naiss), "type_piece": type_piece, "num_piece": num_piece, 
                            "poste": poste, "salaire_mensuel": float(salaire), "date_integration": str(date_int), 
                            "num_ss": num_ss, "statut": "Actif"
                            # Note: Supabase n'acceptera que les colonnes déjà créées. 
                            # Si lieu_deliv, telephone ou porte_acces provoquent une erreur, ils devront être ajoutés à la BDD.
                            # Pour éviter un crash de la BDD actuelle, ils sont gardés dans le formulaire local.
                        }
                        res = supabase.table("employes").insert(new_data).execute()
                        if res.data:
                            # Sauvegarde des champs additionnels en mémoire session pour l'utilisation immédiate
                            employe_cree = res.data[0]
                            employe_cree['telephone'] = telephone
                            employe_cree['porte_acces'] = porte_acces
                            employe_cree['lieu_deliv'] = lieu_deliv
                            employe_cree['date_deliv'] = str(date_deliv)
                            
                            st.session_state["liste_employes"].append(employe_cree) 
                            st.success("✅ Salarié ajouté avec succès !")
                            st.rerun() 
                    except Exception as e:
                        st.error(f"Erreur d'insertion (Vérifiez les colonnes Supabase) : {e}")
                else:
                    st.error("⚠️ Veuillez remplir les champs obligatoires (*).")

    with sub_edit:
        if employes:
            emp_a_modifier = st.selectbox("Rechercher un employé :", employes, format_func=lambda x: x.get("nom_complet", "Inconnu"))
            with st.form("form_edit_salarie"):
                st.markdown("#### Mise à jour du dossier")
                c1, c2, c3, c4 = st.columns(4)
                
                # Découpage basique du nom complet s'il n'est pas séparé en BDD
                noms_split = emp_a_modifier.get("nom_complet", "").split(" ", 1)
                m_nom_val = noms_split[0]
                m_prenom_val = noms_split[1] if len(noms_split) > 1 else ""

                with c1:
                    m_nom = st.text_input("Nom *", value=m_nom_val)
                    m_prenom = st.text_input("Prénom(s) *", value=m_prenom_val)
                    m_sexe = st.selectbox("Sexe", ["H", "F"], index=0 if emp_a_modifier.get("sexe") == "H" else 1)
                    m_date_naiss = st.date_input("Date Naissance", value=parse_date(emp_a_modifier.get("date_naissance"), 1990))
                with c2:
                    options_piece = ["CIN", "PASSPORT", "PERMIS DE CONDUIRE"]
                    val_piece = emp_a_modifier.get("type_piece", "CIN")
                    idx_piece = options_piece.index(val_piece) if val_piece in options_piece else 0
                    m_type_piece = st.selectbox("Type Pièce *", options_piece, index=idx_piece)
                    m_num_piece = st.text_input("Numéro Pièce *", value=emp_a_modifier.get("num_piece", ""))
                    m_date_deliv = st.date_input("Date de délivrance", value=parse_date(emp_a_modifier.get("date_deliv"), 2020))
                    m_lieu_deliv = st.text_input("Lieu de délivrance *", value=emp_a_modifier.get("lieu_deliv", ""))
                with c3:
                    m_num_ss = st.text_input("N° Assurance (CNAS)", value=emp_a_modifier.get("num_ss", ""))
                    m_telephone = st.text_input("N° Téléphone", value=emp_a_modifier.get("telephone", ""))
                    options_porte = ["P1", "P2", "P3"]
                    val_porte = emp_a_modifier.get("porte_acces", "P1")
                    idx_porte = options_porte.index(val_porte) if val_porte in options_porte else 0
                    m_porte_acces = st.selectbox("Porte d'entrée (Accès)", options_porte, index=idx_porte)
                with c4:
                    m_poste = st.text_input("Poste / Fonction *", value=emp_a_modifier.get("poste", ""))
                    m_salaire = st.number_input("Salaire Base (DA)", value=float(emp_a_modifier.get("salaire_mensuel", 50000.0)), step=5000.0)
                    m_date_int = st.date_input("Date Intégration", value=parse_date(emp_a_modifier.get("date_integration"), 2023))
                
                col_btn1, col_btn2 = st.columns(2)
                btn_modifier = col_btn1.form_submit_button("✏️ Mettre à jour", type="primary", use_container_width=True)
                btn_supprimer = col_btn2.form_submit_button("❌ Supprimer définitivement", use_container_width=True)
                
                if btn_modifier:
                    if m_nom and m_prenom and m_poste and m_num_piece:
                        try:
                            m_nom_complet = f"{m_nom.strip().upper()} {m_prenom.strip().upper()}"
                            update_data = {
                                "nom_complet": m_nom_complet, "sexe": m_sexe, "date_naissance": str(m_date_naiss), 
                                "type_piece": m_type_piece, "num_piece": m_num_piece, "poste": m_poste, 
                                "salaire_mensuel": float(m_salaire), "date_integration": str(m_date_int), 
                                "num_ss": m_num_ss
                            }
                            res = supabase.table("employes").update(update_data).eq("id", emp_a_modifier["id"]).execute()
                            if res.data:
                                for i, e in enumerate(st.session_state["liste_employes"]):
                                    if e["id"] == emp_a_modifier["id"]:
                                        maj_emp = res.data[0]
                                        maj_emp['telephone'] = m_telephone
                                        maj_emp['porte_acces'] = m_porte_acces
                                        maj_emp['lieu_deliv'] = m_lieu_deliv
                                        maj_emp['date_deliv'] = str(m_date_deliv)
                                        st.session_state["liste_employes"][i] = maj_emp
                                        break
                                st.success("✅ Dossier mis à jour !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur de mise à jour : {e}")
                if btn_supprimer:
                    try:
                        supabase.table("employes").delete().eq("id", emp_a_modifier["id"]).execute()
                        st.session_state["liste_employes"] = [e for e in st.session_state["liste_employes"] if e["id"] != emp_a_modifier["id"]]
                        st.success(f"🗑️ Salarié supprimé.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
        else:
            st.info("Aucun employé enregistré.")

    with sub_list:
        if employes:
            df_emp = pd.DataFrame(employes)
            # Affichage des colonnes principales
            cols = ['nom_complet', 'poste', 'num_piece', 'num_ss', 'telephone', 'porte_acces', 'salaire_mensuel']
            cols_ex = [col for col in cols if col in df_emp.columns]
            st.dataframe(df_emp[cols_ex], use_container_width=True)
        else:
            st.info("ℹ️ Le registre est vide.")
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: POINTAGE & PAIE (EXCEL 100% FIDÈLE ET DYNAMIQUE) ---
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
        
        # Initialisation Pointage
        donnees_pointage = []
        for e in employes:
            ligne = {
                "Nom et Prénom": e.get('nom_complet', ''),
                "Fonction": e.get('poste', ''),
                "Salaire Base": float(e.get('salaire_mensuel', 0.0))
            }
            for jour in range(1, num_days + 1):
                ligne[str(jour)] = "P"
            donnees_pointage.append(ligne)
            
        df_pt = pd.DataFrame(donnees_pointage)
        
        st.markdown("### ✍️ Saisie du pointage rapide")
        st.markdown("**Légende :** `P` (Présent) | `P/2` (Demi-journée) | `AI` (Absence Irrégulière) | `AA` (Absence Autorisée)")
        
        col_config = {"Nom et Prénom": st.column_config.TextColumn(disabled=True),
                      "Fonction": st.column_config.TextColumn(disabled=True),
                      "Salaire Base": None} 
        
        for jour in range(1, num_days + 1):
            col_config[str(jour)] = st.column_config.SelectboxColumn(options=["P", "P/2", "AI", "AA"], default="P")
            
        df_edit = st.data_editor(df_pt, column_config=col_config, hide_index=True, use_container_width=True)
        
        # Calcul de la Paie
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
        
        nom_mois_str = calendar.month_name[mois_select].capitalize()

        # GÉNÉRATION EXCEL 1 : POINTAGE (100% FIDÈLE AU MODÈLE D'ORIGINE)
        out_pt = io.BytesIO()
        workbook_pt = xlsxwriter.Workbook(out_pt, {'in_memory': True})
        ws_pt = workbook_pt.add_worksheet(f'Pointage {nom_mois_str[:3]}-{str(annee_select)[-2:]}')
        
        fmt_border = workbook_pt.add_format({'border': 1})
        fmt_bold = workbook_pt.add_format({'bold': True, 'valign': 'vcenter'})
        fmt_center_border = workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
        fmt_header = workbook_pt.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        
        ws_pt.set_row(0, 33)
        ws_pt.write('D1', 'P', fmt_center_border); ws_pt.write('E1', 'Present', workbook_pt.add_format({'valign': 'vcenter'}))
        ws_pt.write('G1', 'P/2', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFFF00'}))
        ws_pt.write('H1', 'Present\nDemi journé', workbook_pt.add_format({'valign': 'vcenter', 'text_wrap': True}))
        ws_pt.write('J1', 'AA', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FF9900'}))
        ws_pt.write('K1', 'Absence Autorisé', workbook_pt.add_format({'valign': 'vcenter'}))
        ws_pt.write('M1', 'AI', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FF0000'}))
        ws_pt.write('N1', 'Absence Irreguliere', workbook_pt.add_format({'valign': 'vcenter'}))
        ws_pt.write('P1', 'M', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#00B0F0'}))
        ws_pt.write('Q1', 'Mission', workbook_pt.add_format({'valign': 'vcenter'}))
        ws_pt.write('S1', 'CR', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#66FF33'}))
        ws_pt.write('T1', 'Congé\nRécuperation', workbook_pt.add_format({'valign': 'vcenter', 'text_wrap': True}))
        ws_pt.write('V1', 'F', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FF00FF'}))
        ws_pt.write('W1', 'Jour Férier', workbook_pt.add_format({'valign': 'vcenter'}))
        ws_pt.write('Y1', 'FRT', workbook_pt.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#A6A6A6'}))
        ws_pt.write('Z1', 'Fin de relation\n de travail', workbook_pt.add_format({'valign': 'vcenter', 'text_wrap': True}))

        ws_pt.set_row(2, 33)
        ws_pt.write('B3', societe_nom, workbook_pt.add_format({'bold': True, 'valign': 'vcenter', 'border': 1, 'align': 'center'}))
        ws_pt.write('D3', 'POINTAGE MOIS DE :', fmt_bold)
        ws_pt.write('H3', nom_mois_str.upper(), fmt_bold)
        ws_pt.write('K3', annee_select, fmt_bold)
        ws_pt.write('AI3', 'NB. JRS OUVR', fmt_bold)
        formule_jo = f'=NETWORKDAYS.INTL(DATE({annee_select},{mois_select},1),EOMONTH(DATE({annee_select},{mois_select},1),0),"0000110")'
        ws_pt.write('AJ3', formule_jo, fmt_bold)

        ws_pt.set_row(3, 16); ws_pt.set_row(4, 25)
        ws_pt.write('A5', 'N°', fmt_header); ws_pt.write('B5', 'NOM Prenom', fmt_header); ws_pt.write('C5', 'Fonction', fmt_header)
        ws_pt.set_column('A:A', 6); ws_pt.set_column('B:B', 35); ws_pt.set_column('C:C', 25)
        ws_pt.set_column('D:AH', 5); ws_pt.set_column('AI:AM', 12)

        for i in range(num_days):
            col = 3 + i
            dt = date(annee_select, mois_select, i+1)
            ws_pt.write(3, col, i+1, fmt_header)
            ws_pt.write(4, col, jours_fr[dt.weekday()], fmt_header)
            
        ws_pt.write('AI5', 'Presence', fmt_header); ws_pt.write('AJ5', 'Absence', fmt_header)
        ws_pt.write('AK5', 'Mission', fmt_header); ws_pt.write('AL5', 'Férier', fmt_header); ws_pt.write('AM5', 'Départ (FRT)', fmt_header)

        fmt_nom = workbook_pt.add_format({'valign': 'vcenter', 'border': 1, 'align': 'left'})
        
        for row_idx, row in df_export.iterrows():
            r = 5 + row_idx
            ws_pt.set_row(r, 25)
            ws_pt.write(r, 0, f"{row_idx + 1:02d}", fmt_center_border)
            ws_pt.write(r, 1, row['Nom et Prénom'], fmt_nom)
            ws_pt.write(r, 2, row['Fonction'], fmt_nom)
            
            for i in range(num_days): ws_pt.write(r, 3 + i, row[str(i+1)], fmt_center_border)
                
            ex_r = r + 1 
            ws_pt.write_formula(r, 34, f'=COUNTIF(D{ex_r}:AH{ex_r},"P")+COUNTIF(D{ex_r}:AH{ex_r},"P/2")/2+AK{ex_r}+AL{ex_r}', fmt_center_border)
            ws_pt.write_formula(r, 35, f'=COUNTIF(D{ex_r}:AH{ex_r},"AI")+COUNTIF(D{ex_r}:AH{ex_r},"AA")+COUNTIF(D{ex_r}:AH{ex_r},"P/2")/2', fmt_center_border)
            ws_pt.write_formula(r, 36, f'=COUNTIF(D{ex_r}:AH{ex_r},"M")', fmt_center_border)
            ws_pt.write_formula(r, 37, f'=COUNTIF(D{ex_r}:AH{ex_r},"F")', fmt_center_border)
            ws_pt.write_formula(r, 38, f'=IF(COUNTIF(D{ex_r}:AH{ex_r},"FRT")>0,1,0)', fmt_center_border)

        derniere_ligne = 5 + len(df_export)
        plage = f'D6:AH{derniere_ligne}'
        ws_pt.conditional_format(plage, {'type': 'cell', 'criteria': '==', 'value': '"P/2"', 'format': workbook_pt.add_format({'bg_color': '#FFFF00'})})
        ws_pt.conditional_format(plage, {'type': 'cell', 'criteria': '==', 'value': '"AA"', 'format': workbook_pt.add_format({'bg_color': '#FF9900'})})
        ws_pt.conditional_format(plage, {'type': 'cell', 'criteria': '==', 'value': '"AI"', 'format': workbook_pt.add_format({'bg_color': '#FF0000', 'font_color': 'white'})})
        ws_pt.conditional_format(plage, {'type': 'cell', 'criteria': '==', 'value': '"FRT"', 'format': workbook_pt.add_format({'bg_color': '#A6A6A6', 'font_color': 'white'})})
        ws_pt.conditional_format(plage, {'type': 'formula', 'criteria': '=OR(D$5="ven.", D$5="sam.")', 'format': workbook_pt.add_format({'bg_color': '#F2F2F2'})})

        workbook_pt.close()

        # GÉNÉRATION EXCEL 2 : ÉTAT DES SALAIRES
        out_paie = io.BytesIO()
        workbook_paie = xlsxwriter.Workbook(out_paie, {'in_memory': True})
        ws_paie = workbook_paie.add_worksheet('État des Salaires')

        fmt_titre_paie = workbook_paie.add_format({'bold': True, 'font_size': 15, 'font_color': 'white', 'bg_color': '#1F4E78', 'align': 'center', 'valign': 'vcenter', 'border': 1})
        fmt_header_paie = workbook_paie.add_format({'bold': True, 'bg_color': '#D9E1F2', 'align': 'center', 'valign': 'vcenter', 'border': 1})
        fmt_data_texte = workbook_paie.add_format({'valign': 'vcenter', 'border': 1, 'align': 'left'})
        fmt_data_num = workbook_paie.add_format({'valign': 'vcenter', 'border': 1, 'align': 'center'})
        fmt_data_argent = workbook_paie.add_format({'valign': 'vcenter', 'border': 1, 'align': 'right', 'num_format': '#,##0.00 "DA"'})

        ws_paie.set_row(0, 40)
        ws_paie.merge_range("A1:F1", f"ÉTAT DES SALAIRES - {nom_mois_str.upper()} {annee_select} - {societe_nom}", fmt_titre_paie)

        entetes_paie = ["Nom et Prénom", "Fonction", "Jours Travaillés", "Jours Absents", "Salaire Base", "Salaire Net Estimé"]
        for col_num, entete in enumerate(entetes_paie):
            ws_paie.write(1, col_num, entete, fmt_header_paie)

        ws_paie.set_column('A:A', 35); ws_paie.set_column('B:B', 25)
        ws_paie.set_column('C:D', 18); ws_paie.set_column('E:F', 22)
        ws_paie.set_row(1, 25)

        for row_idx, row in df_paie_display.iterrows():
            r = row_idx + 2
            ws_paie.set_row(r, 22)
            ws_paie.write(r, 0, row['Nom et Prénom'], fmt_data_texte)
            ws_paie.write(r, 1, row['Fonction'], fmt_data_texte)
            ws_paie.write(r, 2, row['Jours Travaillés'], fmt_data_num)
            ws_paie.write(r, 3, row['Jours Absents'], fmt_data_num)
            ws_paie.write(r, 4, row['Salaire Base'], fmt_data_argent)
            ws_paie.write(r, 5, row['Salaire Net Estimé'], fmt_data_argent)

        workbook_paie.close()
        
        c_dl1, c_dl2 = st.columns(2)
        c_dl1.download_button("📥 Télécharger Pointage (Format Exact)", data=out_pt.getvalue(), file_name=f"Pointage_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="primary", use_container_width=True)
        c_dl2.download_button("📥 Télécharger État des Salaires (Pro)", data=out_paie.getvalue(), file_name=f"Salaires_{nom_mois_str}_{annee_select}.xlsx", mime="application/vnd.ms-excel", type="secondary", use_container_width=True)
        
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
