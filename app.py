import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Optima RH - Plateforme SaaS",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
        .stMetric {
            background-color: #1e222d;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #2e3545;
        }
        .stButton>button {
            border-radius: 8px;
            height: 45px;
            font-weight: bold;
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

# Initialisation de la session utilisateur
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None

# --- 3. SYSTÈME DE CONNEXION / INSCRIPTION DES ENTREPRISES ---
if st.session_state["connected_company"] is None:
    st.title("⚡ Optima RH — Accès Entreprise")
    st.caption("Connectez-vous à votre espace client pour gérer vos équipes.")
    
    col_login, col_signup = st.columns(2, gap="large")
    
    with col_login:
        st.subheader("🔑 Se connecter")
        res_ent = supabase.table("entreprises").select("*").execute()
        entreprises_dict = {e['nom']: e for e in res_ent.data} if res_ent.data else {}
        
        if entreprises_dict:
            nom_sel = st.selectbox("Sélectionner votre entreprise :", list(entreprises_dict.keys()))
            mdp_saisi = st.text_input("Mot de passe :", type="password", key="login_mdp")
            
            if st.button("Connexion", type="primary"):
                compte = entreprises_dict[nom_sel]
                mdp_attendu = compte.get("mot_de_passe") or "123456"
                if mdp_saisi == mdp_attendu:
                    st.session_state["connected_company"] = compte
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
        else:
            st.info("Aucune entreprise inscrite. Créez votre compte à droite.")

    with col_signup:
        st.subheader("📝 Créer un nouveau compte client")
        with st.form("form_nouveau_compte", clear_on_submit=True):
            nouveau_nom = st.text_input("Nom de la société (ex: SARL MAINA) *")
            nouveau_mdp = st.text_input("Créer un mot de passe *", type="password")
            
            if st.form_submit_button("Inscrire mon entreprise"):
                if nouveau_nom and nouveau_mdp:
                    supabase.table("entreprises").insert({
                        "nom": nouveau_nom,
                        "mot_de_passe": nouveau_mdp
                    }).execute()
                    st.success(f"Compte créé pour '{nouveau_nom}'. Vous pouvez vous connecter !")
                    st.rerun()
                else:
                    st.warning("Veuillez remplir tous les champs.")

    st.stop()

# --- 4. ESPACE DE TRAVAIL CLIENT ---
entreprise_active = st.session_state["connected_company"]
entreprise_id = entreprise_active["id"]
nom_client = entreprise_active["nom"]

with st.sidebar:
    st.title("⚡ Optima RH")
    st.write(f"🏢 **{nom_client}**")
    st.caption(f"ID Client: #{entreprise_id}")
    st.divider()
    if st.button("🚪 Se déconnecter"):
        st.session_state["connected_company"] = None
        st.rerun()

st.title(f"Tableau de Bord — {nom_client}")

res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
liste_employes = res_emp.data if res_emp.data else []
df_emp = pd.DataFrame(liste_employes)

tab_dash, tab_emp, tab_pointage, tab_docs = st.tabs([
    "📊 Vue Générale & KPIs", 
    "👤 Gestion du Personnel", 
    "📅 Pointage & Paie Automatique", 
    "📄 Documents & Canva"
])

# --- TAB 1 : VUE GÉNÉRALE & KPIS ---
with tab_dash:
    col1, col2, col3 = st.columns(3)
    nb_employes = len(liste_employes)
    total_jours = 0
    total_paie = 0
    
    if nb_employes > 0:
        emp_ids = [e['id'] for e in liste_employes]
        res_pt = supabase.table("pointages").select("*").in_("employe_id", emp_ids).eq("statut", "Présent").execute()
        total_jours = len(res_pt.data) if res_pt.data else 0
        
        for emp in liste_employes:
            pts = [p for p in (res_pt.data or []) if p['employe_id'] == emp['id']]
            sal_mensuel = float(emp.get('salaire_mensuel') or 0)
            sal_jour = sal_mensuel / 26 if sal_mensuel > 0 else float(emp.get('salaire_journalier', 0))
            total_paie += len(pts) * sal_jour

    col1.metric("Effectif Total", f"{nb_employes} Salariés")
    col2.metric("Total Jours Pointés", f"{total_jours} Jours")
    col3.metric("Masse Salariale Cumulée", f"{total_paie:,.2f} DA".replace(",", " "))

    st.divider()
    st.subheader("Effectif de l'entreprise")
    if not df_emp.empty:
        df_display = df_emp.copy()
        if 'salaire_mensuel' in df_display.columns:
            df_display['salaire_journalier_calc'] = df_display['salaire_mensuel'].apply(lambda x: float(x or 0) / 26)
        st.dataframe(
            df_display[['nom_complet', 'poste', 'salaire_mensuel', 'salaire_journalier_calc', 'date_embauche']], 
            use_container_width=True,
            column_config={
                "nom_complet": "Nom & Prénom",
                "poste": "Poste",
                "salaire_mensuel": st.column_config.NumberColumn("Salaire Mensuel Base (DA)", format="%d DA"),
                "salaire_journalier_calc": st.column_config.NumberColumn("Tarif Jour (Base 26j)", format="%.2f DA"),
                "date_embauche": "Date d'intégration"
            }
        )
    else:
        st.info("Aucun employé inscrit.")

# --- TAB 2 : GESTION DU PERSONNEL ---
with tab_emp:
    col_add, col_edit = st.columns(2, gap="large")
    
    with col_add:
        st.subheader("➕ Ajouter un Salarié")
        with st.form("form_nouveau_emp", clear_on_submit=True):
            nom = st.text_input("Nom & Prénom *")
            poste = st.text_input("Poste occupé *")
            sal_mensuel = st.number_input("Salaire Mensuel (DA) *", min_value=10000, value=60000, step=5000)
            st.caption(f"💡 Tarif jour automatique (Base 26 jours) : **{sal_mensuel / 26:,.2f} DA / jour**")
            
            if st.form_submit_button("Ajouter à l'effectif"):
                if nom and poste:
                    supabase.table("employes").insert({
                        "entreprise_id": entreprise_id,
                        "nom_complet": nom,
                        "poste": poste,
                        "salaire_mensuel": sal_mensuel,
                        "salaire_journalier": sal_mensuel / 26
                    }).execute()
                    st.success(f"{nom} a été ajouté !")
                    st.rerun()

    with col_edit:
        st.subheader("✏️ Modifier / Supprimer un Salarié")
        if liste_employes:
            emp_a_modifier = st.selectbox(
                "Sélectionner le salarié :", 
                options=liste_employes, 
                format_func=lambda x: f"{x['nom_complet']} ({x['poste']})"
            )
            
            with st.form("form_edit_emp"):
                mod_nom = st.text_input("Nom & Prénom", value=emp_a_modifier['nom_complet'])
                mod_poste = st.text_input("Poste", value=emp_a_modifier['poste'])
                mod_sal_mensuel = st.number_input(
                    "Salaire Mensuel (DA)", 
                    min_value=10000, 
                    value=int(emp_a_modifier.get('salaire_mensuel') or 60000), 
                    step=5000
                )
                
                c_btn1, c_btn2 = st.columns(2)
                btn_sauvegarder = c_btn1.form_submit_button("💾 Enregistrer modifications")
                btn_supprimer = c_btn2.form_submit_button("🗑️ Supprimer l'employé")
                
                if btn_sauvegarder:
                    supabase.table("employes").update({
                        "nom_complet": mod_nom,
                        "poste": mod_poste,
                        "salaire_mensuel": mod_sal_mensuel,
                        "salaire_journalier": mod_sal_mensuel / 26
                    }).eq("id", emp_a_modifier['id']).execute()
                    st.success("Informations mises à jour !")
                    st.rerun()
                    
                if btn_supprimer:
                    supabase.table("employes").delete().eq("id", emp_a_modifier['id']).execute()
                    st.warning("Salarié supprimé.")
                    st.rerun()
        else:
            st.info("Aucun salarié à modifier.")

# --- TAB 3 : POINTAGE (COLLECTIF + INDIVIDUEL) & PAIE ---
with tab_pointage:
    st.subheader("📅 Saisie du Pointage")
    
    if liste_employes:
        mode_pointage = st.radio(
            "Choisir le mode de pointage :", 
            ["⚡ Pointage Collectif (Toute l'équipe)", "👤 Pointage Individuel (Unité)"], 
            horizontal=True
        )
        
        # --- MODE 1 : POINTAGE COLLECTIF PAR ÉQUIPE ---
        if mode_pointage == "⚡ Pointage Collectif (Toute l'équipe)":
            st.info("💡 Tous vos salariés sont inscrits 'Présent' par défaut. Ajustez uniquement le statut des absents/congés puis cliquez sur le bouton de validation.")
            
            c_date, _ = st.columns([1, 2])
            date_p_collectif = c_date.date_input("Date du pointage d'équipe", value=date.today(), key="date_col")
            
            # Formate la liste des salariés pour l'éditeur de tableau
            data_equipe = [{
                "id": emp['id'],
                "Salarié": emp['nom_complet'],
                "Poste": emp['poste'],
                "Statut": "Présent"
            } for emp in liste_employes]
            
            df_equipe = pd.DataFrame(data_equipe)
            
            # Tableau interactif permettant la modification rapide des statuts
            df_edite = st.data_editor(
                df_equipe,
                column_config={
                    "id": None, # Masqué
                    "Salarié": st.column_config.TextColumn("Salarié", disabled=True),
                    "Poste": st.column_config.TextColumn("Poste", disabled=True),
                    "Statut": st.column_config.SelectboxColumn(
                        "Statut du jour",
                        options=["Présent", "Absent", "Congé", "Maladie"],
                        required=True
                    )
                },
                hide_index=True,
                use_container_width=True,
                key="editor_pointage"
            )
            
            if st.button("💾 Valider le pointage de toute l'équipe (1-Clic)", type="primary"):
                pointages_batch = [
                    {
                        "employe_id": int(row['id']),
                        "date_pointage": str(date_p_collectif),
                        "statut": row['Statut']
                    }
                    for _, row in df_edite.iterrows()
                ]
                supabase.table("pointages").insert(pointages_batch).execute()
                st.success(f"✅ Pointage du {date_p_collectif.strftime('%d/%m/%Y')} validé pour les {len(pointages_batch)} salariés !")
                st.rerun()

        # --- MODE 2 : POINTAGE INDIVIDUEL ---
        else:
            c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
            emp_sel = c_p1.selectbox("Salarié :", options=liste_employes, format_func=lambda x: f"{x['nom_complet']} ({x['poste']})", key="pt_sel")
            date_p = c_p2.date_input("Date du pointage", value=date.today(), key="date_ind")
            statut_p = c_p3.selectbox("Statut :", ["Présent", "Absent", "Congé", "Maladie"], key="stat_ind")
            
            if st.button("Valider le pointage individuel"):
                supabase.table("pointages").insert({
                    "employe_id": emp_sel['id'],
                    "date_pointage": str(date_p),
                    "statut": statut_p
                }).execute()
                st.success(f"Pointage enregistré pour {emp_sel['nom_complet']}.")
                st.rerun()
            
        st.divider()
        st.subheader("💰 Calculateur de Paie Dynamique (Automatique)")
        
        recap_paie = []
        for emp in liste_employes:
            res_p = supabase.table("pointages").select("*").eq("employe_id", emp['id']).eq("statut", "Présent").execute()
            nb_jours = len(res_p.data) if res_p.data else 0
            
            sal_mensuel = float(emp.get('salaire_mensuel') or 0)
            sal_jour = sal_mensuel / 26 if sal_mensuel > 0 else float(emp.get('salaire_journalier', 0))
            paie_actuelle = nb_jours * sal_jour
            
            recap_paie.append({
                "Employé": emp['nom_complet'],
                "Poste": emp['poste'],
                "Salaire Mensuel Base": f"{sal_mensuel:,.0f} DA",
                "Tarif / Jour (Base 26j)": f"{sal_jour:,.2f} DA",
                "Jours Présents": nb_jours,
                "Paie Comptabilisée": f"{paie_actuelle:,.2f} DA".replace(",", " ")
            })
            
        st.table(pd.DataFrame(recap_paie))
    else:
        st.info("Ajoutez des employés dans l'onglet 'Personnel'.")

# --- TAB 4 : DOCUMENTS & CANVA ---
with tab_docs:
    st.subheader("📄 Générateur de Documents & Canvas")
    if liste_employes:
        emp_doc = st.selectbox("Choisir l'employé :", options=liste_employes, format_func=lambda x: x['nom_complet'], key="sel_doc_tab4")
        type_doc = st.radio("Document à générer :", ["Attestation de Travail", "ATS (Attestation de Salaire)", "Badge Canva"])
        
        box = st.container(border=True)
        with box:
            sal_mensuel = float(emp_doc.get('salaire_mensuel') or 0)
            st.markdown(f"**ENTREPRISE :** {nom_client}")
            st.markdown(f"**SALARIÉ :** {emp_doc['nom_complet']} — **POSTE :** {emp_doc['poste']}")
            st.markdown(f"**SALAIRE MENSUEL BASE :** {sal_mensuel:,.2f} DA")
            st.markdown(f"**DATE :** {datetime.now().strftime('%d/%m/%Y')}")
            st.markdown("---")
            if type_doc == "Attestation de Travail":
                st.write(f"Nous soussignés, **{nom_client}**, attestons que M./Mme **{emp_doc['nom_complet']}** est employé(e) en qualité de **{emp_doc['poste']}**.")
            elif type_doc == "ATS (Attestation de Salaire)":
                st.write(f"Attestation certifiant que le salarié **{emp_doc['nom_complet']}** perçoit un salaire mensuel de base de **{sal_mensuel:,.2f} DA** (soit un tarif journalier de **{sal_mensuel/26:,.2f} DA**).")
            else:
                st.info(f"🎴 **BADGE RH**\n\nNom: {emp_doc['nom_complet']}\nPoste: {emp_doc['poste']}\nSociété: {nom_client}")
    else:
        st.info("Aucun employé disponible.")