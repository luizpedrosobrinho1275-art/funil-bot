# bot.py
# Bot Telegram com funil AIDA (estrutura conceitual) + 2 perguntas reais
# Compatível com Python 3.10.11 + python-telegram-bot >= 20
# CORREÇÕES:
# - Sem exibir "Pergunta 1" e "Pergunta 2" no texto
# - Botão "Voltar" do amarelar reinicia o funil completo (como novo /start)

import os
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
CHECKOUT_URL = "https://t.me/PAMpagamentosbot"
BOT_TOKEN_ENV = os.getenv("BOT_TOKEN")

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ================= ESTADOS =================
STAGE_Q1 = "q1"
STAGE_Q2 = "q2"
STAGE_FINAL = "final"
STAGE_REJECTED = "rejected"


@dataclass
class UserSession:
    stage: str
    message_id: Optional[int] = None


SESSIONS: Dict[int, UserSession] = {}

# ================= TEXTOS =================

# A — ATENÇÃO (apenas texto introdutório, NÃO é pergunta)
ATTENTION_TEXT = (
    "👀 Leia com atenção.\n\n"
    "Responda às próximas perguntas e concorra a uma seleção reservada.\n\n"
    "Apenas 10 homens diferentes vão avançar.\n\n"
    "A curiosidade trouxe você até aqui.\n"
    "Vamos ver o que faz você ficar. 🔥\n\n"
)

# PERGUNTA 1 (SEM exibir "Pergunta 1:" no texto)
Q1_QUESTION = (
    "O que mais te prende quando percebe que alguém é diferente da maioria?\n"
)

Q1_RESPONSE = {
    "autenticidade": (
        "Interessante.\n"
        "Pouca gente sabe reconhecer quando algo é verdadeiro sem esforço.\n"
        "Isso já diz bastante sobre você.\n\n"
    ),
    "personalidade": (
        "Personalidade chama atenção antes mesmo das palavras.\n"
        "Quem percebe isso costuma enxergar além do óbvio.\n\n"
    ),
    "conexao": (
        "Nem todo mundo valoriza conexão de verdade.\n"
        "Quando valoriza, geralmente é porque já sentiu falta disso antes.\n\n"
    ),
}

# PERGUNTA 2 (SEM exibir "Pergunta 2:" no texto)
Q2_QUESTION = (
    "E quando algo não é aberto ao público,\n"
    "mas reservado para poucos…\n"
    "isso te atrai?\n"
)

Q2_RESPONSE = {
    "sim": (
        "Faz sentido.\n"
        "Quem se sente atraído por isso geralmente não gosta do que é comum.\n"
        "Vamos ver até onde você vai.\n\n"
    ),
    "depende": (
        "Justo.\n"
        "Nem tudo vale a pena só por ser exclusivo.\n"
        "A diferença está no porquê — e você vai entender isso já.\n\n"
    ),
}

# A — AÇÃO (estrutura conceitual, tela final)
FINAL_TEXT = (
    "🏆 Parabéns.\n\n"
    "Entre muitos perfis, o seu foi escolhido.\n\n"
    "Você acaba de garantir acesso a uma proposta reservada,\n"
    "liberada apenas para 10 homens selecionados.\n\n"
    "🎁 Como parte dessa escolha,\n"
    "vou liberar para você o acesso ao meu canal privado no Telegram\n"
    "com 86% de desconto.\n\n"
    "Isso não é público.\n"
    "Não se repete.\n"
    "É o resultado da sua seleção. ✨\n"
)

# Texto de "quebra de ego" (rejected)
AMARELAR_TEXT = (
    "Tudo bem.\n\n"
    "Nem todo mundo se sente confortável quando percebe que foi realmente escolhido.\n\n"
    "Se mudar de ideia, talvez ainda dê tempo. 😉\n"
)

# ================= KEYBOARDS =================
def kb_q1():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👀 Autenticidade", callback_data="q1:autenticidade")],
        [InlineKeyboardButton("🧠 Personalidade", callback_data="q1:personalidade")],
        [InlineKeyboardButton("😌 Conexão real", callback_data="q1:conexao")],
    ])


