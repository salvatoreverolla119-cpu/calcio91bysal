import math
import requests
import streamlit as st

# --- CONFIGURAZIONE API FOOTBALL-DATA.ORG ---
API_KEY = "1e404410b39746348b71144ca6aea9ff"

# --- FUNZIONI STATISTICHE (POISSON & DIXON-COLES) ---
def calcola_poisson(media_gol, gol):
    """Calcola la probabilità base di Poisson."""
    return (math.pow(media_gol, gol) * math.exp(-media_gol)) / math.factorial(gol)

def correzione_dixon_coles(xg_casa, xg_ospite, g_casa, g_ospite, rho=-0.15):
    """
    Applica il fattore Dixon-Coles per correggere la sottostima dei pareggi 
    (0-0, 1-1) e delle vittorie di misura (1-0, 0-1).
    """
    if g_casa == 0 and g_ospite == 0:
        return 1 - (xg_casa * xg_ospite * rho)
    elif g_casa == 0 and g_ospite == 1:
        return 1 + (xg_casa * rho)
    elif g_casa == 1 and g_ospite == 0:
        return 1 + (xg_ospite * rho)
    elif g_casa == 1 and g_ospite == 1:
        return 1 - rho
    else:
        return 1.0

def calcola_ev_e_kelly(prob_decimale, quota):
    """Calcola l'Expected Value (EV) e la percentuale di cassa consigliata (Kelly)."""
    ev = (prob_decimale * quota) - 1
    kelly_pieno = ev / (quota - 1) if quota > 1 else 0
    kelly_consigliato = (kelly_pieno / 4) * 100 
    return ev * 100, max(0, kelly_consigliato)

# --- CARICAMENTO AUTOMATICO DATI DA API ---
@st.cache_data(ttl=3600)
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

# --- CONFIGURAZIONE INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="Algoritmo Predittivo Pro & Exchange", page_icon="⚡", layout="wide")
st.title("⚡ ALGORITMO PREDITTIVO PRO (Dixon-Coles & Exchange) ⚽")
st.markdown("*Analisi automatica in tempo reale con quote bookmaker e strategie Betting Exchange*")

# --- SELEZIONE CAMPIONATO ---
st.sidebar.header("🌍 Scegli il Campionato")
campionati = {
    "Serie A (Italia)": "SA",
    "Premier League (Inghilterra)": "PL",
    "La Liga (Spagna)": "PD",
    "Bundesliga (Germania)": "BL1",
    "Ligue 1 (Francia)": "FL1",
    "Champions League": "CL"
}
scelta_campionato = st.sidebar.selectbox("Campionato:", list(campionati.keys()))
code_campionato = campionati[scelta_campionato]

squadre_dati = carica_classifica(code_campionato)

if squadre_dati is None:
    st.error("⚠️ Impossibile caricare i dati dall'API. Riprova tra un minuto (limite richieste API raggiunto).")
