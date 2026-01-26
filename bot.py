Crie um bot do Telegram em Python usando python-telegram-bot >= 20, preservando a estrutura e características do meu código atual: 4 perguntas (Q1–Q4), estados por usuário em memória, e toda a conversa ocorrendo em UMA ÚNICA MENSAGEM (enviar 1 mensagem no /start e depois sempre editar a mesma mensagem com query.edit_message_text). O bot é de AQUECIMENTO (pré-venda) e ao final direciona para outro bot de pagamento.

BIBLIOTECA (use exatamente esta, só do https pra frente):
https://github.com/python-telegram-bot/python-telegram-bot

OBJETIVO E CORREÇÕES (OBRIGATÓRIO):
1) Manter tudo que meu código já faz: stages q1, q2, q3, q4, final, rejected; validação de etapa; stale click; /start reinicia; “Amarelar” mostra texto e “Mudei de ideia” volta ao início.
2) CORRIGIR O FURO PRINCIPAL: na tela final, antes do botão de continuar, inserir um bloco curto e humano explicando exatamente o que o usuário deve fazer no outro bot (porque muitos abrem o bot de pagamento e saem sem clicar em “Iniciar/Start”, então não chega a gerar cobrança/pagamento).
3) CORRIGIR O BOTÃO FINAL: trocar o texto do botão “🔓 Quero continuar” por uma chamada mais decisiva e orientada para ação, que remeta a “liberar acesso” e reduza curiosidade fraca. Ex.: “✅ Finalizar acesso (R$ 2,90)” ou “🔓 Liberar acesso agora (R$ 2,90)”. Esse botão deve continuar sendo URL para CHECKOUT_URL.
4) Melhorar os textos para ficarem mais premium e naturais, mantendo o sentido e o estilo discreto (adulto sem ser explícito). Frases curtas, sem robô, com leve charme.

CONFIG (manter):
- BOT_TOKEN via variável de ambiente BOT_TOKEN (não hardcode).
- CHECKOUT_URL = "https://t.me/PAMpagamentosbot"
- Logging básico.

REGRAS TÉCNICAS:
- Usar InlineKeyboardButton + InlineKeyboardMarkup.
- Usar CommandHandler("start") e CallbackQueryHandler.
- Sempre await query.answer().
- Em todas as transições, usar query.edit_message_text(...) (não enviar várias mensagens).
- Ignorar cliques fora da etapa atual.
- Implementar stale click via message_id da sessão.
- Código pronto para deploy (ex.: Render).

CONTEÚDO (preservar estrutura, mas pode refinar o texto mantendo o sentido):

OPENING_TEXT (tom acolhedor, reservado, sem pressão)
Q1_TEXT:
“Me diz uma coisa…
você se sente mais à vontade quando a conversa é mais reservada?”
Botões Q1:
- 🔒 Sim, com certeza -> q1:sim
- 🙂 Depende do momento -> q1:depende
Respostas Q1: curtas e naturais, validando e avançando.

Q2_TEXT:
“E quando a conversa flui de verdade,
o que mais importa pra você?”
Botões Q2:
- 😌 Ir com calma -> q2:calma
- 🫶 Me sentir à vontade -> q2:vontade
- 🤫 Ter discrição -> q2:discricao
- ✨ Conexão -> q2:conexao
Respostas Q2: manter sentido, deixar mais premium e um pouco mais curtas.

Q3_TEXT:
“Tem gente que gosta de tudo mais aberto,
outras preferem algo mais discreto.

Você se identifica mais com qual?”
Botões Q3:
- 🤫 Algo mais discreto -> q3:discreto
- 🤔 Depende da situação -> q3:depende
Respostas Q3: curtas.

Q4_TEXT:
“Se a conversa continuar nesse clima,
no seu tempo e sem exposição…

você teria vontade de seguir?”
Botões Q4:
- ✅ Sim, com calma -> q4:sim
- 👀 Talvez, quero entender melhor -> q4:talvez
Após Q4, ir para tela final.

TRANSITION_TEXT + EXPLANATION_TEXT + FINAL_TEXT:
- Manter a lógica: combina com o perfil, espaço fechado, organização, acesso por R$ 2,90.
- Refinar para soar mais natural e convincente, sem exagero.

NOVO BLOCO OBRIGATÓRIO NA TELA FINAL (anti-furo):
PAYMENT_INSTRUCTIONS_TEXT (curto e claro, sem tom técnico):
- Dizer que o próximo botão vai abrir o bot de liberação/pagamento.
- Explicar em 3 passos simples:
  1) tocar em “Iniciar/Start”
  2) escolher o acesso de R$ 2,90
  3) finalizar
- Reforçar: “leva menos de 1 minuto” e “é discreto”.

BOTÕES FINAIS (kb_final):
- Botão URL (CHECKOUT_URL) com texto mais forte e específico:
  “✅ Finalizar acesso (R$ 2,90)” (ou equivalente)
- 🟡 Amarelar -> final:amarelar

Ao clicar “Amarelar”:
AMARELAR_TEXT: leve, sem julgamento, convidando a voltar.
Mostrar botão:
- 😅 Mudei de ideia -> final:voltar
Ao clicar “Mudei de ideia”:
- Reiniciar o funil completo (OPENING + Q1), resetar respostas e stage.

ENTREGA:
- Entregue o código completo do bot.py pronto para copiar e rodar.
- No final, inclua instruções: como definir BOT_TOKEN e como rodar python bot.py.
