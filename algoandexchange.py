import math

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

def richiedi_dati_squadra(nome_squadra):
    """Acquisisce i dati totali e quelli recenti per calcolare lo stato di forma."""
    print(f"\n--- DATI {nome_squadra.upper()} ---")
    pg_tot = float(input(f"Partite totali giocate (Campionato): "))
    gf_tot = float(input(f"Gol totali FATTI: "))
    gs_tot = float(input(f"Gol totali SUBITI: "))
    
    print(f"  [Forma Recente - Ultime 5 Partite]")
    pg_rec = float(input(f"Partite recenti (es. 5): "))
    gf_rec = float(input(f"Gol FATTI nelle ultime {int(pg_rec)}: "))
    gs_rec = float(input(f"Gol SUBITI nelle ultime {int(pg_rec)}: "))
    
    media_fatti_tot = gf_tot / pg_tot if pg_tot > 0 else 0
    media_subiti_tot = gs_tot / pg_tot if pg_tot > 0 else 0
    
    media_fatti_rec = gf_rec / pg_rec if pg_rec > 0 else media_fatti_tot
    media_subiti_rec = gs_rec / pg_rec if pg_rec > 0 else media_subiti_tot
    
    gf_ponderato = (media_fatti_tot * 0.35) + (media_fatti_rec * 0.65)
    gs_ponderato = (media_subiti_tot * 0.35) + (media_subiti_rec * 0.65)
    
    return gf_ponderato, gs_ponderato

def calcola_ev_e_kelly(prob_decimale, quota):
    """Calcola l'Expected Value (EV) e la percentuale di cassa consigliata (Kelly)."""
    ev = (prob_decimale * quota) - 1
    kelly_pieno = ev / (quota - 1) if quota > 1 else 0
    kelly_consigliato = (kelly_pieno / 4) * 100 
    return ev * 100, max(0, kelly_consigliato)

