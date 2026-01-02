import streamlit as st
import pandas as pd

# 1. IMPOSTAZIONI PAGINA
st.set_page_config(page_title="PISTINE", page_icon="🂡")
st.title("PISTINAE")

# 2. INIZIALIZZAZIONE MEMORIA
if 'giocatori' not in st.session_state:
    st.session_state['giocatori'] = []
if 'punteggi' not in st.session_state:
    st.session_state['punteggi'] = {}
if 'storico' not in st.session_state:
    st.session_state['storico'] = []
if 'mazziere_corrente' not in st.session_state:
    st.session_state['mazziere_corrente'] = None

# --- BARRA LATERALE: GESTIONE GIOCATORI ---
with st.sidebar:
    st.header("Gestione Tavolo")

    # Aggiunta Giocatori (Corretto nuevo -> nuovo)
    nuovo_giocatore = st.text_input("Nome Giocatore")
    if st.button("Aggiungi al Tavolo"):
        if nuovo_giocatore and nuovo_giocatore not in st.session_state['giocatori']:
            if nuovo_giocatore == "Flavio":
                st.snow()
            st.session_state['giocatori'].append(nuovo_giocatore)
            # Inizializza a 0.0 se non esiste
            if nuovo_giocatore not in st.session_state['punteggi']:
                st.session_state['punteggi'][nuovo_giocatore] = 0.0

            # Se è il primo, diventa mazziere
            if len(st.session_state['giocatori']) == 1:
                st.session_state['mazziere_corrente'] = nuovo_giocatore
            st.rerun()

    st.divider()

    # SELEZIONE DEL MAZZIERE
    if st.session_state['giocatori']:
        st.subheader("Seleziona nuovo mazziere")
        # Gestione sicura dell'indice (se il mazziere cambia o viene rimosso)
        try:
            if st.session_state['mazziere_corrente'] in st.session_state['giocatori']:
                index_mazziere = st.session_state['giocatori'].index(st.session_state['mazziere_corrente'])
            else:
                index_mazziere = 0
        except ValueError:
            index_mazziere = 0

        mazziere = st.selectbox(
            "Seleziona il Mazziere attuale:",
            st.session_state['giocatori'],
            index=index_mazziere
        )

        if mazziere != st.session_state['mazziere_corrente']:
            st.session_state['mazziere_corrente'] = mazziere
            st.rerun()

    st.divider()
    if st.button("🔴 Resetta Partita"):
        st.session_state['punteggi'] = {k: 0.0 for k in st.session_state['giocatori']}
        st.session_state['storico'] = []
        st.rerun()

# --- LOGICA ANNULLA ULTIMA MANO (UNDO) - VERSIONE ROBUSTA ---
if st.session_state['storico']:
    col_undo, _ = st.columns([1, 3])
    with col_undo:
        if st.button("↩️ Annulla Ultima Mano", type="secondary"):
            try:
                # 1. Recuperiamo l'ultima mano senza rimuoverla ancora (peek)
                if not st.session_state['storico']:
                    st.warning("Nessuna mano da annullare.")
                    st.stop()

                # 2. Rimuoviamo l'ultima mano
                ultima_mano = st.session_state['storico'].pop()

                # 3. Sottraiamo i punti (operazione inversa)
                for nome, punti in ultima_mano.items():
                    # Controllo di sicurezza: il giocatore esiste ancora?
                    if nome in st.session_state['punteggi']:
                        st.session_state['punteggi'][nome] -= punti
                    else:
                        # Se il giocatore non c'è più, ricreiamolo o ignoriamo (qui lo ricreiamo per sicurezza)
                        st.session_state['punteggi'][nome] = -punti

                st.success("Ultima mano annullata!")
                st.rerun()

            except Exception as e:
                st.error(f"Errore nell'annullamento: {e}")

# --- AREA PRINCIPALE ---

if len(st.session_state['giocatori']) < 2:
    st.info("Aggiungi giocatori")
else:
    st.markdown(f"### Mazziere attuale: **:red[{st.session_state['mazziere_corrente']}]** 🎩")
    st.write("Inserisci vincite/perdite degli altri.")

    # --- FORM INSERIMENTO (CON RESET AUTOMATICO) ---
    with st.form("form_mano", clear_on_submit=True):
        punti_round = {}
        cols = st.columns(len(st.session_state['giocatori']))

        somma_giocatori = 0.0

        # Iteriamo sui giocatori presenti
        for i, nome in enumerate(st.session_state['giocatori']):
            with cols[i]:
                if nome == st.session_state['mazziere_corrente']:
                    st.text_input(f"{nome} (Banco)", value="?", disabled=True)
                else:
                    val = st.number_input(f"{nome}", step=0.5, value=0.0)
                    punti_round[nome] = val
                    somma_giocatori += val

        conferma = st.form_submit_button("💰 Conferma Mano")

        if conferma:
            # Calcolo mazziere
            punti_mazziere = -somma_giocatori
            # Assicuriamoci che il mazziere sia nel dizionario del round
            punti_round[st.session_state['mazziere_corrente']] = punti_mazziere

            # Salvataggio
            st.session_state['storico'].append(punti_round)
            for nome, p in punti_round.items():
                if nome in st.session_state['punteggi']:
                    st.session_state['punteggi'][nome] += p
                else:
                    st.session_state['punteggi'][nome] = p

            st.rerun()

    # --- CLASSIFICA E STORICO ---
    st.divider()
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Bilancio")
        # Creazione sicura del DataFrame
        if st.session_state['punteggi']:
            df = pd.DataFrame(list(st.session_state['punteggi'].items()), columns=['Giocatore', 'Bilancio'])
            df = df.sort_values(by='Bilancio', ascending=False)
            st.dataframe(df, hide_index=True)

            # Check Somma Zero
            somma = sum(st.session_state['punteggi'].values())
            # Tolleranza floating point
            if abs(somma) > 0.001:
                st.caption(f"⚠️ Check Somma: {somma:.2f}")
        else:
            st.write("Nessun giocatore.")

    with col2:
        st.subheader("Ultimi Round")
        if st.session_state['storico']:
            df_storico = pd.DataFrame(st.session_state['storico'])
            df_storico = df_storico.iloc[::-1]
            st.dataframe(df_storico, use_container_width=True, height=200)

    # --- STATISTICHE ---
    st.divider()
    if st.checkbox("Mostra Statistiche Avanzate"):
        if len(st.session_state['storico']) > 0:
            st.caption("Andamento Bilancio nel Tempo")

            # Ricostruzione sicura dello storico per il grafico
            history_data = []
            current_sums = {name: 0.0 for name in st.session_state['giocatori']}

            history_data.append(current_sums.copy())

            for mano in st.session_state['storico']:
                for nome, punti in mano.items():
                    # Usiamo .get() per evitare crash se un giocatore non esiste più nel dizionario temporaneo
                    current_sums[nome] = current_sums.get(nome, 0.0) + punti
                history_data.append(current_sums.copy())

            df_chart = pd.DataFrame(history_data)
            st.line_chart(df_chart)
        else:
            st.info("Gioca qualche mano per vedere i grafici!")