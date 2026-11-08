import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
import io

# --- 1. CONFIGURATION & STYLES GLOBAUX ---
st.set_page_config(
    page_title="Optima RH - Solution SaaS RH & Paie",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles Clean & Professionnels
st.markdown("""
    <style>
        /* Styles des métriques et boutons */
        .stMetric { background-color: var(--secondary-background-color); padding: 18px; border-radius: 12px; border: 1px solid rgba(128, 128, 128, 0.2); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        .stButton>button { border-radius: 8px; height: 45px; font-weight: 600; }
        
        /* Centrage visuel pour la page de connexion */
        .login-header {
            text-align: center;
            margin-bottom: 30px;
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

if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None

# --- 3. LANDING PAGE MARKETING & CONNEXION (PAGE UNIQUE CENTRÉE) ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    # Utilisation de 3 colonnes pour centrer le formulaire (vide, centre, vide)
    _, col_centre, _ = st.columns([1, 1.2, 1])

    with col_centre:
        st.markdown('''
            <div class="login-header">
                <h1 style="font-size: 3.5rem; font-weight: 800; margin-bottom: 0;">⚡ Optima RH</h1>
                <p style="font-size: 1.1rem; opacity: 0.8; margin-top: 5px;">La gestion du personnel et de la paie, réinventée.</p>
            </div>
        ''', unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 Connexion", "📝 Créer un Espace"])

        with tab_login:
            with st.form("form_connexion_client"):
                nom_saisi = st.text_input("Nom de votre société", key="login_nom")
                mdp_saisi = st.text_input("Mot de passe", type="password", key="login_mdp")
                if st.form_submit_button("Se Connecter", type="primary", use_container_width=True):
                    if nom_saisi and mdp_saisi:
                        res = supabase.table("entreprises").select("*").ilike("nom", nom_saisi.strip()).execute()
                        if res.data:
                            compte = res.data[0]
                            if mdp_saisi == (compte.get("mot_de_passe") or "123456"):
                                st.session_state["connected_company"] = compte
                                st.success("Connexion réussie !")
                                st.rerun()
                            else:
                                st.error("Mot de passe incorrect.")
                        else:
                            st.error("Aucune entreprise trouvée à ce nom.")

        with tab_signup:
            with st.form("form_nouveau_compte", clear_on_submit=True):
                nouveau_nom = st.text_input("Nom de la société *")
                nouveau_mdp = st.text_input("Mot de passe *", type="password")
                if st.form_submit_button("Déployer mon Espace", use_container_width=True):
                    if nouveau_nom and nouveau_mdp:
                        verif = supabase.table("entreprises").select("id").ilike("nom", nouveau_nom.strip()).execute()
                        if verif.data:
                            st.error("Cette entreprise existe déjà.")
                        else:
                            supabase.table("entreprises").insert({"nom": nouveau_nom.strip(), "mot_de_passe": nouveau_mdp}).execute()
                            st.success(f"Compte '{nouveau_nom}' créé ! Vous pouvez vous connecter.")
                            
    st.stop()

# --- 4. ESPACE DE TRAVAIL CLIENT ---
entreprise_active = st.session_state["connected_company"]
entreprise_id = entreprise_active["id"]
nom_client = entreprise_active["nom"]

with st.sidebar:
    st.title("⚡ Optima RH")
    st.write(f"🏢 **{nom_client}**")
    st.divider()
    with st.expander("🔑 Paramètres du compte"):
        with st.form("form_change_mdp"):
            nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
            if st.form_submit_button("Mettre à jour"):
                if len(nouveau_mdp) >= 4:
                    supabase.table("entreprises").update({"mot_de_passe": nouveau_mdp}).eq("id", entreprise_id).execute()
                    st.session_state["connected_company"]["mot_de_passe"] = nouveau_mdp
                    st.success("Mot de passe modifié !")
    with st.expander("⚠️ Zone de danger"):
        if st.button("Supprimer mon entreprise", type="primary"):
            supabase.table("entreprises").delete().eq("id", entreprise_id).execute()
            st.session_state["connected_company"] = None
            st.rerun()
    st.divider()
    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.rerun()

st.title(f"Tableau de Bord — {nom_client}")

res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
liste_employes = res_emp.data if res_emp.data else []
df_emp = pd.DataFrame(liste_employes)

tab_dash, tab_emp, tab_pointage = st.tabs(["📊 Vue Générale", "👤 Gestion du Personnel", "📅 Pointage & Paie Mensuelle"])

# --- TAB 1 : VUE GÉNÉRALE ---
with tab_dash:
    nb_employes = len(liste_employes)
    nb_actifs = len([e for e in liste_employes if e.get("statut") == "Actif"]) if nb_employes > 0 else 0
    
    c1, c2 = st.columns(2)
    c1.metric("Effectif Total", f"{nb_employes} Salariés")
    c2.metric("En activité", f"{nb_actifs} Actifs")
    st.divider()
    
    if not df_emp.empty:
        col_titre, col_btn = st.columns([3, 1])
        col_titre.subheader("Situation du personnel")
        
        def generer_excel_personnel(df, societe):
            output = io.BytesIO()
            df_pro = df[['nom_complet', 'poste', 'projet_affectation', 'date_integration', 'date_depart', 'statut', 'salaire_mensuel']].copy()
            df_pro.columns = ['Nom & Prénom', 'Poste', 'Projet/Chantier', 'Date Intégration', 'Date Départ', 'Statut', 'Salaire Mensuel (DA)']
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_pro.to_excel(writer, index=False, sheet_name='Personnel', startrow=3)
                workbook = writer.book
                worksheet = writer.sheets['Personnel']
                titre_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
                date_format = workbook.add_format({'italic': True, 'align': 'left'})
                header_format = workbook.add_format({'bold': True, 'bg_color': '#1E293B', 'font_color': 'white', 'border': 1, 'align': 'center'})
                cell_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
                money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})
                signature_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'top', 'border': 1, 'text_wrap': True})
                
                worksheet.merge_range('A1:G1', f'ÉTAT DE SITUATION DU PERSONNEL - {societe.upper()}', titre_format)
                worksheet.write('A2', f"Date d'édition : {date.today().strftime('%d/%m/%Y')}", date_format)
                for col_num, value in enumerate(df_pro.columns.values):
                    worksheet.write(3, col_num, value, header_format)
                    if 'Salaire' in value: worksheet.set_column(col_num, col_num, 20, money_format)
                    elif 'Date' in value: worksheet.set_column(col_num, col_num, 15, cell_format)
                    else: worksheet.set_column(col_num, col_num, 22, cell_format)
                last_row = len(df_pro) + 4
                worksheet.merge_range(last_row + 2, 5, last_row + 5, 6, "Cachet et Signature :\n(Chef de Projet / RH)", signature_format)
            return output.getvalue()
        
        for col in ['statut', 'projet_affectation', 'date_integration', 'date_depart']:
            if col not in df_emp.columns:
                df_emp[col] = '' if 'date' in col else ('Actif' if col == 'statut' else 'Non affecté')
            else:
                df_emp[col] = df_emp[col].fillna('' if 'date' in col else ('Actif' if col == 'statut' else 'Non affecté'))
        
        excel_pers = generer_excel_personnel(df_emp, nom_client)
        col_btn.download_button("📥 Exporter le Personnel", data=excel_pers, file_name=f"Situation_Personnel_{nom_client}.xlsx", mime="application/vnd.ms-excel", type="primary", use_container_width=True)
        
        st.dataframe(df_emp[['nom_complet', 'poste', 'projet_affectation', 'date_integration', 'date_depart', 'statut', 'salaire_mensuel']], use_container_width=True, hide_index=True)
    else:
        st.info("Aucun employé inscrit. Allez dans 'Gestion du Personnel' pour commencer.")

# --- TAB 2 : GESTION DU PERSONNEL ---
with tab_emp:
    options_statuts = ["Actif", "En congé", "Arrêt maladie", "Fin de contrat", "Départ"]
    col_add, col_edit = st.columns(2, gap="large")
    
    with col_add:
        st.subheader("➕ Ajouter un Salarié")
        with st.form("form_new", clear_on_submit=True):
            nom = st.text_input("Nom & Prénom *")
            poste = st.text_input("Poste *")
            projet = st.text_input("Projet d'affectation *", value="Siège")
            date_int = st.date_input("Date d'intégration *", value=date.today())
            statut = st.selectbox("Statut initial", options_statuts)
            sal = st.number_input("Salaire Mensuel (DA) *", min_value=10000.0, value=60000.0, step=5000.0)
            
            if st.form_submit_button("Ajouter à l'effectif", type="primary"):
                if nom and poste and projet:
                    supabase.table("employes").insert({
                        "entreprise_id": entreprise_id, "nom_complet": nom, "poste": poste, 
                        "projet_affectation": projet, "date_integration": str(date_int),
                        "statut": statut, "salaire_mensuel": float(sal), "salaire_journalier": float(sal)/26
                    }).execute()
                    st.success(f"{nom} ajouté avec succès !")
                    st.rerun()
                else:
                    st.error("Veuillez remplir les champs obligatoires (*)")

    with col_edit:
        st.subheader("✏️ Modifier / Supprimer")
        if liste_employes:
            emp_mod = st.selectbox("Sélectionner le salarié :", liste_employes, format_func=lambda x: f"{x['nom_complet']} ({x['poste']})")
            val_int = pd.to_datetime(emp_mod.get('date_integration')).date() if emp_mod.get('date_integration') else date.today()
            val_dep = pd.to_datetime(emp_mod.get('date_depart')).date() if emp_mod.get('date_depart') else None

            with st.form("form_edit"):
                m_nom = st.text_input("Nom & Prénom", emp_mod['nom_complet'])
                m_poste = st.text_input("Poste", emp_mod['poste'])
                m_proj = st.text_input("Projet d'affectation", emp_mod.get('projet_affectation', 'Siège'))
                col_d1, col_d2 = st.columns(2)
                m_d_int = col_d1.date_input("Date d'intégration", value=val_int)
                m_d_dep = col_d2.date_input("Date de départ", value=val_dep)
                statut_actuel = emp_mod.get('statut', 'Actif')
                idx_statut = options_statuts.index(statut_actuel) if statut_actuel in options_statuts else 0
                m_statut = st.selectbox("Statut", options_statuts, index=idx_statut)
                
                salaire_actuel = float(emp_mod.get('salaire_mensuel') or 60000.0)
                m_sal = st.number_input("Salaire Mensuel (DA)", min_value=10000.0, value=salaire_actuel, step=5000.0)
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.form_submit_button("💾 Sauvegarder"):
                    supabase.table("employes").update({
                        "nom_complet": m_nom, "poste": m_poste, "projet_affectation": m_proj, 
                        "date_integration": str(m_d_int) if m_d_int else None, "date_depart": str(m_d_dep) if m_d_dep else None,
                        "statut": m_statut, "salaire_mensuel": float(m_sal), "salaire_journalier": float(m_sal)/26
                    }).eq("id", emp_mod['id']).execute()
                    st.success("Modifications enregistrées !")
                    st.rerun()
                if c_btn2.form_submit_button("🗑️ Supprimer"):
                    supabase.table("employes").delete().eq("id", emp_mod['id']).execute()
                    st.rerun()

# --- TAB 3 : POINTAGE & PAIE ---
with tab_pointage:
    if liste_employes:
        sub_saisie, sub_historique = st.tabs(["📝 Saisie Quotidienne", "📊 Clôture & Paie Mensuelle"])
        
        with sub_saisie:
            st.info("💡 Par défaut, tout le monde est 'Présent'. Modifiez les statuts (Absent, Demi-Journée...), puis validez.")
            c_date, _ = st.columns([1, 2])
            date_p = c_date.date_input("Date du pointage", value=date.today())
            
            df_equipe = pd.DataFrame([{"id": e['id'], "Salarié": e['nom_complet'], "Projet": e.get('projet_affectation',''), "Statut": "Présent"} for e in liste_employes])
            df_edite = st.data_editor(
                df_equipe,
                column_config={"id": None, "Salarié": st.column_config.TextColumn(disabled=True), "Projet": st.column_config.TextColumn(disabled=True), "Statut": st.column_config.SelectboxColumn("Présence", options=["Présent", "Demi-Journée", "Absent", "Congé", "Maladie"], required=True)},
                hide_index=True, use_container_width=True
            )
            
            if st.button("💾 Valider le pointage de la journée", type="primary"):
                batch = [{"employe_id": int(r['id']), "date_pointage": str(date_p), "statut": r['Statut']} for _, r in df_edite.iterrows()]
                
                # Sécurité anti-doublon vérifiée : supprime l'ancien pointage du jour avant d'insérer le nouveau
                emp_ids = [int(r['id']) for _, r in df_edite.iterrows()]
                supabase.table("pointages").delete().in_("employe_id", emp_ids).eq("date_pointage", str(date_p)).execute()
                
                # Insertion des nouveaux pointages
                supabase.table("pointages").insert(batch).execute()
                st.success(f"✅ Pointage du {date_p.strftime('%d/%m/%Y')} enregistré avec succès !")
        
        with sub_historique:
            mois_dict = {"Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6, "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12}
            col_m, col_a, _ = st.columns([1, 1, 2])
            mois_nom = col_m.selectbox("Mois à clôturer", list(mois_dict.keys()), index=datetime.now().month - 1)
            annee = col_a.number_input("Année", min_value=2024, value=datetime.now().year)
            
            emp_ids = [e['id'] for e in liste_employes]
            res_pts = supabase.table("pointages").select("*").in_("employe_id", emp_ids).execute()
            df_tous_pts = pd.DataFrame(res_pts.data) if res_pts.data else pd.DataFrame()
            
            if not df_tous_pts.empty:
                df_tous_pts['date_pointage'] = pd.to_datetime(df_tous_pts['date_pointage'])
                df_mois = df_tous_pts[(df_tous_pts['date_pointage'].dt.month == mois_dict[mois_nom]) & (df_tous_pts['date_pointage'].dt.year == annee)]
                
                recap_paie = []
                for emp in liste_employes:
                    pts_emp = df_mois[df_mois['employe_id'] == emp['id']]
                    jours_complets = len(pts_emp[pts_emp['statut'] == 'Présent'])
                    demi_jours = len(pts_emp[pts_emp['statut'] == 'Demi-Journée'])
                    jours_absents_complets = len(pts_emp[~pts_emp['statut'].isin(['Présent', 'Demi-Journée'])])
                    
                    # Calculs stricts et vérifiés
                    total_jours_travailles = float(jours_complets + (demi_jours * 0.5))
                    total_jours_absents = float(jours_absents_complets + (demi_jours * 0.5))
                    sal_mensuel = float(emp.get('salaire_mensuel') or 0.0)
                    
                    # Base 26 jours ouvrables
                    paie_totale = total_jours_travailles * (sal_mensuel / 26.0)
                    
                    recap_paie.append({
                        "Nom & Prénom": emp['nom_complet'], 
                        "Projet": emp.get('projet_affectation', 'Non affecté'), 
                        "Salaire Base (DA)": sal_mensuel, 
                        "Jours Travaillés": total_jours_travailles, 
                        "Jours Absents": total_jours_absents, 
                        "Total à Payer (DA)": paie_totale
                    })
                
                df_recap = pd.DataFrame(recap_paie)
                
                def generer_excel_paie(df, mois, annee, societe):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name=f'Paie_{mois[:3]}_{annee}', startrow=3)
                        workbook = writer.book
                        worksheet = writer.sheets[f'Paie_{mois[:3]}_{annee}']
                        header_format = workbook.add_format({'bold': True, 'bg_color': '#2563EB', 'font_color': 'white', 'border': 1, 'align': 'center'})
                        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'valign': 'vcenter'})
                        cell_format = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter'})
                        worksheet.merge_range('A1:F1', f'ÉTAT DE PAIE - {societe.upper()} - {mois.upper()} {annee}', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
                        worksheet.write('A2', f"Édité le : {date.today().strftime('%d/%m/%Y')}", workbook.add_format({'italic': True}))
                        for col_num, value in enumerate(df.columns.values):
                            worksheet.write(3, col_num, value, header_format)
                            if 'Salaire' in value or 'Total' in value: worksheet.set_column(col_num, col_num, 20, money_format)
                            else: worksheet.set_column(col_num, col_num, 18, cell_format)
                        worksheet.set_column(0, 0, 25)
                    return output.getvalue()
                
                st.download_button(f"📥 Télécharger la Paie de {mois_nom} (Excel)", data=generer_excel_paie(df_recap, mois_nom, annee, nom_client), file_name=f"Fiche_Paie_{nom_client}_{mois_nom}_{annee}.xlsx", mime="application/vnd.ms-excel", type="primary")
                st.dataframe(df_recap, use_container_width=True, hide_index=True, column_config={"Salaire Base (DA)": st.column_config.NumberColumn(format="%.2f DA"), "Total à Payer (DA)": st.column_config.NumberColumn(format="%.2f DA")})
            else:
                st.info(f"Aucun pointage n'a encore été enregistré pour {mois_nom} {annee}.")