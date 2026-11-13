import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF
import plotly.express as px

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Optima RH - 2026", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .alert-card { background: rgba(220, 38, 38, 0.15); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        div.stButton > button { background: linear-gradient(90deg, #2563eb, #4f46e5); color: white; border: none; border-radius: 8px; }
        div.stButton > button:hover { transform: translateY(-2px); }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXION SUPABASE ---
URL = "https://firjafhrsqsfluohcrow.supabase.co"
CLE_API = "sb_publishable_4x5vHBt6RnM5LbwVi9xLLg_OsANQ0Li"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(URL, CLE_API)

supabase = init_supabase()
if "connected_company" not in st.session_state: st.session_state["connected_company"] = None

# --- 3. LOGIQUE MÉTIER (ALGÉRIE) ---
def calculer_irg(base_imposable):
    """Calcul de l'IRG Algérien (Barème avec abattement 40%)"""
    if base_imposable <= 30000: return 0
    irg_brut = (base_imposable - 30000) * 0.30 if base_imposable <= 120000 else (120000 - 30000) * 0.30 + (base_imposable - 120000) * 0.35
    abattement = max(1000, min(1500, irg_brut * 0.40))
    return max(0, irg_brut - abattement)

def generer_pdf(titre, contenu, nom_societe):
    """Générateur universel de documents RH (PDF)"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=nom_societe.upper(), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=titre, ln=True, align='C')
    pdf.ln(15)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8, txt=contenu)
    pdf.ln(20)
    pdf.cell(0, 10, txt="Le Directeur / DRH", ln=True, align='R')
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

# --- 4. PORTAIL DE CONNEXION SAAS ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="glass-card" style="text-align:center;"><h2>⚡ Optima RH</h2><p>Espace de Travail Sécurisé</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            nom = st.text_input("Société")
            mdp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Accéder à mon espace", use_container_width=True):
                res = supabase.table("entreprises").select("*").ilike("nom", nom.strip()).execute()
                if res.data and mdp == res.data[0].get("mot_de_passe", ""):
                    compte = res.data[0]
                    # VERROUILLAGE SAAS (Connexion avec Master App)
                    if "OPTIMA RH" not in (compte.get("projets_autorises") or ""):
                        st.error("🔒 Accès suspendu ou abonnement expiré. Contactez BENMOUMENE TECH.")
                    else:
                        st.session_state["connected_company"] = compte
                        st.rerun()
                else:
                    st.error("Identifiants incorrects.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. ESPACE CLIENT ---
entreprise = st.session_state["connected_company"]
entreprise_id = entreprise["id"]
societe = entreprise["nom"]

with st.sidebar:
    st.title("⚡ Optima RH")
    st.write(f"🏢 **{societe}**")
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state["connected_company"] = None
        st.rerun()

res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
employes = res_emp.data if res_emp.data else []
df_emp = pd.DataFrame(employes)

tab_dash, tab_emp, tab_docs, tab_paie = st.tabs(["📊 Direction & Alertes", "👥 Base Salariés", "📄 Docs RH (PDF)", "💰 Paie Algérienne"])

# --- TAB 1 : DASHBOARD DIRECTION & ALERTES ---
with tab_dash:
    st.markdown("### 📈 Indicateurs Clés & Alertes")
    if not df_emp.empty:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="glass-card"><h4>Effectif Actif</h4><h2>{len([e for e in employes if e.get("statut") == "Actif"])}</h2></div>', unsafe_allow_html=True)
        masse = df_emp['salaire_mensuel'].sum() if 'salaire_mensuel' in df_emp.columns else 0
        c2.markdown(f'<div class="glass-card"><h4>Masse Salariale Base</h4><h2>{masse:,.0f} DA</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="glass-card"><h4>Postes Total</h4><h2>{df_emp["poste"].nunique()}</h2></div>', unsafe_allow_html=True)
        
        st.markdown("<br>#### ⚠️ Alertes RH Automatiques", unsafe_allow_html=True)
        alertes = 0
        seuil_alerte = date.today() + timedelta(days=15)
        for emp in employes:
            d_dep = emp.get("date_depart")
            if d_dep and emp.get("statut") == "Actif":
                d_obj = datetime.strptime(d_dep, "%Y-%m-%d").date()
                if date.today() <= d_obj <= seuil_alerte:
                    alertes += 1
                    st.markdown(f'<div class="alert-card">⏳ <b>Fin de contrat imminente :</b> {emp["nom_complet"]} ({emp["poste"]}) - Le {d_dep}</div>', unsafe_allow_html=True)
        if alertes == 0:
            st.success("✅ Aucune alerte contrat à signaler.")
    else:
        st.info("Ajoutez des employés pour visualiser les indicateurs.")

# --- TAB 2 : GESTION DES EMPLOYÉS ---
with tab_emp:
    c_add, c_list = st.columns([1, 2], gap="large")
    with c_add:
        st.markdown('<div class="glass-card"><h4>➕ Nouveau Salarié</h4>', unsafe_allow_html=True)
        with st.form("form_add_emp"):
            n = st.text_input("Nom & Prénom")
            p = st.text_input("Poste")
            s = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
            d_int = st.date_input("Date Intégration")
            d_fin = st.date_input("Date Fin Contrat (Optionnel)", value=None)
            if st.form_submit_button("Enregistrer"):
                supabase.table("employes").insert({"entreprise_id": entreprise_id, "nom_complet": n, "poste": p, "salaire_mensuel": s, "date_integration": str(d_int), "date_depart": str(d_fin) if d_fin else None, "statut": "Actif"}).execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_list:
        st.markdown("#### 📋 Répertoire")
        if not df_emp.empty:
            st.dataframe(df_emp[['nom_complet', 'poste', 'salaire_mensuel', 'date_integration', 'statut']], use_container_width=True, hide_index=True)

# --- TAB 3 : DOCUMENTS RH (EN 1 CLIC) ---
with tab_docs:
    st.markdown("### 📄 Générateur de Documents Officiels")
    if employes:
        c_doc1, c_doc2 = st.columns([1, 2])
        emp_choisi = c_doc1.selectbox("Sélectionner l'employé :", employes, format_func=lambda x: x["nom_complet"])
        type_doc = c_doc1.selectbox("Type de document :", ["Attestation de Travail", "Certificat de Travail"])
        
        if c_doc1.button("Générer le PDF", type="primary"):
            if type_doc == "Attestation de Travail":
                texte = f"Nous soussignés, l'entreprise {societe}, attestons que :\n\nM. / Mme : {emp_choisi['nom_complet']}\nOccupe le poste de : {emp_choisi['poste']}\n\nFait partie de nos effectifs depuis le {emp_choisi.get('date_integration', 'N/A')}.\n\nCette attestation est délivrée à l'intéressé(e) pour servir et valoir ce que de droit."
            else:
                texte = f"Nous certifions que M. / Mme : {emp_choisi['nom_complet']}\nA été employé(e) au sein de notre structure en qualité de : {emp_choisi['poste']}\n\nLibre de tout engagement, ce certificat lui est délivré pour faire valoir ses droits."
            
            pdf_bytes = generer_pdf(type_doc.upper(), texte, societe)
            c_doc2.success("✅ Document généré avec succès !")
            c_doc2.download_button(label="📥 Télécharger le PDF", data=pdf_bytes, file_name=f"{type_doc}_{emp_choisi['nom_complet']}.pdf", mime="application/pdf")
    else:
        st.info("Aucun employé enregistré.")

# --- TAB 4 : POINTAGE & PAIE ALGÉRIENNE ---
with tab_paie:
    if employes:
        s_point, s_paie = st.tabs(["📝 Pointage Rapide", "💰 Calcul Bulletins & PDF"])
        
        with s_point:
            d_p = st.date_input("Date de Pointage", date.today())
            df_pt = pd.DataFrame([{"id": e['id'], "Employé": e['nom_complet'], "Présence": "Présent"} for e in employes])
            df_edit = st.data_editor(df_pt, column_config={"Présence": st.column_config.SelectboxColumn(options=["Présent", "Absent"])}, hide_index=True)
            if st.button("Sauvegarder Pointage"):
                batch = [{"employe_id": int(r['id']), "date_pointage": str(d_p), "statut": r['Présence']} for _, r in df_edit.iterrows()]
                emp_ids = [int(r['id']) for _, r in df_edit.iterrows()]
                supabase.table("pointages").delete().in_("employe_id", emp_ids).eq("date_pointage", str(d_p)).execute()
                supabase.table("pointages").insert(batch).execute()
                st.success("Pointage validé !")

        with s_paie:
            st.markdown("### 🇩🇿 Simulation Fiche de Paie (CNAS 9% & IRG)")
            e_paie = st.selectbox("Calculer la paie de :", employes, format_func=lambda x: x["nom_complet"], key="paie_emp")
            
            base = float(e_paie.get('salaire_mensuel') or 0.0)
            st.info("Note : Par défaut, le calcul prend 26 jours ouvrables. Vous pouvez ajuster les primes.")
            c_p1, c_p2 = st.columns(2)
            primes = c_p1.number_input("Primes/Indemnités (DA)", value=0.0)
            absences = c_p2.number_input("Jours d'absence non justifiés", value=0, min_value=0, max_value=26)
            
            # --- MOTEUR DE PAIE ALGÉRIENNE ---
            salaire_base_retenu = base * ((26 - absences) / 26)
            salaire_poste = salaire_base_retenu + primes
            retenue_cnas = salaire_poste * 0.09
            base_irg = salaire_poste - retenue_cnas
            retenue_irg = calculer_irg(base_irg)
            net_a_payer = base_irg - retenue_irg
            
            c_r1, c_r2, c_r3 = st.columns(3)
            c_r1.metric("Salaire Soumis (Poste)", f"{salaire_poste:,.2f} DA")
            c_r2.metric("Retenues (CNAS 9% + IRG)", f"{(retenue_cnas + retenue_irg):,.2f} DA")
            c_r3.metric("Net à Payer", f"{net_a_payer:,.2f} DA")
            
            if st.button("📄 Éditer le Bulletin de Paie (PDF)"):
                contenu_paie = f"""BULLETIN DE PAIE
                
Employé : {e_paie['nom_complet']}
Poste : {e_paie['poste']}
------------------------------------------------
Salaire de Base (26j) : {base:,.2f} DA
Absences déduites : {absences} jours
Primes imposables : {primes:,.2f} DA
------------------------------------------------
SALAIRE DE POSTE : {salaire_poste:,.2f} DA

Retenue Sécurité Sociale (CNAS 9%) : -{retenue_cnas:,.2f} DA
Base Imposable IRG : {base_irg:,.2f} DA
Retenue IRG (Barème) : -{retenue_irg:,.2f} DA
------------------------------------------------
NET À PAYER : {net_a_payer:,.2f} DA"""
                
                pdf_paie = generer_pdf(f"BULLETIN DE PAIE", contenu_paie, societe)
                st.download_button("📥 Télécharger le Bulletin PDF", data=pdf_paie, file_name=f"Bulletin_{e_paie['nom_complet']}.pdf", mime="application/pdf", type="primary")