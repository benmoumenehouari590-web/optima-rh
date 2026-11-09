import streamlit as st
import pandas as pd
from supabase import create_client, Client
import json
import os

st.set_page_config(page_title="BMN TECH - Control Room", page_icon="👑", layout="wide")

st.markdown("""
    <style>
        .master-header { text-align: center; margin-bottom: 40px; }
        .master-title { font-size: 3rem; font-weight: 900; color: #1E3A8A; margin-bottom: 0; letter-spacing: -1px; }
        .god-mode { border: 2px solid #ef4444; padding: 20px; border-radius: 10px; background-color: #7f1d1d10; }
        .metric-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #1E3A8A; }
    </style>
""", unsafe_allow_html=True)

URL = "https://firjafhrsqsfluohcrow.supabase.co"
CLE_API = "sb_publishable_4x5vHBt6RnM5LbwVi9xLLg_OsANQ0Li"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, CLE_API)

supabase = init_supabase()

ADMIN_PASSWORD = "bmn_master_2026" 

if "admin_connected" not in st.session_state:
    st.session_state["admin_connected"] = False

if not st.session_state["admin_connected"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.markdown('<div class="master-header"><h1 class="master-title">BENMOUMENE TECHNOLOGIES</h1><p>Control Room Sécurisée</p></div>', unsafe_allow_html=True)
        with st.form("admin_login"):
            mdp_saisi = st.text_input("Clé d'accès", type="password")
            if st.form_submit_button("Déverrouiller le système", type="primary", use_container_width=True):
                if mdp_saisi == ADMIN_PASSWORD:
                    st.session_state["admin_connected"] = True
                    st.rerun()
                else:
                    st.error("Accès refusé.")
    st.stop() 

# --- GESTION DES PROJETS ---
FICHIER_PROJETS = "projets_actifs.json"
def charger_projets():
    if os.path.exists(FICHIER_PROJETS):
        with open(FICHIER_PROJETS, "r") as f:
            return json.load(f)
    return [{"nom": "OPTIMA RH", "statut": "Actif"}]

def sauvegarder_projets(projets):
    with open(FICHIER_PROJETS, "w") as f:
        json.dump(projets, f)

projets = charger_projets()
noms_projets_dispos = [p["nom"] for p in projets]

st.sidebar.title("👑 BMN Control Room")
if st.sidebar.button("🔒 Verrouiller le système", use_container_width=True):
    st.session_state["admin_connected"] = False
    st.rerun()

try:
    res = supabase.table("entreprises").select("*").execute()
    liste_clients = res.data if res.data else []
except Exception as e:
    st.error(f"Erreur de base de données : {e}")
    liste_clients = []

options_clients = {f"{c['nom']} (ID: {c['id']})": c for c in liste_clients} if liste_clients else {}

tab_dash, tab_clients, tab_projets, tab_godmode = st.tabs(["📊 Finances & MRR", "🏢 Gestion Clients", "🚀 Projets Actifs", "👁️ GOD MODE"])

# --- TAB DASHBOARD ---
with tab_dash:
    st.subheader("Analyse Financière Globale")
    if liste_clients:
        df_clients = pd.DataFrame(liste_clients)
        df_clients['prix_abonnement'] = pd.to_numeric(df_clients['prix_abonnement']).fillna(4500)
        mrr_total = df_clients['prix_abonnement'].sum()
        mrr_moyen = df_clients['prix_abonnement'].mean()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Clients Actifs", len(liste_clients))
        c2.metric("Revenu Mensuel (MRR)", f"{mrr_total:,.2f} DA")
        c3.metric("Panier Moyen", f"{mrr_moyen:,.2f} DA")
        c4.metric("Projets Déployés", len(projets))
        
        st.markdown("---")
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            st.markdown("#### Répartition des Revenus par Client")
            df_chart = df_clients[['nom', 'prix_abonnement']].groupby('nom').sum()
            st.bar_chart(df_chart, color="#1E3A8A")
        with col_data:
            st.markdown("#### Détail par entreprise")
            df_display = df_clients[['nom', 'prix_abonnement', 'projets_autorises']].rename(
                columns={"nom": "Client", "prix_abonnement": "MRR (DA)", "projets_autorises": "Projets"}
            )
            st.dataframe(df_display, hide_index=True, use_container_width=True)

# --- TAB GESTION CLIENTS ---
with tab_clients:
    c_ajout, c_modif = st.columns([1, 1.5], gap="large")
    with c_ajout:
        st.markdown("#### ➕ Nouveau Client")
        with st.form("ajout_client_prix", clear_on_submit=True):
            nv_nom = st.text_input("Nom de l'entreprise")
            nv_mdp = st.text_input("Mot de passe", value="1234")
            nv_prix = st.number_input("Abonnement Mensuel (DA)", value=4500, step=500)
            nv_acces = st.multiselect("Autoriser l'accès aux projets :", noms_projets_dispos, default=["OPTIMA RH"] if "OPTIMA RH" in noms_projets_dispos else [])
            if st.form_submit_button("Créer le compte", type="primary"):
                if nv_nom:
                    acces_str = ", ".join(nv_acces)
                    supabase.table("entreprises").insert({
                        "nom": nv_nom, "mot_de_passe": nv_mdp, "prix_abonnement": nv_prix, "projets_autorises": acces_str
                    }).execute()
                    st.success("Client ajouté avec succès !")
                    st.rerun()

    with c_modif:
        st.markdown("#### ⚙️ Contrôle et Nettoyage")
        if options_clients:
            choix_nom = st.selectbox("Sélectionnez un client à modifier/supprimer :", list(options_clients.keys()))
            client_sel = options_clients[choix_nom]
            acces_actuels_str = client_sel.get('projets_autorises') or ''
            acces_actuels_list = [p.strip() for p in acces_actuels_str.split(",")] if acces_actuels_str else []
            acces_valides = [p for p in acces_actuels_list if p in noms_projets_dispos]

            with st.form("modifier_client"):
                mod_nom = st.text_input("Nom", value=client_sel['nom'])
                mod_mdp = st.text_input("Mot de passe", value=client_sel.get('mot_de_passe', ''))
                mod_prix = st.number_input("Abonnement Mensuel (DA)", value=client_sel.get('prix_abonnement') or 4500, step=500)
                mod_acces = st.multiselect("Autoriser l'accès aux projets :", noms_projets_dispos, default=acces_valides)
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.form_submit_button("💾 Mettre à jour"):
                    acces_str = ", ".join(mod_acces)
                    supabase.table("entreprises").update({
                        "nom": mod_nom, "mot_de_passe": mod_mdp, "prix_abonnement": mod_prix, "projets_autorises": acces_str
                    }).eq("id", client_sel['id']).execute()
                    st.success("Modifications enregistrées.")
                    st.rerun()
                if c_btn2.form_submit_button("🛑 Supprimer ce client"):
                    supabase.table("entreprises").delete().eq("id", client_sel['id']).execute()
                    st.rerun()

# --- TAB PROJETS ---
with tab_projets:
    st.subheader("Vos Logiciels (Software House)")
    with st.form("ajout_projet"):
        cols = st.columns([2, 1])
        nv_proj_nom = cols[0].text_input("Nom du nouveau projet")
        if cols[1].form_submit_button("➕ Ajouter au catalogue"):
            if nv_proj_nom and nv_proj_nom not in noms_projets_dispos:
                projets.append({"nom": nv_proj_nom, "statut": "Actif"})
                sauvegarder_projets(projets)
                st.rerun()
    for i, proj in enumerate(projets):
        col_txt, col_btn = st.columns([4, 1])
        col_txt.success(f"🟢 **{proj['nom']}**")
        if col_btn.button("🗑️ Retirer", key=f"del_proj_{i}"):
            projets.pop(i)
            sauvegarder_projets(projets)
            st.rerun()

# --- TAB GOD MODE ---
with tab_godmode:
    st.markdown('<div class="god-mode">', unsafe_allow_html=True)
    st.subheader("👁️ Accès Directeur (God Mode) - Manipulation des Données")
    if options_clients:
        god_nom_complet = st.selectbox("Inspection des données du client :", list(options_clients.keys()), key="god")
        g_c = options_clients[god_nom_complet]
        
        st.info(f"**Client :** {g_c['nom']} | **Projets autorisés :** {g_c.get('projets_autorises', 'Aucun')}")
        
        try:
            res_emp = supabase.table("employes").select("*").eq("entreprise_id", g_c['id']).execute()
            employes = res_emp.data
            
            if employes:
                df_employes = pd.DataFrame(employes)
                if 'entreprise_id' in df_employes.columns:
                    df_employes = df_employes.drop(columns=['entreprise_id'])
                st.dataframe(df_employes, use_container_width=True)
                
                st.markdown("#### ✏️ Modifier ou Supprimer un employé pour ce client")
                options_emp = {f"{e.get('nom', '')} {e.get('prenom', '')} (ID: {e['id']})": e for e in employes}
                emp_sel_name = st.selectbox("Sélectionnez l'employé à modifier :", list(options_emp.keys()))
                emp_sel = options_emp[emp_sel_name]
                
                with st.form("edit_emp_godmode"):
                    c1, c2 = st.columns(2)
                    mod_nom_emp = c1.text_input("Nom", value=emp_sel.get('nom', ''))
                    mod_prenom_emp = c2.text_input("Prénom", value=emp_sel.get('prenom', ''))
                    mod_poste = c1.text_input("Poste", value=emp_sel.get('poste', ''))
                    mod_salaire = c2.number_input("Salaire", value=float(emp_sel.get('salaire_base') or 0), step=1000.0)
                    
                    col_btn_edit, col_btn_del = st.columns(2)
                    if col_btn_edit.form_submit_button("💾 Enregistrer la modification"):
                        supabase.table("employes").update({
                            "nom": mod_nom_emp, "prenom": mod_prenom_emp, "poste": mod_poste, "salaire_base": mod_salaire
                        }).eq("id", emp_sel['id']).execute()
                        st.success("Employé mis à jour !")
                        st.rerun()
                        
                    if col_btn_del.form_submit_button("🛑 Supprimer l'employé"):
                        supabase.table("employes").delete().eq("id", emp_sel['id']).execute()
                        st.rerun()
            else:
                st.warning("Aucun employé enregistré pour ce client.")

            st.markdown("#### ➕ Forcer l'ajout d'un employé dans la base de ce client")
            with st.form("add_emp_godmode", clear_on_submit=True):
                c1, c2 = st.columns(2)
                add_nom = c1.text_input("Nom")
                add_prenom = c2.text_input("Prénom")
                add_poste = c1.text_input("Poste")
                add_salaire = c2.number_input("Salaire de base", min_value=0.0, step=1000.0)

                if st.form_submit_button("Ajouter à la base de données"):
                    if add_nom and add_prenom:
                        supabase.table("employes").insert({
                            "entreprise_id": g_c['id'],
                            "nom": add_nom,
                            "prenom": add_prenom,
                            "poste": add_poste,
                            "salaire_base": add_salaire
                        }).execute()
                        st.success("Employé ajouté avec succès !")
                        st.rerun()

        except Exception as e:
            st.error(f"Information : Erreur lors du chargement des employés. Détail : {e}")
            
    st.markdown('</div>', unsafe_allow_html=True)