def kb_q2():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("😏 Sim", callback_data="q2:sim"),
        InlineKeyboardButton("🤔 Depende", callback_data="q2:depende"),
    ]])


def kb_final():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 Resgatar agora", url=CHECKOUT_URL)],
        [InlineKeyboardButton("🟡 Amarelar", callback_data="final:amarelar")],
    ])


def kb_voltar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Voltar", callback_data="final:voltar")]
    ])


# ================= HELPERS =================
def is_stale_click(session: UserSession, update: Update) -> bool:
    q = update.callback_query
    if not q or not q.message:
        return True
    return session.message_id != q.message.message_id


def expected_stage(cb: str) -> str:
    if ":" not in cb:
        return "unknown"
    p = cb.split(":", 1)[0]
    return {
        "q1": STAGE_Q1,
        "q2": STAGE_Q2,
        "final": STAGE_FINAL
    }.get(p, "unknown")


def get_initial_text_and_keyboard():
    """Retorna texto e teclado da tela inicial (Atenção + Q1)"""
    text = ATTENTION_TEXT + Q1_QUESTION
    keyboard = kb_q1()
    return text, keyboard


# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    session = UserSession(stage=STAGE_Q1)
    SESSIONS[user.id] = session

    text, reply_markup = get_initial_text_and_keyboard()

    msg = await context.bot.send_message(chat.id, text, reply_markup=reply_markup)
    session.message_id = msg.message_id
    logger.info(f"START user_id={user.id}")


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    session = SESSIONS.get(user.id)
    if not session:
        logger.info(f"NO_SESSION user_id={user.id}")
        return

    if is_stale_click(session, update):
        logger.info(f"STALE_CLICK user_id={user.id}")
        return

    data = query.data
    stage_required = expected_stage(data)

    # Exceção: "final:voltar" pode vir de STAGE_REJECTED
    if data == "final:voltar" and session.stage == STAGE_REJECTED:
        # REINICIAR O FUNIL COMPLETO (como novo /start)
        session.stage = STAGE_Q1
        text, reply_markup = get_initial_text_and_keyboard()
        await query.edit_message_text(text, reply_markup=reply_markup)
        logger.info(f"RESTART_FUNNEL user_id={user.id}")
        return

    if stage_required != session.stage:
        logger.info(f"OUT_OF_STAGE user_id={user.id} current={session.stage} expected={stage_required}")
        return

    prefix, choice = data.split(":", 1)

    # ===== PERGUNTA 1 =====
    if session.stage == STAGE_Q1 and prefix == "q1":
        if choice not in Q1_RESPONSE:
            return

        text = Q1_RESPONSE[choice] + Q2_QUESTION
        session.stage = STAGE_Q2
        await query.edit_message_text(text, reply_markup=kb_q2())
        logger.info(f"Q1 user_id={user.id} choice={choice}")
        return

    # ===== PERGUNTA 2 =====
    if session.stage == STAGE_Q2 and prefix == "q2":
        if choice not in Q2_RESPONSE:
            return

        text = Q2_RESPONSE[choice] + FINAL_TEXT
        session.stage = STAGE_FINAL
        await query.edit_message_text(text, reply_markup=kb_final())
        logger.info(f"Q2 user_id={user.id} choice={choice}")
        return

    # ===== TELA FINAL =====
    if session.stage == STAGE_FINAL and prefix == "final":
        if choice == "amarelar":
            session.stage = STAGE_REJECTED
            await query.edit_message_text(AMARELAR_TEXT, reply_markup=kb_voltar())
            logger.info(f"AMARELAR user_id={user.id}")
        return


# ================= MAIN =================
def main():
    token = os.getenv(BOT_TOKEN_ENV)
    if not token:
        raise RuntimeError(f"Defina a variável de ambiente {BOT_TOKEN_ENV}")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))

    logger.info("Bot iniciado. Polling...")
    app.run_polling()


if __name__ == "__main__":
    main()

