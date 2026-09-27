import math
import streamlit as st

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

# --- IMPOSTAZIONI PAGINA WEB ---
st.set_page_config(page_title="Algoritmo Predittivo Pro", page_icon="⚽", layout="wide")
st.title("⚡ Algoritmo Predittivo PRO ⚽")
st.markdown("*Modello statistico avanzato con Poisson, correzione Dixon-Coles e calcolo del Valore.*")

# --- AREA DI INSERIMENTO DATI ---
with st.form("dati_partita"):
    col_casa, col_ospite = st.columns(2)
    
    with col_casa:
        st.header("🏠 Squadra in Casa")
        squadra_casa = st.text_input("Nome Squadra:", "Casa").strip()
        pg_tot_c = st.number_input("Partite totali giocate:", min_value=1.0, value=10.0)
        gf_tot_c = st.number_input("Gol totali FATTI:", min_value=0.0, value=15.0)
        gs_tot_c = st.number_input("Gol totali SUBITI:", min_value=0.0, value=10.0)
        
        st.markdown("**Forma Recente (Ultime partite)**")
        pg_rec_c = st.number_input("Partite recenti:", min_value=1.0, value=5.0)
        gf_rec_c = st.number_input("Gol FATTI recenti:", min_value=0.0, value=8.0)
        gs_rec_c = st.number_input("Gol SUBITI recenti:", min_value=0.0, value=5.0)

    with col_ospite:
        st.header("✈️ Squadra in Trasferta")
        squadra_ospite = st.text_input("Nome Squadra :", "Ospite").strip()
        pg_tot_o = st.number_input("Partite totali giocate: ", min_value=1.0, value=10.0)
        gf_tot_o = st.number_input("Gol totali FATTI: ", min_value=0.0, value=12.0)
        gs_tot_o = st.number_input("Gol totali SUBITI: ", min_value=0.0, value=14.0)
        
        st.markdown("**Forma Recente (Ultime partite)**")
        pg_rec_o = st.number_input("Partite recenti: ", min_value=1.0, value=5.0)
        gf_rec_o = st.number_input("Gol FATTI recenti: ", min_value=0.0, value=6.0)
        gs_rec_o = st.number_input("Gol SUBITI recenti: ", min_value=0.0, value=7.0)
        
    st.markdown("---")
    st.subheader("📊 Quote del Bookmaker (Lascia 0 per ignorare)")
    q1, q2, q3, q4 = st.columns(4)
    quota_1 = q1.number_input("Quota 1", min_value=0.0, value=0.0)
    quota_x = q2.number_input("Quota X", min_value=0.0, value=0.0)
    quota_2 = q3.number_input("Quota 2", min_value=0.0, value=0.0)
    
    q5, q6, q7, q8 = st.columns(4)
    quota_un = q5.number_input("Quota Under 2.5", min_value=0.0, value=0.0)
    quota_ov = q6.number_input("Quota Over 2.5", min_value=0.0, value=0.0)
    quota_gg = q7.number_input("Quota Goal (GG)", min_value=0.0, value=0.0)
    quota_ng = q8.number_input("Quota No Goal (NG)", min_value=0.0, value=0.0)

    invia_dati = st.form_submit_button("🚀 Avvia Calcolo Probabilità")