else:
    elenco_squadre = sorted(list(squadre_dati.keys()))

    with st.form("form_partita"):
        st.subheader("📋 Selezione Partita")
        col_c, col_o = st.columns(2)
        with col_c:
            squadra_casa = st.selectbox("🏠 Squadra Casa:", elenco_squadre, index=0)
        with col_o:
            squadra_ospite = st.selectbox("✈️ Squadra Trasferta:", elenco_squadre, index=min(1, len(elenco_squadre)-1))

        st.markdown("---")
        st.subheader("📊 Quote Bookmaker (Opzionale per Value Betting)")
        st.caption("Lascia 0.0 per ignorare l'analisi di una specifica quota")

        q1, qx, q2 = st.columns(3)
        quota_1 = q1.number_input(f"Quota 1 ({squadra_casa})", min_value=0.0, value=0.0, step=0.05)
        quota_x = qx.number_input("Quota X (Pareggio)", min_value=0.0, value=0.0, step=0.05)
        quota_2 = q2.number_input(f"Quota 2 ({squadra_ospite})", min_value=0.0, value=0.0, step=0.05)

        qu, qo, qgg, qng = st.columns(4)
        quota_under = qu.number_input("Quota Under 2.5", min_value=0.0, value=0.0, step=0.05)
        quota_over = qo.number_input("Quota Over 2.5", min_value=0.0, value=0.0, step=0.05)
        quota_gg = qgg.number_input("Quota Goal (GG)", min_value=0.0, value=0.0, step=0.05)
        quota_ng = qng.number_input("Quota No Goal (NG)", min_value=0.0, value=0.0, step=0.05)

        btn_calcola = st.form_submit_button("🚀 ESEGUI ANALISI COMPLETA")

    if btn_calcola:
        dati_c = squadre_dati[squadra_casa]
        dati_o = squadre_dati[squadra_ospite]

        # Calcolo medie per partita
        media_gf_c = dati_c['gf'] / dati_c['pg'] if dati_c['pg'] > 0 else 1.0
        media_gs_c = dati_c['gs'] / dati_c['pg'] if dati_c['pg'] > 0 else 1.0
        media_gf_o = dati_o['gf'] / dati_o['pg'] if dati_o['pg'] > 0 else 1.0
        media_gs_o = dati_o['gs'] / dati_o['pg'] if dati_o['pg'] > 0 else 1.0

        # Expected Goals (xG)
        xg_casa = max(0.5, (media_gf_c * media_gs_o) / 1.35)
        xg_ospite = max(0.5, (media_gf_o * media_gs_c) / 1.35)

        # Inizializzazione variabili
        prob_1, prob_x, prob_2 = 0.0, 0.0, 0.0
        prob_over, prob_under = 0.0, 0.0
        prob_gg, prob_ng = 0.0, 0.0

        mg_1_2, mg_1_3, mg_1_4, mg_2_3, mg_2_4, mg_3_4 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        mg_casa_1_2, mg_casa_1_3 = 0.0, 0.0
        mg_osp_1_2, mg_osp_1_3 = 0.0, 0.0

        risultati_esatti = {}
        tot_prob = 0.0

        # Matrice di calcolo
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

                # Multigoal Totali
                if 1 <= tot_gol <= 2: mg_1_2 += p_esatto
                if 1 <= tot_gol <= 3: mg_1_3 += p_esatto
                if 1 <= tot_gol <= 4: mg_1_4 += p_esatto
                if 2 <= tot_gol <= 3: mg_2_3 += p_esatto
                if 2 <= tot_gol <= 4: mg_2_4 += p_esatto
                if 3 <= tot_gol <= 4: mg_3_4 += p_esatto

                # Multigoal Squadra
                if 1 <= g_casa <= 2: mg_casa_1_2 += p_esatto
                if 1 <= g_casa <= 3: mg_casa_1_3 += p_esatto
                if 1 <= g_ospite <= 2: mg_osp_1_2 += p_esatto
                if 1 <= g_ospite <= 3: mg_osp_1_3 += p_esatto

        # Normalizzazione
        prob_1, prob_x, prob_2 = prob_1/tot_prob, prob_x/tot_prob, prob_2/tot_prob
        prob_under, prob_over = prob_under/tot_prob, prob_over/tot_prob
        prob_gg, prob_ng = prob_gg/tot_prob, prob_ng/tot_prob

        mg_1_2, mg_1_3, mg_1_4 = mg_1_2/tot_prob, mg_1_3/tot_prob, mg_1_4/tot_prob
        mg_2_3, mg_2_4, mg_3_4 = mg_2_3/tot_prob, mg_2_4/tot_prob, mg_3_4/tot_prob
        mg_casa_1_2, mg_casa_1_3 = mg_casa_1_2/tot_prob, mg_casa_1_3/tot_prob
        mg_osp_1_2, mg_osp_1_3 = mg_osp_1_2/tot_prob, mg_osp_1_3/tot_prob

        for k in risultati_esatti:
            risultati_esatti[k] = risultati_esatti[k] / tot_prob
        top_risultati = sorted(risultati_esatti.items(), key=lambda x: x[1], reverse=True)[:3]

        # --- VISUALIZZAZIONE RISULTATI ---
        st.divider()
        st.header(f"📊 PROBABILITÀ REALI CALCOLATE: {squadra_casa} vs {squadra_ospite}")

        # 1X2 & Main Markets
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Vittoria 1 ({squadra_casa})", f"{prob_1*100:.1f}%")
        c2.metric("Pareggio X", f"{prob_x*100:.1f}%")
        c3.metric(f"Vittoria 2 ({squadra_ospite})", f"{prob_2*100:.1f}%")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Under 2.5", f"{prob_under*100:.1f}%")
        m2.metric("Over 2.5", f"{prob_over*100:.1f}%")
        m3.metric("Goal (GG)", f"{prob_gg*100:.1f}%")
        m4.metric("No Goal (NG)", f"{prob_ng*100:.1f}%")

        # Multigoal
        st.subheader("⚽ Multigoal Totali & Squadra")
        mg_col1, mg_col2 = st.columns(2)
        with mg_col1:
            st.markdown("**Multigoal Match:**")
            st.write(f"• Multigoal 1-2: **{mg_1_2*100:.1f}%**")
            st.write(f"• Multigoal 1-3: **{mg_1_3*100:.1f}%**")
            st.write(f"• Multigoal 1-4: **{mg_1_4*100:.1f}%**")
            st.write(f"• Multigoal 2-3: **{mg_2_3*100:.1f}%**")
            st.write(f"• Multigoal 2-4: **{mg_2_4*100:.1f}%**")
            st.write(f"• Multigoal 3-4: **{mg_3_4*100:.1f}%**")
        with mg_col2:
            st.markdown("**Multigoal Singole Squadre:**")
            st.write(f"• {squadra_casa} (Casa) MG 1-2: **{mg_casa_1_2*100:.1f}%**")
            st.write(f"• {squadra_casa} (Casa) MG 1-3: **{mg_casa_1_3*100:.1f}%**")
            st.write(f"• {squadra_ospite} (Trasferta) MG 1-2: **{mg_osp_1_2*100:.1f}%**")
            st.write(f"• {squadra_ospite} (Trasferta) MG 1-3: **{mg_osp_1_3*100:.1f}%**")

        # Risultati Esatti
        st.subheader("🎯 Top 3 Risultati Esatti Probabili")
        for res, p in top_risultati:
            st.write(f"• **{res}** al **{p*100:.1f}%**")

        # --- SEZIONE BETTING EXCHANGE (PUNTA / BANCA) ---
        st.divider()
        st.header("🔄 STRATEGIA BETTING EXCHANGE (es. Betfair)")

        esiti_exchange = {
            "1": prob_1, "X": prob_x, "2": prob_2,
            "Over 2.5": prob_over, "Under 2.5": prob_under,
            "Goal": prob_gg, "No Goal": prob_ng
        }

        miglior_punta = max(esiti_exchange, key=esiti_exchange.get)
        miglior_banca = min(esiti_exchange, key=esiti_exchange.get)

        st.info(f"🔵 **IDEALE DA PUNTARE (BACK): {miglior_punta}** ({esiti_exchange[miglior_punta]*100:.1f}%)\n\n"
                f"→ È l'evento con la probabilità più alta in assoluto tra i mercati principali.")

        if esiti_exchange[miglior_banca] < 0.25:
            st.warning(f"🔴 **IDEALE DA BANCARE (LAY): {miglior_banca}** (Probabilità solo {esiti_exchange[miglior_banca]*100:.1f}%)\n\n"
                       f"→ L'evento è altamente improbabile (< 25%). Ottima occasione per bancare se la quota è contenuta.")
        else:
            st.warning(f"🔴 **IDEALE DA BANCARE (LAY): Nessun evento netto.**\n\n"
                       f"L'esito meno probabile è **{miglior_banca}** al {esiti_exchange[miglior_banca]*100:.1f}%, ma la percentuale è troppo alta per bancare in sicurezza.")

        # --- SEZIONE VALUE BETTING & KELLY ---
        st.divider()
        st.header("🏆 VERDETTO ALGORITMO: VALUE BETTING & KELLY")

        mappa_prob = {
            "1": (prob_1, quota_1, f"Vittoria {squadra_casa}"),
            "X": (prob_x, quota_x, "Pareggio (X)"),
            "2": (prob_2, quota_2, f"Vittoria {squadra_ospite}"),
            "Under 2.5": (prob_under, quota_under, "Under 2.5"),
            "Over 2.5": (prob_over, quota_over, "Over 2.5"),
            "Goal": (prob_gg, quota_gg, "Goal (GG)"),
            "No Goal": (prob_ng, quota_ng, "No Goal (NG)")
        }

        giocate_analizzate = []
        for chiave, (p_dec, q, nome_esito) in mappa_prob.items():
            if q > 0:
                ev, kelly = calcola_ev_e_kelly(p_dec, q)
                if ev > 0:
                    giocate_analizzate.append({
                        "esito": nome_esito,
                        "ev": ev,
                        "kelly": kelly,
                        "quota": q,
                        "prob": p_dec * 100
                    })

        if giocate_analizzate:
            giocate_analizzate.sort(key=lambda x: x["ev"], reverse=True)
            top = giocate_analizzate[0]

            st.success(f"🎯 **GIOCATA DI VALORE ASSOLUTO: {top['esito']}**\n\n"
                       f"• **Quota Bookmaker:** {top['quota']:.2f}\n\n"
                       f"• **Probabilità Reale:** {top['prob']:.1f}%\n\n"
                       f"• **Expected Value (Vantaggio Matematico):** +{top['ev']:.2f}%\n\n"
                       f"• **Stake Consigliato (Kelly Cautelativo):** {top['kelly']:.2f}% del budget")

            if len(giocate_analizzate) > 1:
                st.markdown("### ➕ Altre giocate con valore matematico positivo:")
                for g in giocate_analizzate[1:]:
                    st.write(f"• **{g['esito']}** a quota **{g['quota']:.2f}** (EV: +{g['ev']:.2f}% | Stake Kelly: {g['kelly']:.2f}%)")
        else:
            st.error("❌ **NESSUN VALORE MATEMATICO TROVATO SULLE QUOTE INSERITE.**\n\n"
                     "Le quote fornite non presentano un vantaggio statistico sul lungo periodo rispetto alle probabilità reali dell'algoritmo.")
