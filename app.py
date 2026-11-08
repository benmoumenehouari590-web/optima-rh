import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- 1. CONFIGURATION & DESIGN SAAS ---
st.set_page_config(
    page_title="Optima RH - Solution SaaS RH & Paie",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Adaptatif (Supporte automatiquement le Light Mode et Dark Mode du système)
st.markdown("""
    <style>
        /* Cartes Métriques */
        .stMetric {
            background-color: var(--secondary-background-color);
            padding: 18px;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        /* Boutons Principaux */
        .stButton>button {
            border-radius: 8px;
            height: 45px;
            font-weight: 600;
        }
        /* Hero Box Marketing */
        .hero-box {
            background-color: var(--secondary-background-color);
            padding: 35px 25px;
            border-radius: 16px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        /* Cartes de fonctionnalités */
        .feature-card {
            background-color: var(--secondary-background-color);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid rgba(128, 128, 128, 0.2);
            margin-bottom: 14px;
        }
        /* Titres dans le HTML adaptatifs */
        .adaptive-title {
            color: var(--text-color);
            font-weight: 700;
        }
        .adaptive-text {
            color: var(--text-color);
            opacity: 0.8;
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

# --- 3. LANDING PAGE MARKETING & CONNEXION SÉCURISÉE ---
if st.session_state["connected_company"] is None:
    
    # Hero Box Marketing adaptative
    st.markdown("""
        <div class="hero-box">
            <h1 style="color: #2563EB; font-size: 2.7rem; margin-bottom: 8px; font-weight: 700;">⚡ Optima RH</h1>
            <h3 class="adaptive-title" style="margin-top: 0; font-size: 1.3rem;">La plateforme SaaS pour simplifier la gestion de votre personnel et votre paie</h3>
            <p class="adaptive-text" style="font-size: 1.05rem; max-width: 800px; margin: 15px auto 0 auto; line-height: 1.6;">
                Un espace client sécurisé, moderne et intuitif. Pointez vos équipes en 1-clic, gérez vos salaires avec précision et éditez vos documents administratifs sans effort.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_marketing, col_auth = st.columns([1.2, 1], gap="large")

    with col_marketing:
        st.subheader("✨ Pourquoi les entreprises choisissent Optima RH ?")
        
        st.markdown("""
        <div class="feature-card">
            <h4 style="color: #2563EB; margin-bottom: 6px; font-size: 1.1rem;">⚡ Pointage Collectif 1-Clic</h4>
            <p class="adaptive-text" style="margin: 0; font-size: 0.95rem;">Gagnez du temps chaque jour : l'ensemble de votre effectif est pré-validé. Vous ne modifiez que les absences et congés.</p>
        </div>
        <div class="feature-card">
            <h4 style="color: #2563EB; margin-bottom: 6px; font-size: 1.1rem;">💰 Calculateur de Paie en Temps Réel</h4>
            <p class="adaptive-text" style="margin: 0; font-size: 0.95rem;">Calcul automatique des salaires mensuels au prorata des jours de présence (Base réglementaire 26 jours).</p>
        </div>
        <div class="feature-card">
            <h4 style="color: #2563EB; margin-bottom: 6px; font-size: 1.1rem;">🔒 Confidentialité & Sécurité Cloud</h4>
            <p class="adaptive-text" style="margin: 0; font-size: 0.95rem;">Chaque société accède à un espace isolé et étanche. Vos données sont sauvegardées en continu et accessibles 24/7.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        tab_login, tab_signup = st.tabs(["🔑 Se Connecter", "📝 Inscrire une Entreprise"])

        with tab_login:
            st.subheader("Accès Espace Client")
            with st.form("form_connexion_client"):
                nom_saisi = st.text_input("Nom de votre société (ex: SARL MAINA)", key="login_nom")
                mdp_saisi = st.text_input("Mot de passe", type="password", key="login_mdp")
                
                btn_connexion = st.form_submit_button("Connexion à l'Espace RH", type="primary", use_container_width=True)
                
                if btn_connexion:
                    if nom_saisi and mdp_saisi:
                        res = supabase.table("entreprises").select("*").ilike("nom", nom_saisi.strip()).execute()
                        if res.data:
                            compte = res.data[0]
                            mdp_attendu = compte.get("mot_de_passe") or "123456"
                            if mdp_saisi == mdp_attendu:
                                st.session_state["connected_company"] = compte
                                st.success("Connexion réussie !")
                                st.rerun()
                            else:
                                st.error("Mot de passe incorrect.")
                        else:
                            st.error("Aucune entreprise enregistrée sous ce nom.")
                    else:
                        st.warning("Veuillez remplir le nom de la société et le mot de passe.")

        with tab_signup:
            st.subheader("Créer un nouveau compte")
            with st.form("form_nouveau_compte", clear_on_submit=True):
                nouveau_nom = st.text_input("Nom officiel de votre société *")
                nouveau_mdp = st.text_input("Créer un mot de passe *", type="password")
                
                if st.form_submit_button("Créer l'Espace Entreprise", use_container_width=True):
                    if nouveau_nom and nouveau_mdp:
                        verif = supabase.table("entreprises").select("id").ilike("nom", nouveau_nom.strip()).execute()
                        if verif.data:
                            st.error("Une entreprise portant ce nom est déjà inscrite.")
                        else:
                            supabase.table("entreprises").insert({
                                "nom": nouveau_nom.strip(),
                                "mot_de_passe": nouveau_mdp
                            }).execute()
                            st.success(f"Compte créé avec succès pour '{nouveau_nom}' ! Vous pouvez vous connecter.")
                    else:
                        st.warning("Veuillez remplir tous les champs obligatoires.")

    st.stop()

# --- 4. ESPACE DE TRAVAIL CLIENT (APRÈS CONNEXION) ---
entreprise_active = st.session_state["connected_company"]
entreprise_id = entreprise_active["id"]
nom_client = entreprise_active["nom"]

# SIDEBAR : MENU ET GESTION DE COMPTE
with st.sidebar:
    st.title("⚡ Optima RH")
    st.write(f"🏢 **{nom_client}**")
    st.caption(f"ID Client : #{entreprise_id}")
    st.divider()

    # OPTION : CHANGER DE MOT DE PASSE
    with st.expander("🔑 Paramètres du compte"):
        with st.form("form_change_mdp", clear_on_submit=True):
            st.write("Modifier le mot de passe")
            ancien_mdp = st.text_input("Mot de passe actuel", type="password")
            nouveau_mdp = st.text_input("Nouveau mot de passe", type="password")
            conf_mdp = st.text_input("Confirmer le mot de passe", type="password")
            
            if st.form_submit_button("Mettre à jour"):
                mdp_actuel_db = entreprise_active.get("mot_de_passe") or "123456"
                if ancien_mdp != mdp_actuel_db:
                    st.error("Le mot de passe actuel est incorrect.")
                elif nouveau_mdp != conf_mdp:
                    st.error("Les nouveaux mots de passe ne correspondent pas.")
                elif len(nouveau_mdp) < 4:
                    st.error("Le mot de passe est trop court.")
                else:
                    supabase.table("entreprises").update({"mot_de_passe": nouveau_mdp}).eq("id", entreprise_id).execute()
                    st.session_state["connected_company"]["mot_de_passe"] = nouveau_mdp
                    st.success("✅ Mot de passe modifié !")
                    
    # OPTION : SUPPRIMER LE COMPTE (ZONE DE DANGER)
    with st.expander("⚠️ Zone de danger"):
        st.warning("Action irréversible. Toutes vos données seront perdues.")
        confirm_del = st.text_input("Tapez 'SUPPRIMER' pour confirmer :")
        if st.button("Supprimer mon entreprise", type="primary", use_container_width=True):
            if confirm_del == "SUPPRIMER":
                supabase.table("entreprises").delete().eq("id", entreprise_id).execute()
                st.session_state["connected_company"] = None
                st.rerun()
            else:
                st.error("Confirmation invalide.")

    st.divider()
    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        st.rerun()

st.title(f"Tableau de Bord — {nom_client}")

res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
liste_employes = res_emp.data if res_emp.data else []
df_emp = pd.DataFrame(liste_employes)

# SUPPRESSION DE L'ONGLET DOCUMENTS (3 onglets restants)
tab_dash, tab_emp, tab_pointage = st.tabs([
    "📊 Vue Générale & KPIs", 
    "👤 Gestion du Personnel", 
    "📅 Pointage & Paie Automatique"
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
        
        # MODE 1 : POINTAGE COLLECTIF
        if mode_pointage == "⚡ Pointage Collectif (Toute l'équipe)":
            st.info("💡 Tous vos salariés sont inscrits 'Présent' par défaut. Ajustez uniquement le statut des absents/congés puis cliquez sur le bouton de validation.")
            
            c_date, _ = st.columns([1, 2])
            date_p_collectif = c_date.date_input("Date du pointage d'équipe", value=date.today(), key="date_col")
            
            data_equipe = [{
                "id": emp['id'],
                "Salarié": emp['nom_complet'],
                "Poste": emp['poste'],
                "Statut": "Présent"
            } for emp in liste_employes]
            
            df_equipe = pd.DataFrame(data_equipe)
            
            df_edite = st.data_editor(
                df_equipe,
                column_config={
                    "id": None,
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

        # MODE 2 : POINTAGE INDIVIDUEL
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