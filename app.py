import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from supabase import create_client, Client
import io
import tempfile
from fpdf import FPDF
import plotly.express as px
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Optima RH - SaaS Pro", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); margin-bottom: 20px;}
        .alert-card { background: rgba(220, 38, 38, 0.15); border-left: 4px solid #ef4444; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        div.stButton > button { background: linear-gradient(90deg, #2563eb, #4f46e5); color: white; border: none; border-radius: 8px; font-weight: 600; transition: all 0.3s; }
        div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(37,99,235,0.4); }
        .mail-box { border: 1px dashed #38bdf8; padding: 15px; border-radius: 10px; background: rgba(56, 189, 248, 0.05); mt-3 }
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
if "smtp_config" not in st.session_state: st.session_state["smtp_config"] = {"email": "", "password": ""}

# --- 3. FONCTIONS MÉTIERS (PDF, EXCEL, EMAIL, PAIE) ---
def calculer_irg(base_imposable):
    if base_imposable <= 30000: return 0
    irg_brut = (base_imposable - 30000) * 0.30 if base_imposable <= 120000 else (120000 - 30000) * 0.30 + (base_imposable - 120000) * 0.35
    abattement = max(1000, min(1500, irg_brut * 0.40))
    return max(0, irg_brut - abattement)

def generer_pdf(titre, contenu, nom_societe):
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
    pdf.cell(0, 10, txt="Cachet et Signature", ln=True, align='R')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()

def generer_excel_personnel(df, societe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Personnel', startrow=3)
        workbook, worksheet = writer.book, writer.sheets['Personnel']
        worksheet.merge_range('A1:G1', f'SITUATION DU PERSONNEL - {societe.upper()}', workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'}))
        header_format = workbook.add_format({'bold': True, 'bg_color': '#1E293B', 'font_color': 'white'})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(3, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20)
    return output.getvalue()

def envoyer_email(destinataire, sujet, corps, nom_fichier, bytes_fichier, mime_type):
    expediteur = st.session_state["smtp_config"]["email"]
    mdp = st.session_state["smtp_config"]["password"]
    
    if not expediteur or not mdp:
        return False, "Veuillez configurer votre email d'envoi dans la barre latérale."
    
    msg = MIMEMultipart()
    msg['From'] = expediteur
    msg['To'] = destinataire
    msg['Subject'] = sujet
    msg.attach(MIMEText(corps, 'plain'))
    
    piece_jointe = MIMEApplication(bytes_fichier, _subtype=mime_type)
    piece_jointe.add_header('Content-Disposition', 'attachment', filename=nom_fichier)
    msg.attach(piece_jointe)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(expediteur, mdp)
        server.send_message(msg)
        server.quit()
        return True, "Email envoyé avec succès !"
    except Exception as e:
        return False, f"Erreur d'envoi : Vérifiez vos identifiants ou le mot de passe d'application. Détail: {e}"

# --- 4. PORTAIL DE CONNEXION SAAS ---
if st.session_state["connected_company"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="glass-card" style="text-align:center;"><h2>⚡ Optima RH</h2><p>Portail Entreprise Sécurisé</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            nom = st.text_input("Société")
            mdp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Accéder à mon espace", use_container_width=True):
                res = supabase.table("entreprises").select("*").ilike("nom", nom.strip()).execute()
                if res.data and mdp == res.data[0].get("mot_de_passe", ""):
                    compte = res.data[0]
                    if "OPTIMA RH" not in (compte.get("projets_autorises") or ""):
                        st.error("🔒 Accès suspendu. Veuillez contacter BENMOUMENE TECH.")
                    else:
                        st.session_state["connected_company"] = compte
                        st.rerun()
                else:
                    st.error("Identifiants incorrects.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. ESPACE CLIENT CONNECTÉ ---
entreprise = st.session_state["connected_company"]
entreprise_id = entreprise["id"]
societe = entreprise["nom"]

with st.sidebar:
    st.title("⚡ Optima RH")
    st.write(f"🏢 **{societe}**")
    st.divider()
    
    st.markdown("### 📧 Configuration Email")
    st.caption("Pour envoyer des documents directement depuis l'app (Utilisez un mot de passe d'application Gmail).")
    mail_input = st.text_input("Votre adresse Gmail", value=st.session_state["smtp_config"]["email"])
    pass_input = st.text_input("Mot de passe d'application", type="password", value=st.session_state["smtp_config"]["password"])
    if st.button("Sauvegarder config SMTP"):
        st.session_state["smtp_config"] = {"email": mail_input, "password": pass_input}
        st.success("Config enregistrée (Session)")
        
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state["connected_company"] = None
        st.rerun()

res_emp = supabase.table("employes").select("*").eq("entreprise_id", entreprise_id).execute()
employes = res_emp.data if res_emp.data else []
df_emp = pd.DataFrame(employes)

tab_dash, tab_emp, tab_point, tab_docs, tab_paie = st.tabs(["📊 Dashboard", "👥 Base Salariés", "📅 Pointage & Exports", "📄 Docs RH", "💰 Paie"])

# --- TAB 1 : DASHBOARD ---
with tab_dash:
    st.markdown("### 📈 Vue Globale & Alertes")
    if not df_emp.empty:
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="glass-card"><h4>Effectif Actif</h4><h2>{len([e for e in employes if e.get("statut") == "Actif"])}</h2></div>', unsafe_allow_html=True)
        masse = df_emp['salaire_mensuel'].sum() if 'salaire_mensuel' in df_emp.columns else 0
        c2.markdown(f'<div class="glass-card"><h4>Masse Salariale</h4><h2>{masse:,.0f} DA</h2></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="glass-card"><h4>Postes Total</h4><h2>{df_emp["poste"].nunique()}</h2></div>', unsafe_allow_html=True)
        
        st.markdown("#### ⚠️ Alertes Contrats")
        alertes = 0
        for emp in employes:
            d_dep = emp.get("date_depart")
            if d_dep and emp.get("statut") == "Actif":
                if date.today() <= datetime.strptime(d_dep, "%Y-%m-%d").date() <= date.today() + timedelta(days=15):
                    alertes += 1
                    st.markdown(f'<div class="alert-card">⏳ <b>Fin imminente :</b> {emp["nom_complet"]} - Le {d_dep}</div>', unsafe_allow_html=True)
        if alertes == 0: st.success("✅ Aucune fin de contrat dans les 15 prochains jours.")
    else:
        st.info("Ajoutez des employés pour visualiser les indicateurs.")

# --- TAB 2 : GESTION DES EMPLOYÉS ---
with tab_emp:
    c_add, c_list = st.columns([1.2, 2], gap="large")
    with c_add:
        st.markdown('<div class="glass-card"><h4>➕ Nouveau Salarié</h4>', unsafe_allow_html=True)
        with st.form("form_add"):
            n = st.text_input("Nom & Prénom")
            p = st.text_input("Poste")
            s = st.number_input("Salaire Base (DA)", value=50000.0, step=5000.0)
            d_int = st.date_input("Date Intégration")
            if st.form_submit_button("Ajouter à la base", use_container_width=True):
                supabase.table("employes").insert({"entreprise_id": entreprise_id, "nom_complet": n, "poste": p, "salaire_mensuel": s, "date_integration": str(d_int), "statut": "Actif"}).execute()
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c_list:
        st.markdown("#### 📋 Répertoire & Export")
        if not df_emp.empty:
            df_export = df_emp[['nom_complet', 'poste', 'salaire_mensuel', 'date_integration', 'statut']]
            excel_pers = generer_excel_personnel(df_export, societe)
            
            c_d, c_e = st.columns(2)
            c_d.download_button("📥 Télécharger Excel Personnel", data=excel_pers, file_name=f"Personnel_{societe}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
            
            with c_e.popover("📧 Envoyer liste par email"):
                mail_dest = st.text_input("Email destinataire (Administration)")
                if st.button("Envoyer Excel", key="m1"):
                    succes, msg = envoyer_email(mail_dest, f"Situation Personnel - {societe}", "Veuillez trouver ci-joint l'état du personnel.", f"Personnel_{societe}.xlsx", excel_pers, "vnd.ms-excel")
                    if succes: st.success(msg)
                    else: st.error(msg)
                    
            st.dataframe(df_export, use_container_width=True, hide_index=True)

# --- TAB 3 : POINTAGE & EXPORT MENSUEL ---
with tab_point:
    if employes:
        t_saisie, t_recap = st.tabs(["📝 Saisie Journalière", "📊 Export Mensuel (Admin)"])
        
        with t_saisie:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            d_p = st.date_input("Date de Pointage", date.today())
            df_pt = pd.DataFrame([{"id": e['id'], "Employé": e['nom_complet'], "Statut": "Présent"} for e in employes])
            df_edit = st.data_editor(df_pt, column_config={"Statut": st.column_config.SelectboxColumn(options=["Présent", "Absent", "Demi-Journée", "Maladie"])}, hide_index=True, use_container_width=True)
            if st.button("💾 Enregistrer la journée", type="primary"):
                batch = [{"employe_id": int(r['id']), "date_pointage": str(d_p), "statut": r['Statut']} for _, r in df_edit.iterrows()]
                emp_ids = [int(r['id']) for _, r in df_edit.iterrows()]
                supabase.table("pointages").delete().in_("employe_id", emp_ids).eq("date_pointage", str(d_p)).execute()
                supabase.table("pointages").insert(batch).execute()
                st.success(f"Pointage du {d_p} validé !")
            st.markdown('</div>', unsafe_allow_html=True)

        with t_recap:
            st.markdown("#### Générer le rapport de présence du mois")
            c_m, c_a, _ = st.columns([1, 1, 2])
            mois = c_m.number_input("Mois", min_value=1, max_value=12, value=date.today().month)
            annee = c_a.number_input("Année", min_value=2024, value=date.today().year)
            
            if st.button("Calculer le bilan du mois"):
                emp_ids = [e['id'] for e in employes]
                res_pts = supabase.table("pointages").select("*").in_("employe_id", emp_ids).execute()
                if res_pts.data:
                    df_tous = pd.DataFrame(res_pts.data)
                    df_tous['date_pointage'] = pd.to_datetime(df_tous['date_pointage'])
                    df_mois = df_tous[(df_tous['date_pointage'].dt.month == mois) & (df_tous['date_pointage'].dt.year == annee)]
                    
                    recap = []
                    for emp in employes:
                        pts_emp = df_mois[df_mois['employe_id'] == emp['id']]
                        recap.append({
                            "Employé": emp['nom_complet'],
                            "Jours Présent": len(pts_emp[pts_emp['statut'] == 'Présent']),
                            "Demi-Journées": len(pts_emp[pts_emp['statut'] == 'Demi-Journée']),
                            "Absences": len(pts_emp[pts_emp['statut'] == 'Absent']),
                            "Total jours calculés": len(pts_emp[pts_emp['statut'] == 'Présent']) + (len(pts_emp[pts_emp['statut'] == 'Demi-Journée']) * 0.5)
                        })
                    df_recap = pd.DataFrame(recap)
                    st.dataframe(df_recap, use_container_width=True, hide_index=True)
                    
                    # Génération Excel Pointage
                    out_pt = io.BytesIO()
                    df_recap.to_excel(out_pt, index=False, engine='xlsxwriter')
                    excel_pt = out_pt.getvalue()
                    
                    c_d1, c_d2 = st.columns(2)
                    c_d1.download_button("📥 Télécharger Pointage Excel", data=excel_pt, file_name=f"Pointage_{mois}_{annee}.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
                    
                    with c_d2.popover("📧 Envoyer Pointage à l'Administration"):
                        m_admin = st.text_input("Email Administration")
                        if st.button("Envoyer Pointage"):
                            suc, msg = envoyer_email(m_admin, f"Pointage Mensuel - {societe} - {mois}/{annee}", "Ci-joint le relevé de pointage mensuel généré par Optima RH.", f"Pointage_{mois}_{annee}.xlsx", excel_pt, "vnd.ms-excel")
                            if suc: st.success(msg)
                            else: st.error(msg)
                else:
                    st.warning("Aucun pointage trouvé pour cette période.")

# --- TAB 4 : DOCUMENTS RH ---
with tab_docs:
    st.markdown("### 📄 Générateur de Documents")
    if employes:
        c_doc1, c_doc2 = st.columns([1, 1.5])
        e_doc = c_doc1.selectbox("Employé :", employes, format_func=lambda x: x["nom_complet"])
        t_doc = c_doc1.selectbox("Type :", ["Attestation de Travail", "Certificat de Travail"])
        
        if c_doc1.button("Générer PDF", type="primary", use_container_width=True):
            texte = f"L'entreprise {societe} atteste que M./Mme {e_doc['nom_complet']} travaille en tant que {e_doc['poste']} depuis le {e_doc.get('date_integration', 'N/A')}." if "Attestation" in t_doc else f"Certificat de travail pour M./Mme {e_doc['nom_complet']}, {e_doc['poste']}."
            pdf_b = generer_pdf(t_doc.upper(), texte, societe)
            st.session_state["last_pdf"] = {"name": f"{t_doc}_{e_doc['nom_complet']}.pdf", "bytes": pdf_b}
            
        if "last_pdf" in st.session_state:
            c_doc2.success("✅ Document prêt.")
            c_doc2.download_button("📥 Télécharger", data=st.session_state["last_pdf"]["bytes"], file_name=st.session_state["last_pdf"]["name"], mime="application/pdf")
            st.markdown('<div class="mail-box">', unsafe_allow_html=True)
            mail_emp = c_doc2.text_input("Envoyer par mail à :", placeholder="email.employe@gmail.com")
            if c_doc2.button("📧 Envoyer PDF"):
                s, m = envoyer_email(mail_emp, st.session_state["last_pdf"]["name"], "Veuillez trouver votre document RH en pièce jointe.", st.session_state["last_pdf"]["name"], st.session_state["last_pdf"]["bytes"], "pdf")
                if s: c_doc2.success(m)
                else: c_doc2.error(m)
            st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 5 : PAIE ALGÉRIENNE ---
with tab_paie:
    st.markdown("### 🇩🇿 Bulletins de Paie (CNAS/IRG)")
    if employes:
        e_paie = st.selectbox("Salarié :", employes, format_func=lambda x: x["nom_complet"])
        base = float(e_paie.get('salaire_mensuel') or 0.0)
        c_p1, c_p2 = st.columns(2)
        primes = c_p1.number_input("Primes (DA)", value=0.0)
        absences = c_p2.number_input("Absences (Jours)", value=0)
        
        sal_poste = (base * ((26 - absences) / 26)) + primes
        cnas = sal_poste * 0.09
        base_irg = sal_poste - cnas
        irg = calculer_irg(base_irg)
        net = base_irg - irg
        
        c_r1, c_r2, c_r3 = st.columns(3)
        c_r1.metric("Salaire Poste", f"{sal_poste:,.2f} DA")
        c_r2.metric("Retenues", f"{(cnas + irg):,.2f} DA")
        c_r3.metric("Net à Payer", f"{net:,.2f} DA")
        
        if st.button("Générer Bulletin PDF", type="primary"):
            texte_paie = f"BULLETIN DE PAIE\nEmployé : {e_paie['nom_complet']}\nPoste : {e_paie['poste']}\n\nSalaire Base: {base} DA\nAbsences: {absences}j\nPrimes: {primes} DA\n\nSALAIRE POSTE: {sal_poste} DA\nCNAS (9%): -{cnas} DA\nIRG: -{irg} DA\n\nNET A PAYER: {net} DA"
            pdf_paie = generer_pdf("Fiche de Paie", texte_paie, societe)
            st.session_state["last_paie"] = {"name": f"Paie_{e_paie['nom_complet']}.pdf", "bytes": pdf_paie}
            
        if "last_paie" in st.session_state:
            c_d, c_e = st.columns(2)
            c_d.download_button("📥 Télécharger Bulletin", data=st.session_state["last_paie"]["bytes"], file_name=st.session_state["last_paie"]["name"], mime="application/pdf", use_container_width=True)
            with c_e.popover("📧 Envoyer au salarié"):
                m_dest = st.text_input("Email du salarié")
                if st.button("Envoyer Bulletin"):
                    s, m = envoyer_email(m_dest, "Votre Fiche de Paie", "Veuillez trouver votre fiche de paie jointe.", st.session_state["last_paie"]["name"], st.session_state["last_paie"]["bytes"], "pdf")
                    if s: st.success(m)
                    else: st.error(m)