# --- MOTORE DI CALCOLO (Si attiva solo dopo il click sul bottone) ---
if invia_dati:
    with st.spinner("Calcolo delle probabilità in corso..."):
        # Ponderazione Dati Casa
        media_f_tot_c = gf_tot_c / pg_tot_c
        media_s_tot_c = gs_tot_c / pg_tot_c
        media_f_rec_c = gf_rec_c / pg_rec_c
        media_s_rec_c = gs_rec_c / pg_rec_c
        gf_casa = (media_f_tot_c * 0.35) + (media_f_rec_c * 0.65)
        gs_casa = (media_s_tot_c * 0.35) + (media_s_rec_c * 0.65)

        # Ponderazione Dati Ospite
        media_f_tot_o = gf_tot_o / pg_tot_o
        media_s_tot_o = gs_tot_o / pg_tot_o
        media_f_rec_o = gf_rec_o / pg_rec_o
        media_s_rec_o = gs_rec_o / pg_rec_o
        gf_ospite = (media_f_tot_o * 0.35) + (media_f_rec_o * 0.65)
        gs_ospite = (media_s_tot_o * 0.35) + (media_s_rec_o * 0.65)

        # xG Attesi
        xg_casa = max(0.5, (gf_casa * gs_ospite) / 1.35)
        xg_ospite = max(0.5, (gf_ospite * gs_casa) / 1.35)

        # Variabili Statistiche
        prob_1, prob_x, prob_2, prob_over, prob_under, prob_gg, prob_ng = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        mg_1_2, mg_1_3, mg_2_3, mg_2_4 = 0.0, 0.0, 0.0, 0.0
        risultati_esatti = {}
        tot_prob = 0.0

        # Loop Matrice Poisson
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

                if 1 <= tot_gol <= 2: mg_1_2 += p_esatto
                if 1 <= tot_gol <= 3: mg_1_3 += p_esatto
                if 2 <= tot_gol <= 3: mg_2_3 += p_esatto
                if 2 <= tot_gol <= 4: mg_2_4 += p_esatto

        # Normalizzazione
        prob_1, prob_x, prob_2 = prob_1/tot_prob, prob_x/tot_prob, prob_2/tot_prob
        prob_under, prob_over = prob_under/tot_prob, prob_over/tot_prob
        prob_gg, prob_ng = prob_gg/tot_prob, prob_ng/tot_prob
        mg_1_2, mg_1_3, mg_2_3, mg_2_4 = mg_1_2/tot_prob, mg_1_3/tot_prob, mg_2_3/tot_prob, mg_2_4/tot_prob

        for k in risultati_esatti: risultati_esatti[k] = risultati_esatti[k] / tot_prob
        top_risultati = sorted(risultati_esatti.items(), key=lambda x: x[1], reverse=True)[:3]

        # --- MOSTRA I RISULTATI A SCHERMO ---
        st.divider()
        st.header(f"📊 Probabilità Reali: {squadra_casa} vs {squadra_ospite}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Vittoria 1", f"{prob_1*100:.1f}%")
        c2.metric("Pareggio X", f"{prob_x*100:.1f}%")
        c3.metric("Vittoria 2", f"{prob_2*100:.1f}%")

        c4, c5, c6, c7 = st.columns(4)
        c4.metric("Under 2.5", f"{prob_under*100:.1f}%")
        c5.metric("Over 2.5", f"{prob_over*100:.1f}%")
        c6.metric("Goal (GG)", f"{prob_gg*100:.1f}%")
        c7.metric("No Goal (NG)", f"{prob_ng*100:.1f}%")
        
        st.write(f"**Multigoal Totali:** 1-2 ({mg_1_2*100:.1f}%) | 1-3 ({mg_1_3*100:.1f}%) | 2-3 ({mg_2_3*100:.1f}%) | 2-4 ({mg_2_4*100:.1f}%)")
        
        st.markdown("### 🎯 Top 3 Risultati Esatti")
        for res, p in top_risultati:
            st.write(f"• **{res}** al {p*100:.1f}%")

        # --- BETTING EXCHANGE ---
        st.divider()
        st.subheader("🔄 Strategia Betting Exchange (es. Betfair)")
        esiti_exchange = {
            "1": prob_1, "X": prob_x, "2": prob_2,
            "Over 2.5": prob_over, "Under 2.5": prob_under,
            "Goal": prob_gg, "No Goal": prob_ng
        }
        miglior_punta = max(esiti_exchange, key=esiti_exchange.get)
        miglior_banca = min(esiti_exchange, key=esiti_exchange.get)

        st.info(f"🔵 **IDEALE DA PUNTARE (BACK): {miglior_punta} ({esiti_exchange[miglior_punta]*100:.1f}%)**  \nL'evento più probabile in assoluto sul tabellone.")
        
        if esiti_exchange[miglior_banca] < 0.25:
            st.warning(f"🔴 **IDEALE DA BANCARE (LAY): {miglior_banca} (Probabilità solo {esiti_exchange[miglior_banca]*100:.1f}%)**  \nL'evento è altamente improbabile. Ottima occasione per bancarlo se trovi quote basse.")
        else:
            st.warning("🔴 **IDEALE DA BANCARE (LAY): Nessun evento netto.**  \nTutti gli esiti hanno probabilità troppo alte per rischiare una bancata.")

        # --- ANALISI QUOTE / VALUE BETTING ---
        st.divider()
        st.subheader("🏆 Verdetto Algoritmo (Value Bet)")
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
            giocate_analizzate.sort(key=lambda x: x["ev"], reverse=True)
            top = giocate_analizzate[0]
            st.success(f"🎯 **LA GIOCATA DI VALORE ASSOLUTO: {top['esito']}**")
            st.write(f"• Quota Bookmaker: **{top['quota']:.2f}**")
            st.write(f"• Probabilità Reale: **{top['prob']:.1f}%**")
            st.write(f"• Expected Value: **+{top['ev']:.2f}%**")
            st.write(f"• Stake Consigliato (Kelly): **{top['kelly']:.2f}%** della cassa")
            
            if len(giocate_analizzate) > 1:
                st.markdown("**Altre giocate con valore matematico positivo:**")
                for g in giocate_analizzate[1:4]:
                    st.write(f"- {g['esito']} a quota {g['quota']:.2f} (EV: +{g['ev']:.2f}%)")
        else:
            st.error("❌ Nessun valore matematico (Value Bet) trovato tra le quote che hai inserito.")
