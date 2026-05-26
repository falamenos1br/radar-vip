if st.button("📲 DESPACHAR PARA O TELEGRAM"):
        if not t_token or not t_id:
            st.error("Token ou ID ausentes!")
        else:
            cabecalho = f"🎯 *RADAR VIP - {data_alvo.strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
            mensagens = []
            texto_atual = cabecalho
            
            for idx, j in enumerate(st.session_state.res_pauta, 1):
                b_fav = criar_barra_porcentagem(j['🎯 % Fav'])
                b_dc = criar_barra_porcentagem(j['🛡️ % DC'])
                b_gol = criar_barra_porcentagem(j['📊 % Gol'])
                
                bloco = (
                    f"🔥 *JOGO {idx:02d}*\n"
                    f"⏰ *{j['⏰ Hora']}* | {j['🌍 País/Origem']}\n"
                    f"🏆 {j['🏆 Liga']}\n\n"
                    f"⭐ *PALPITE PRINCIPAL (MERCADO 1X2):*\n"
                    f"👉 Vitória do {j['🛡️ Fav']} ({j['📈 Odd F']:.2f}) | *{j['🎯 % Fav']:.1f}% de Chance*\n"
                    f"`{b_fav}`\n"
                    f"🦓 {j['🦓 Zeb']} ({j['📉 Odd Z']:.2f})\n\n"
                    f"🛡️ *COBERTURA ANTI-ZEBRA (MERCADO DUPLA CHANCE):*\n"
                    f"👉 {j['🛡️ Fav']} ou Empate ({j['🛡️ Odd DC']:.2f}) | *{j['🛡️ % DC']:.1f}% de Segurança*\n"
                    f"`{b_dc}`\n\n"
                    f"⚽ *MERCADO DE GOLS:*\n"
                    f"👉 {j['⚽ Mercado Gol']}: *{j['📊 % Gol']:.1f}% de Chance*\n"
                    f"`{b_gol}`\n\n"
                    f"📐 *MERCADO DE ESCANTEIOS:*\n"
                    f"⏱️ {j['📐 Canto HT']}: *{j['📈 % HT']:.1f}%*\n"
                    f"🏃 {j['📐 Canto FT']}: *{j['📈 % FT']:.1f}%*\n"
                    f"🏦 Via {j['🏦 Casa']}\n"
                    f"───────────────\n\n"
                )
                
                if len(texto_atual + bloco) > 3500:
                    mensagens.append(texto_atual)
                    texto_atual = cabecalho + bloco
                else:
                    texto_atual += bloco
            
            # Fecha a lista corretamente
            mensagens.append(texto_atual)
            
            # --- NOVO: Lógica de envio para a API do Telegram ---
            sucesso = True
            for msg in mensagens:
                url_telegram = f"https://api.telegram.org/bot{t_token}/sendMessage"
                payload = {
                    "chat_id": t_id,
                    "text": msg,
                    "parse_mode": "Markdown"
                }
                try:
                    resp = requests.post(url_telegram, json=payload)
                    if resp.status_code != 200:
                        st.error(f"Falha ao enviar uma parte da mensagem. Erro: {resp.text}")
                        sucesso = False
                except Exception as e:
                    st.error(f"Erro de conexão com o Telegram: {e}")
                    sucesso = False
                    
            if sucesso:
                st.success("✅ Pauta despachada com sucesso para o Telegram!")
