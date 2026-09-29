import math
import requests
import streamlit as st

# --- LA TUA API KEY DI FOOTBALL-DATA.ORG ---
API_KEY = "1e404410b39746348b71144ca6aea9ff"

# --- FUNZIONI STATISTICHE (POISSON & DIXON-COLES) ---
def calcola_poisson(media_gol, gol):
    return (math.pow(media_gol, gol) * math.exp(-media_gol)) / math.factorial(gol)

def correzione_dixon_coles(xg_casa, xg_ospite, g_casa, g_ospite, rho=-0.15):
    if g_casa == 0 and g_ospite == 0: return 1 - (xg_casa * xg_ospite * rho)
    elif g_casa == 0 and g_ospite == 1: return 1 + (xg_casa * rho)
    elif g_casa == 1 and g_ospite == 0: return 1 + (xg_ospite * rho)
    elif g_casa == 1 and g_ospite == 1: return 1 - rho
    else: return 1.0

def calcola_ev_e_kelly(prob_decimale, quota):
    ev = (prob_decimale * quota) - 1
    kelly_pieno = ev / (quota - 1) if quota > 1 else 0
    kelly_consigliato = (kelly_pieno / 4) * 100 
    return ev * 100, max(0, kelly_consigliato)

# --- FUNZIONE PER SCARICARE I DATI AUTOMATICI DA FOOTBALL-DATA.ORG ---
@st.cache_data(ttl=3600) # Salva in cache i dati per 1 ora per non esaurire le chiamate API
def carica_classifica(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {"X-Auth-Token": API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            squadre = {}
            for row in data['standings'][0]['table']:
                nome = row['team']['name']
                squadre[nome] = {
                    "pg": row['playedGames'],
                    "gf": row['goalsFor'],
                    "gs": row['goalsAgainst']
                }
            return squadre
        else:
            return None
    except Exception:
        return None

# --- IMPOSTAZIONI PAGINA WEB ---
st.set_page_config(page_title="Algoritmo Predittivo Pro", page_icon="⚽", layout="wide")
st.title("⚡ Algoritmo Predittivo Automatico PRO ⚽")
st.markdown("*Analisi automatica in tempo reale tramite API di Football-Data.org*")

# --- BARRA LATERALE PER CAMPIONATO ---
st.sidebar.header("🌍 Scegli il Campionato")
campionati = {
    "Serie A (Italia)": "SA",
    "Premier League (Inghilterra)": "PL",
    "La Liga (Spagna)": "PD",
    "Bundesliga (Germania)": "BL1",
    "Ligue 1 (Francia)": "FL1",
    "Champions League": "CL"
}
scelta_campionato = st.sidebar.selectbox("Seleziona:", list(campionati.keys()))
code_campionato = campionati[scelta_campionato]

# Caricamento automatico delle squadre senza chiedere l'API Key!
squadre_dati = carica_classifica(code_campionato)
    
if squadre_dati is None:
    st.error("⚠️ Errore nel caricamento dei dati. Attendi un minuto prima di riprovare (limite richieste API gratuite).")
else:
    elenco_squadre = sorted(list(squadre_dati.keys()))
    
    # --- SELEZIONE AUTOMATICA SQUADRE ---
    with st.form("dati_partita"):
        col1, col2 = st.columns(2)
        with col1:
            squadra_casa = st.selectbox("🏠 Squadra in Casa:", elenco_squadre, index=0)
        with col2:
            squadra_ospite = st.selectbox("✈️ Squadra in Trasferta:", elenco_squadre, index=min(1, len(elenco_squadre)-1))
        
        st.markdown("---")
        st.subheader("📊 Quote del Bookmaker (Opzionale - lascia 0 per ignorare)")
        q1, q2, q3 = st.columns(3)
        quota_1 = q1.number_input("Quota 1", min_value=0.0, value=0.0)
        quota_x = q2.number_input("Quota X", min_value=0.0, value=0.0)
        quota_2 = q3.number_input("Quota 2", min_value=0.0, value=0.0)
        
        q5, q6, q7, q8 = st.columns(4)
        quota_un = q5.number_input("Quota Under 2.5", min_value=0.0, value=0.0)
        quota_ov = q6.number_input("Quota Over 2.5", min_value=0.0, value=0.0)
        quota_gg = q7.number_input("Quota Goal (GG)", min_value=0.0, value=0.0)
        quota_ng = q8.number_input("Quota No Goal (NG)", min_value=0.0, value=0.0)

        invia_dati = st.form_submit_button("🚀 Calcola Pronostico Automatico")

    # --- MOTORE DI CALCOLO AUTOMATICO ---
    if invia_dati:
        dati_c = squadre_dati[squadra_casa]
        dati_o = squadre_dati[squadra_ospite]

        # Calcolo medie gol reali recuperati dall'API
        media_gf_c = dati_c['gf'] / dati_c['pg'] if dati_c['pg'] > 0 else 1.0
        media_gs_c = dati_c['gs'] / dati_c['pg'] if dati_c['pg'] > 0 else 1.0
        media_gf_o = dati_o['gf'] / dati_o['pg'] if dati_o['pg'] > 0 else 1.0
        media_gs_o = dati_o['gs'] / dati_o['pg'] if dati_o['pg'] > 0 else 1.0

        # xG Attesi
        xg_casa = max(0.5, (media_gf_c * media_gs_o) / 1.35)
        xg_ospite = max(0.5, (media_gf_o * media_gs_c) / 1.35)

        # Matrice Poisson e Dixon-Coles
        prob_1, prob_x, prob_2, prob_over, prob_under, prob_gg, prob_ng = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        risultati_esatti = {}
        tot_prob = 0.0

        for g_casa in range(10):
            for g_ospite in range(10):
                p_base = calcola_poisson(xg_casa, g_casa) * calcola_poisson(xg_ospite, g_ospite)
                correzione = correzione_dixon_coles(xg_casa, xg_ospite, g_casa, g_ospite)
                p_esatto = max(0, p_base * correzione)
                
                risultati_esatti[f"{g_casa}-{g_ospite}"] = p_esatto
                tot_prob += p_esatto

                if g_casa > g_ospite: prob_1 += p_esatto
                elif g_casa == g_ospite: prob_x += p_esatto
                else: prob_2 += p_esatto

                tot_gol = g_casa + g_ospite
                if tot_gol > 2.5: prob_over += p_esatto
                else: prob_under += p_esatto

                if g_casa > 0 and g_ospite > 0: prob_gg += p_esatto
                else: prob_ng += p_esatto

        # Normalizzazione
        prob_1, prob_x, prob_2 = prob_1/tot_prob, prob_x/tot_prob, prob_2/tot_prob
        prob_under, prob_over = prob_under/tot_prob, prob_over/tot_prob
        prob_gg, prob_ng = prob_gg/tot_prob, prob_ng/tot_prob

        for k in risultati_esatti: risultati_esatti[k] = risultati_esatti[k] / tot_prob
        top_risultati = sorted(risultati_esatti.items(), key=lambda x: x[1], reverse=True)[:3]

        # --- MOSTRA RISULTATI ---
        st.divider()
        st.header(f"📊 Pronostico: {squadra_casa} vs {squadra_ospite}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Vittoria 1", f"{prob_1*100:.1f}%")
        c2.metric("Pareggio X", f"{prob_x*100:.1f}%")
        c3.metric("Vittoria 2", f"{prob_2*100:.1f}%")

        c4, c5, c6, c7 = st.columns(4)
        c4.metric("Under 2.5", f"{prob_under*100:.1f}%")
        c5.metric("Over 2.5", f"{prob_over*100:.1f}%")
        c6.metric("Goal (GG)", f"{prob_gg*100:.1f}%")
        c7.metric("No Goal (NG)", f"{prob_ng*100:.1f}%")

        st.markdown("### 🎯 Top 3 Risultati Esatti Probabili")
        for res, p in top_risultati:
            st.write(f"• **{res}** al {p*100:.1f}%")

        # --- VALUE BETTING ---
        mappa_prob = {
            "1": (prob_1, quota_1, f"Vittoria {squadra_casa}"),
            "X": (prob_x, quota_x, "Pareggio"),
            "2": (prob_2, quota_2, f"Vittoria {squadra_ospite}"),
            "Under 2.5": (prob_under, quota_un, "Under 2.5"),
            "Over 2.5": (prob_over, quota_ov, "Over 2.5"),
            "Goal": (prob_gg, quota_gg, "Goal (GG)"),
            "NoGoal": (prob_ng, quota_ng, "No Goal (NG)")
        }

        giocate_analizzate = []
        for chiave, (p_dec, q, nome_esito) in mappa_prob.items():
            if q > 0:
                ev, kelly = calcola_ev_e_kelly(p_dec, q)
                if ev > 0:
                    giocate_analizzate.append({"esito": nome_esito, "ev": ev, "kelly": kelly, "quota": q, "prob": p_dec * 100})

        if giocate_analizzate:
            st.divider()
            st.subheader("🏆 Verdetto Value Bet (Quote Inserite)")
            giocate_analizzate.sort(key=lambda x: x["ev"], reverse=True)
            top = giocate_analizzate[0]
            st.success(f"🎯 **GIOCATA DI VALORE ASSOLUTO: {top['esito']}** (Quota {top['quota']:.2f} | EV: +{top['ev']:.2f}%)")