def main():
    print("\n" + "=" * 60)
    print(" ⚡ ALGORITMO PREDITTIVO PRO (Dixon-Coles & Exchange)")
    print("=" * 60)

    squadra_casa = input("Nome Squadra Casa: ").strip()
    squadra_ospite = input("Nome Squadra Trasferta: ").strip()

    gf_casa, gs_casa = richiedi_dati_squadra(squadra_casa)
    gf_ospite, gs_ospite = richiedi_dati_squadra(squadra_ospite)

    xg_casa = max(0.5, (gf_casa * gs_ospite) / 1.35)
    xg_ospite = max(0.5, (gf_ospite * gs_casa) / 1.35)

    prob_1, prob_x, prob_2 = 0.0, 0.0, 0.0
    prob_over, prob_under = 0.0, 0.0
    prob_gg, prob_ng = 0.0, 0.0
    
    mg_1_2, mg_1_3, mg_1_4, mg_2_3, mg_2_4, mg_3_4 = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    mg_casa_1_2, mg_casa_1_3 = 0.0, 0.0
    mg_osp_1_2, mg_osp_1_3 = 0.0, 0.0

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

            if 1 <= tot_gol <= 2: mg_1_2 += p_esatto
            if 1 <= tot_gol <= 3: mg_1_3 += p_esatto
            if 1 <= tot_gol <= 4: mg_1_4 += p_esatto
            if 2 <= tot_gol <= 3: mg_2_3 += p_esatto
            if 2 <= tot_gol <= 4: mg_2_4 += p_esatto
            if 3 <= tot_gol <= 4: mg_3_4 += p_esatto

            if 1 <= g_casa <= 2: mg_casa_1_2 += p_esatto
            if 1 <= g_casa <= 3: mg_casa_1_3 += p_esatto
            if 1 <= g_ospite <= 2: mg_osp_1_2 += p_esatto
            if 1 <= g_ospite <= 3: mg_osp_1_3 += p_esatto

    # Normalizzazione finale
    prob_1, prob_x, prob_2 = prob_1/tot_prob, prob_x/tot_prob, prob_2/tot_prob
    prob_under, prob_over = prob_under/tot_prob, prob_over/tot_prob
    prob_gg, prob_ng = prob_gg/tot_prob, prob_ng/tot_prob
    
    mg_1_2, mg_1_3, mg_2_3, mg_2_4 = mg_1_2/tot_prob, mg_1_3/tot_prob, mg_2_3/tot_prob, mg_2_4/tot_prob
    mg_casa_1_2, mg_casa_1_3 = mg_casa_1_2/tot_prob, mg_casa_1_3/tot_prob
    mg_osp_1_2, mg_osp_1_3 = mg_osp_1_2/tot_prob, mg_osp_1_3/tot_prob

    for k in risultati_esatti: risultati_esatti[k] = risultati_esatti[k] / tot_prob
    top_risultati = sorted(risultati_esatti.items(), key=lambda x: x[1], reverse=True)[:3]

    print("\n" + "=" * 60)
    print(f" 📊 PROBABILITÀ REALI CALCOLATE: {squadra_casa} vs {squadra_ospite}")
    print("=" * 60)
    print(f" [1X2] 1: {prob_1*100:.1f}% | X: {prob_x*100:.1f}% | 2: {prob_2*100:.1f}%")
    print(f" [O/U] Under 2.5: {prob_under*100:.1f}% | Over 2.5: {prob_over*100:.1f}%")
    print(f" [G/NG] Goal (GG): {prob_gg*100:.1f}% | No Goal (NG): {prob_ng*100:.1f}%")
    print("-" * 60)
    print(" [MULTIGOAL TOTALI]")
    print(f" 1-2: {mg_1_2*100:.1f}% | 1-3: {mg_1_3*100:.1f}% | 2-3: {mg_2_3*100:.1f}% | 2-4: {mg_2_4*100:.1f}%")
    print("-" * 60)
    print(" 🎯 TOP 3 RISULTATI ESATTI:")
    for res, p in top_risultati:
        print(f"  • {res} ({p*100:.1f}%)")
    
    # --- SEZIONE BETTING EXCHANGE ---
    esiti_exchange = {
        "1": prob_1, "X": prob_x, "2": prob_2,
        "Over 2.5": prob_over, "Under 2.5": prob_under,
        "Goal": prob_gg, "No Goal": prob_ng
    }
    
    miglior_punta = max(esiti_exchange, key=esiti_exchange.get)
    miglior_banca = min(esiti_exchange, key=esiti_exchange.get)

    print("\n" + "=" * 60)
    print(" 🔄 STRATEGIA BETTING EXCHANGE (es. Betfair)")
    print("=" * 60)
    print(f" 🔵 IDEALE DA PUNTARE (BACK): {miglior_punta} ({esiti_exchange[miglior_punta]*100:.1f}%)")
    print("    -> L'evento più probabile in assoluto sul tabellone.")
    
    # Condizione: suggeriamo la bancata solo se l'evento ha meno del 25% di probabilità di verificarsi
    if esiti_exchange[miglior_banca] < 0.25:
        print(f" 🔴 IDEALE DA BANCARE (LAY): {miglior_banca} (Probabilità solo {esiti_exchange[miglior_banca]*100:.1f}%)")
        print("    -> L'evento è altamente improbabile. Ottima occasione per bancarlo se trovi quote basse.")
    else:
        print(f" 🔴 IDEALE DA BANCARE (LAY): Nessun evento netto.")
        print(f"    (L'esito meno probabile è {miglior_banca} al {esiti_exchange[miglior_banca]*100:.1f}%, ma è troppo rischioso da bancare).")
    print("=" * 60)

    # MAPPA MERCATI PER ANALISI QUOTE TRADIZIONALE
    mappa_prob = {
        "1": (prob_1, f"Vittoria {squadra_casa}"),
        "X": (prob_x, "Pareggio (X)"),
        "2": (prob_2, f"Vittoria {squadra_ospite}"),
        "Under": (prob_under, "Under 2.5"),
        "Over": (prob_over, "Over 2.5"),
        "Goal": (prob_gg, "Goal (GG)"),
        "NoGoal": (prob_ng, "No Goal (NG)")
    }

    print("\n[INSERISCI LE QUOTE DEL BOOKMAKER TRADIZIONALE PER TROVARE IL VALORE]")
    print("*(Lascia vuoto e premi INVIO per saltare una quota)*\n")
    
    giocate_analizzate = []
    
    for chiave, (p_dec, nome_esito) in mappa_prob.items():
        quota_str = input(f"Quota per {nome_esito}: ").strip()
        if quota_str:
            try:
                q = float(quota_str)
                ev, kelly = calcola_ev_e_kelly(p_dec, q)
                if ev > 0:
                    giocate_analizzate.append({
                        "esito": nome_esito,
                        "ev": ev,
                        "kelly": kelly,
                        "quota": q,
                        "prob": p_dec * 100
                    })
            except ValueError:
                pass

    print("\n" + "=" * 60)
    print(" 🏆 VERDETTO ALGORITMO: PRONOSTICO CONSIGLIATO (Bookmaker)")
    print("=" * 60)

    if giocate_analizzate:
        giocate_analizzate.sort(key=lambda x: x["ev"], reverse=True)
        top = giocate_analizzate[0]
        
        print(f" 🎯 LA GIOCATA DI VALORE ASSOLUTO: {top['esito']}")
        print(f"  • Quota Bookmaker: {top['quota']:.2f}")
        print(f"  • Probabilità Reale: {top['prob']:.1f}%")
        print(f"  • Expected Value (Vantaggio Matematico): +{top['ev']:.2f}%")
        print(f"  • Gestione Cassa (Stake Consigliato): {top['kelly']:.2f}% del budget")
        
        if len(giocate_analizzate) > 1:
            print("\n Altre giocate con valore matematico positivo:")
            for g in giocate_analizzate[1:4]:
                print(f"  - {g['esito']} a quota {g['quota']:.2f} (EV: +{g['ev']:.2f}%)")
    else:
        print(" ❌ NESSUN VALORE MATEMATICO TROVATO SUI BOOKMAKER.")
        print(" Le quote inserite non offrono un vantaggio matematico sul lungo periodo.")
    print("=" * 60)

if __name__ == "__main__":
    main()