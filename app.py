import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF
import time

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

# --- 2. CONNEXION SUPABASE & CACHE MEMOIRE ---
URL = "https://firjafhrsqsfluohcrow.supabase.co"
CLE_API = "sb_publishable_4x5vHBt6RnM5LbwVi9xLLg_OsANQ0Li"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, CLE_API)

supabase = init_supabase()

@st.cache_data(ttl=3600)
def fetch_entreprises():
    try:
        res = supabase.table("entreprises").select("*").execute()
        return res.data if res.data else [{"nom": "SARL MAINA", "id": 0}]
    except:
        return [{"nom": "SARL MAINA", "id": 0}]

@st.cache_data(ttl=3600)
def fetch_employes(entreprise_id):
    try:
        res = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
        return res.data if res.data else []
    except:
        return []

def parse_date(date_str, default_year):
    try:
        return datetime.strptime(str(date_str).split('T')[0], '%Y-%m-%d').date()
    except:
        return date(default_year, 1, 1)

# --- 3. FONCTIONS DE GÉNÉRATION DE DOCUMENTS ---
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
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, " 1. IDENTIFICATION DE L'EMPLOYEUR", border=1, ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, " Raison Sociale :", border='L'); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, f"{societe}", border='R', ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, " N° Employeur CNAS :", border='L'); pdf.cell(0, 8, "...............................................................", border='R', ln=True)
    pdf.cell(50, 8, " Adresse :", border='LB'); pdf.cell(0, 8, "...............................................................", border='RB', ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, " 2. RENSEIGNEMENTS CONCERNANT LE SALARIE", border=1, ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, " Nom et Prénom :", border='L'); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, f"{emp.get('nom_complet', '')}", border='R', ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, " N° Immatriculation SS :", border='L'); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, f"{emp.get('num_ss', '')}", border='R', ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(50, 8, " Date de naissance :", border='L'); pdf.cell(0, 8, f"{emp.get('date_naissance', '')}", border='R', ln=True)
    pdf.cell(50, 8, " Profession :", border='L'); pdf.cell(0, 8, f"{emp.get('poste', '')}", border='R', ln=True)
    pdf.cell(50, 8, " Date de recrutement :", border='LB'); pdf.cell(0, 8, f"{emp.get('date_integration', '')}", border='RB', ln=True)
    pdf.ln(15)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 6, ""); pdf.cell(0, 6, f"Fait à ......................., le {date.today().strftime('%d/%m/%Y')}", ln=True, align='C')
    pdf.ln(5)
    pdf.cell(100, 6, ""); pdf.set_font("Arial", 'B', 11); pdf.cell(0, 6, "Le Directeur / L'Employeur", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(100, 6, ""); pdf.cell(0, 6, "(Cachet et Signature)", ln=True, align='C')
    return pdf

def generer_avis_depart(emp, projet, date_dep, motif, societe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, f"ENTREPRISE : {societe}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "AVIS DE FIN DE RELATION DE TRAVAIL", border=1, ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Arial", '', 12); pdf.cell(0, 10, f"Nous vous informons officiellement du départ du salarié désigné ci-dessous :", ln=True); pdf.ln(5)
    pdf.set_font("Arial", 'B', 12); pdf.cell(60, 10, " Nom de l'employé :", border=1); pdf.set_font("Arial", '', 12); pdf.cell(130, 10, f" {emp.get('nom_complet', '')}", border=1, ln=True)
    pdf.set_font("Arial", 'B', 12); pdf.cell(60, 10, " En qualité de :", border=1); pdf.set_font("Arial", '', 12); pdf.cell(130, 10, f" {emp.get('poste', '')}", border=1, ln=True)
    pdf.set_font("Arial", 'B', 12); pdf.cell(60, 10, " Affectation :", border=1); pdf.set_font("Arial", '', 12); pdf.cell(130, 10, f" {projet}", border=1, ln=True)
    pdf.set_font("Arial", 'B', 12); pdf.cell(60, 10, " Date de départ :", border=1); pdf.set_font("Arial", '', 12); pdf.cell(130, 10, f" {date_dep.strftime('%d/%m/%Y')}", border=1, ln=True)
    pdf.set_font("Arial", 'B', 12); pdf.cell(60, 10, " Motif du départ :", border=1); pdf.set_font("Arial", '', 12); pdf.cell(130, 10, f" {motif}", border=1, ln=True)
    pdf.ln(20)
    pdf.cell(120, 6, ""); pdf.cell(0, 6, "Signature de la Direction", ln=True, align='C')
    return pdf

def exporter_pdf(pdf_obj):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_obj.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- 4. PORTAIL DE CONNEXION & INSCRIPTION ---
if "connected_company" not in st.session_state:
    st.session_state["connected_company"] = None

if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center; color: #0284c7;'>🏢 Portail Optima RH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Solution de gestion RH & Paie intelligente.</p>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Connexion Client", "✨ Inscrire une Entreprise"])
        
        # ONGLET CONNEXION
        with tab_login:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            liste_soc = fetch_entreprises()
            noms_soc = [s["nom"] for s in liste_soc]
            
            with st.form("formulaire_connexion"):
                societe_choisie = st.selectbox("Sélectionnez votre entreprise", noms_soc)
                mot_de_passe = st.text_input("Mot de passe Administrateur", type="password", help="Le mot de passe par défaut est : admin")
                submit_btn = st.form_submit_button("Se Connecter", type="primary", use_container_width=True)
                
                if submit_btn:
                    if mot_de_passe.strip().lower() == "admin":
                        compte = next((s for s in liste_soc if s["nom"] == societe_choisie), None)
                        st.session_state["connected_company"] = compte
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # ONGLET INSCRIPTION
        with tab_register:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown("Rejoignez la plateforme et gérez vos employés facilement.")
            with st.form("formulaire_inscription"):
                nouveau_nom = st.text_input("Nom officiel de l'entreprise (Raison Sociale) *")
                nouveau_secteur = st.selectbox("Secteur d'activité", ["BTP", "Services", "Industrie", "Commerce", "Technologie", "Autre"])
                st.info("💡 Note : Le mot de passe administrateur par défaut sera 'admin'.")
                
                submit_reg = st.form_submit_button("Créer mon espace", type="primary", use_container_width=True)
                
                if submit_reg:
                    if nouveau_nom.strip() != "":
                        try:
                            # Insertion dans Supabase
                            supabase.table("entreprises").insert({"nom": nouveau_nom.strip()}).execute()
                            fetch_entreprises.clear() # Rafraichit la liste des entreprises
                            st.success("✅ Entreprise créée avec succès ! Allez dans l'onglet 'Connexion Client' pour vous connecter.")
                            time.sleep(2) # Petite pause pour lire le message
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la création : Avez-vous désactivé la sécurité (RLS) sur la table 'entreprises' ? ({e})")
                    else:
                        st.error("⚠️ Le nom de l'entreprise est obligatoire.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. ESPACE ERP CONNECTÉ ---
entreprise = st.session_state["connected_company"]
societe_nom = entreprise["nom"]
entreprise_id = entreprise.get("id", 0)

with st.sidebar:
    st.markdown(f"### 🏢 **{societe_nom}**")
    st.success("🟢 Mode Administrateur")
    st.divider()
    st.metric("Total Salariés", len(fetch_employes(entreprise_id)))
    st.divider()
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["connected_company"] = None
        fetch_employes.clear()
        st.rerun()

employes = fetch_employes(entreprise_id)

st.title(f"Tableau de Bord - {societe_nom}")
tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["👥 Base Salariés", "📅 Pointage Excel", "📄 Documents Légaux", "💰 Simulateur Paie"])

# --- TAB 1: GESTION DES SALARIÉS ---
with tab_emp:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    sub_add, sub_edit, sub_list = st.tabs(["➕ Nouveau Salarié", "✏️ Gérer les Profils", "📋 Registre du Personnel"])
    
    with sub_add:
        with st.form("form_add_salarie", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                nom = st.text_input("Nom Complet *")
                sexe = st.selectbox("Sexe", ["M", "F"])
                date_naiss = st.date_input("Date Naissance", value=date(1990, 1, 1), min_value=date(1920, 1, 1), max_value=date.today())
            with c2:
                type_piece = st.selectbox("Type Pièce *", ["Carte Nationale (CIN)", "Permis de Conduire", "Passeport"])
                num_piece = st.text_input("Numéro Pièce *")
                num_ss = st.text_input("N° Sécurité Sociale (CNAS)")
            with c3:
                poste = st.text_input("Poste / Fonction *")
                salaire = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
                date_int = st.date_input("Date Intégration", value=date.today(), min_value=date(1970, 1, 1), max_value=date(2050, 12, 31))
                
            if st.form_submit_button("💾 Ajouter à la base de données", type="primary"):
                if nom and poste and num_piece:
                    try:
                        supabase.table("employes").insert({
                            "entreprise_id": entreprise_id, "nom_complet": nom, "sexe": sexe, 
                            "date_naissance": str(date_naiss), "type_piece": type_piece, "num_piece": num_piece, 
                            "poste": poste, "salaire_mensuel": float(salaire), "date_integration": str(date_int), 
                            "num_ss": num_ss, "statut": "Actif"
                        }).execute()
                        fetch_employes.clear()
                        st.success("Salarié ajouté !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur d'insertion : {e}")
                else:
                    st.error("⚠️ Veuillez remplir les champs obligatoires (*).")

    with sub_edit:
        if employes:
            emp_a_modifier = st.selectbox("Rechercher un employé :", employes, format_func=lambda x: x.get("nom_complet", "Inconnu"))
            
            with st.form("form_edit_salarie"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    m_nom = st.text_input("Nom Complet *", value=emp_a_modifier.get("nom_complet", ""))
                    m_sexe = st.selectbox("Sexe", ["M", "F"], index=0 if emp_a_modifier.get("sexe") == "M" else 1)
                    m_date_naiss = st.date_input("Date Naissance", value=parse_date(emp_a_modifier.get("date_naissance"), 1990), min_value=date(1920, 1, 1), max_value=date.today())
                with c2:
                    options_piece = ["Carte Nationale (CIN)", "Permis de Conduire", "Passeport"]
                    val_piece = emp_a_modifier.get("type_piece", "Carte Nationale (CIN)")
                    idx_piece = options_piece.index(val_piece) if val_piece in options_piece else 0
                    m_type_piece = st.selectbox("Type Pièce *", options_piece, index=idx_piece)
                    m_num_piece = st.text_input("Numéro Pièce *", value=emp_a_modifier.get("num_piece", ""))
                    m_num_ss = st.text_input("N° Sécurité Sociale (CNAS)", value=emp_a_modifier.get("num_ss", ""))
                with c3:
                    m_poste = st.text_input("Poste / Fonction *", value=emp_a_modifier.get("poste", ""))
                    m_salaire = st.number_input("Salaire Base (DA)", value=float(emp_a_modifier.get("salaire_mensuel", 50000.0)), step=5000.0)
                    m_date_int = st.date_input("Date Intégration", value=parse_date(emp_a_modifier.get("date_integration"), 2023), min_value=date(1970, 1, 1), max_value=date(2050, 12, 31))
                
                col_btn1, col_btn2 = st.columns(2)
                btn_modifier = col_btn1.form_submit_button("✏️ Mettre à jour le dossier", type="primary", use_container_width=True)
                btn_supprimer = col_btn2.form_submit_button("❌ Supprimer définitivement", use_container_width=True)
                
                if btn_modifier:
                    if m_nom and m_poste and m_num_piece:
                        try:
                            supabase.table("employes").update({
                                "nom_complet": m_nom, "sexe": m_sexe, "date_naissance": str(m_date_naiss), 
                                "type_piece": m_type_piece, "num_piece": m_num_piece, "poste": m_poste, 
                                "salaire_mensuel": float(m_salaire), "date_integration": str(m_date_int), 
                                "num_ss": m_num_ss
                            }).eq("id", emp_a_modifier["id"]).execute()
                            fetch_employes.clear()
                            st.success("Dossier mis à jour avec succès !")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur de mise à jour : {e}")
                    else:
                        st.error("⚠️ Champs obligatoires manquants.")
                        
                if btn_supprimer:
                    try:
                        supabase.table("employes").delete().eq("id", emp_a_modifier["id"]).execute()
                        fetch_employes.clear()
                        st.success(f"Salarié {emp_a_modifier.get('nom_complet')} supprimé.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur de suppression : {e}")
        else:
            st.info("Aucun employé enregistré.")

    with sub_list:
        if employes:
            df_emp = pd.DataFrame(employes)
            cols = ['nom_complet', 'poste', 'type_piece', 'num_piece', 'salaire_mensuel', 'statut']
            cols_ex = [col for col in cols if col in df_emp.columns]
            if cols_ex:
                st.dataframe(df_emp[cols_ex], use_container_width=True)
        else:
            st.info("ℹ️ Le registre est vide.")
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: POINTAGE EXCEL ---
with tab_point:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        df_pt = pd.DataFrame([{"Matricule": str(e.get('id', ''))[:8], "Nom et Prénom": e.get('nom_complet', ''), "Fonction": e.get('poste', ''), "Présence": "Présent", "Observations": ""} for e in employes])
        df_edit = st.data_editor(df_pt, column_config={"Présence": st.column_config.SelectboxColumn(options=["Présent", "Absent", "Demi-Journée", "Congé", "Maladie"])}, hide_index=True, use_container_width=True)
        
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_edit.to_excel(writer, index=False, sheet_name='Pointage', startrow=4)
            workbook = writer.book
            worksheet = writer.sheets['Pointage']
            
            title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 1})
            info_format = workbook.add_format({'bold': True, 'font_size': 11})
            header_format = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1, 'align': 'center'})
            
            worksheet.merge_range('A1:E2', f"FEUILLE DE POINTAGE OFFICIELLE - {societe_nom}", title_format)
            worksheet.write('A4', f"Mois d'édition : {date.today().strftime('%B %Y')}", info_format)
            
            worksheet.set_column('A:A', 15); worksheet.set_column('B:B', 35); worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 20); worksheet.set_column('E:E', 30)
            
            for col_num, value in enumerate(df_edit.columns.values):
                worksheet.write(4, col_num, value, header_format)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("📥 Exporter vers Excel", data=out.getvalue(), file_name=f"Pointage_{societe_nom}.xlsx", mime="application/vnd.ms-excel", type="primary")
    else:
        st.info("⚠️ Aucun employé pour générer le pointage.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 3: DOCUMENTS RH ---
with tab_docs:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        c1, c2 = st.columns([1, 2])
        e_doc = c1.selectbox("Sélectionner l'Employé", employes, format_func=lambda x: x.get("nom_complet", "Inconnu"))
        t_doc = c1.radio("Type de document", ["Attestation de Travail (ATS)", "Avis de Fin de Relation"])
        
        with c2:
            st.markdown("<br>", unsafe_allow_html=True)
            if t_doc == "Avis de Fin de Relation":
                projet = st.text_input("Nom du Projet / Site", "Siège Social")
                motif = st.selectbox("Motif du départ", ["Démission", "Fin de CDD", "Licenciement", "Retraite"])
                date_dep = st.date_input("Date de départ", value=date.today())
                if st.button("🖨️ Générer PDF (Avis de départ)", type="primary"):
                    pdf = generer_avis_depart(e_doc, projet, date_dep, motif, societe_nom)
                    st.download_button("📥 Télécharger", exporter_pdf(pdf), file_name=f"Avis_{e_doc.get('nom_complet', '')}.pdf", mime="application/pdf")
            else:
                if st.button("🖨️ Générer PDF (ATS CNAS)", type="primary"):
                    pdf = generer_ats_cnas(e_doc, societe_nom)
                    st.download_button("📥 Télécharger", exporter_pdf(pdf), file_name=f"ATS_{e_doc.get('nom_complet', '')}.pdf", mime="application/pdf")
    else:
        st.info("⚠️ Aucun employé pour générer des documents.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: SIMULATEUR PAIE ---
with tab_paie:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    if employes:
        e_paie = st.selectbox("Calcul pour le Salarié :", employes, format_func=lambda x: x.get("nom_complet", "Inconnu"), key="paie_simul")
        base = float(e_paie.get('salaire_mensuel') or 0.0)
        
        c_p1, c_p2 = st.columns(2)
        jours = c_p1.number_input("Jours Travaillés", value=30.0, max_value=31.0, min_value=0.0, step=0.5)
        primes = c_p2.number_input("Primes (DA)", value=0.0, step=1000.0)
        
        sal_poste = (base * (jours / 30)) + primes
        cnas = sal_poste * 0.09
        net = sal_poste - cnas
        
        st.divider()
        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.metric("Salaire de Poste", f"{sal_poste:,.2f} DA")
        c_r2.metric("Retenue CNAS (9%)", f"-{cnas:,.2f} DA")
        c_r3.markdown(f"**NET À PAYER :** <br><span class='metric-value'>{net:,.2f} DA</span>", unsafe_allow_html=True)
    else:
        st.info("⚠️ Aucun employé pour simuler la paie.")
    st.markdown('</div>', unsafe_allow_html=True)
