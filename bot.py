# bot.py
# Bot Telegram de aquecimento (pré-venda) com 4 perguntas + direcionamento para bot de pagamento
# Compatível com Python 3.10.11 + python-telegram-bot >= 20
# Biblioteca: https://github.com/python-telegram-bot/python-telegram-bot
#
# CARACTERÍSTICAS:
# - 4 perguntas (Q1-Q4) com respostas personalizadas
# - UMA ÚNICA MENSAGEM no chat (sempre edit_message_text)
# - Estados por usuário em memória (q1, q2, q3, q4, final, rejected)
# - Validação de etapa + stale click
# - Instruções claras antes do botão de pagamento (anti-furo)
# - Botão final com CTA forte e preço visível
# - "Amarelar" -> "Mudei de ideia" reinicia o funil

import os
import logging
from dataclasses import dataclass
from typing import Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
CHECKOUT_URL = "https://t.me/PAMpagamentosbot"
BOT_TOKEN_ENV = "BOT_TOKEN"

# ================= LOGGING =================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ================= ESTADOS =================
STAGE_Q1 = "q1"
STAGE_Q2 = "q2"
STAGE_Q3 = "q3"
STAGE_Q4 = "q4"
STAGE_FINAL = "final"
STAGE_REJECTED = "rejected"


@dataclass
class UserSession:
    stage: str
    message_id: Optional[int] = None


SESSIONS: Dict[int, UserSession] = {}

# ================= TEXTOS =================

# Abertura (acolhedor, reservado, sem pressão)
OPENING_TEXT = (
    "Oi.\n\n"
    "Esse espaço é diferente.\n"
    "Aqui a gente conversa com mais liberdade, no seu ritmo e sem nenhuma exposição.\n\n"
    "Antes de continuar, vou te fazer algumas perguntas rápidas.\n"
    "Nada complicado, só para entender se o que eu ofereço faz sentido para você.\n\n"
)

# ===== PERGUNTA 1 =====
Q1_TEXT = (
    "Me diz uma coisa…\n"
    "você se sente mais à vontade quando a conversa é mais reservada?\n"
)

Q1_RESPONSE = {
    "sim": (
        "Entendo perfeitamente. O que é reservado sempre tem mais valor.\n\n"
    ),
    "depende": (
        "Justo. Cada momento pede um nível de entrega diferente.\n\n"
    ),
}

# ===== PERGUNTA 2 =====
Q2_TEXT = (
    "E quando a conversa flui de verdade,\n"
    "o que mais importa pra você?\n"
)

Q2_RESPONSE = {
    "calma": (
        "Saber aproveitar cada etapa é o que torna tudo real.\n\n"
    ),
    "vontade": (
        "Quando a gente se sente à vontade, tudo flui naturalmente.\n\n"
    ),
    "discricao": (
        "Respeito e sigilo são a base de qualquer conversa aqui.\n\n"
    ),
    "conexao": (
        "Sem sintonia, nada faz sentido. Que bom que pensa assim.\n\n"
    ),
}

# ===== PERGUNTA 3 =====
Q3_TEXT = (
    "Tem gente que gosta de tudo mais aberto,\n"
    "outras preferem algo mais discreto.\n\n"
    "Você se identifica mais com qual?\n"
)

Q3_RESPONSE = {
    "discreto": (
        "O discreto é mais elegante e muito mais seguro.\n\n"
    ),
    "depende": (
        "Entendo. A flexibilidade ajuda a deixar o clima mais leve.\n\n"
    ),
}

# ===== PERGUNTA 4 =====
Q4_TEXT = (
    "Se a conversa continuar nesse clima,\n"
    "no seu tempo e sem exposição…\n\n"
    "você teria vontade de seguir?\n"
)

Q4_RESPONSE = {
    "sim": (
        "Ótimo. Fico feliz com a sua transparência.\n\n"
    ),
    "talvez": (
        "Sem problemas. Vou te explicar exatamente como funciona agora.\n\n"
    ),
}

# ===== TELA FINAL =====
TRANSITION_TEXT = (
    "Pelo que você me respondeu, seu perfil combina muito com o que eu prezo aqui.\n\n"
)

EXPLANATION_TEXT = (
    "Este é um espaço fechado e organizado. Cobro um acesso simbólico de R$ 2,90 apenas para manter a discrição do grupo e garantir que apenas homens realmente interessados e educados façam parte.\n\n"
)

# NOVO BLOCO: Instruções claras (anti-furo)
PAYMENT_INSTRUCTIONS_TEXT = (
    "📲 Como finalizar seu acesso:\n\n"
    "1. Toque no botão abaixo para abrir o bot de liberação.\n"
    "2. Assim que ele abrir, toque em \"Iniciar\" (ou Start).\n"
    "3. Selecione a opção de acesso de R$ 2,90 e finalize.\n\n"
    "Leva menos de 1 minuto, é totalmente discreto e o acesso é liberado na hora.\n\n"
)

FINAL_TEXT = (
    "Se estiver pronto, te espero do outro lado.\n"
)

# Texto de "quebra de ego" (rejected)
AMARELAR_TEXT = (
    "Tudo bem.\n\n"
    "Nem todo mundo se sente pronto para algo mais exclusivo logo de cara.\n"
    "Se mudar de ideia e quiser ver o que te espera, a porta continua aberta. 😉\n"
)

# ================= KEYBOARDS =================
def kb_opening():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👉 Continuar", callback_data="opening:continuar")],
    ])


def kb_q1():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔒 Sim, com certeza", callback_data="q1:sim")],
        [InlineKeyboardButton("🙂 Depende do momento", callback_data="q1:depende")],
    ])


def kb_q2():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😌 Ir com calma", callback_data="q2:calma")],
        [InlineKeyboardButton("🫶 Me sentir à vontade", callback_data="q2:vontade")],
        [InlineKeyboardButton("🤫 Ter discrição", callback_data="q2:discricao")],
        [InlineKeyboardButton("✨ Conexão", callback_data="q2:conexao")],
    ])


def kb_q3():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤫 Algo mais discreto", callback_data="q3:discreto")],
        [InlineKeyboardButton("🤔 Depende da situação", callback_data="q3:depende")],
    ])


def kb_q4():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim, com calma", callback_data="q4:sim")],
        [InlineKeyboardButton("👀 Talvez, quero entender melhor", callback_data="q4:talvez")],
    ])


def kb_final():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Finalizar acesso (R$ 2,90)", url=CHECKOUT_URL)],
        [InlineKeyboardButton("🟡 Amarelar", callback_data="final:amarelar")],
    ])


def kb_voltar():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😅 Mudei de ideia", callback_data="final:voltar")]
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
        "opening": STAGE_Q1,
        "q1": STAGE_Q1,
        "q2": STAGE_Q2,
        "q3": STAGE_Q3,
        "q4": STAGE_Q4,
        "final": STAGE_FINAL
    }.get(p, "unknown")


def get_initial_text_and_keyboard():
    """Retorna texto e teclado da tela inicial (Opening)"""
    text = OPENING_TEXT
    keyboard = kb_opening()
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

    # ===== TELA ABERTURA =====
    if session.stage == STAGE_Q1 and prefix == "opening":
        if choice == "continuar":
            text = Q1_TEXT
            await query.edit_message_text(text, reply_markup=kb_q1())
            logger.info(f"OPENING user_id={user.id}")
            return

    # ===== PERGUNTA 1 =====
    if session.stage == STAGE_Q1 and prefix == "q1":
        if choice not in Q1_RESPONSE:
            return

        text = Q1_RESPONSE[choice] + Q2_TEXT
        session.stage = STAGE_Q2
        await query.edit_message_text(text, reply_markup=kb_q2())
        logger.info(f"Q1 user_id={user.id} choice={choice}")
        return

    # ===== PERGUNTA 2 =====
    if session.stage == STAGE_Q2 and prefix == "q2":
        if choice not in Q2_RESPONSE:
            return

        text = Q2_RESPONSE[choice] + Q3_TEXT
        session.stage = STAGE_Q3
        await query.edit_message_text(text, reply_markup=kb_q3())
        logger.info(f"Q2 user_id={user.id} choice={choice}")
        return

    # ===== PERGUNTA 3 =====
    if session.stage == STAGE_Q3 and prefix == "q3":
        if choice not in Q3_RESPONSE:
            return

        text = Q3_RESPONSE[choice] + Q4_TEXT
        session.stage = STAGE_Q4
        await query.edit_message_text(text, reply_markup=kb_q4())
        logger.info(f"Q3 user_id={user.id} choice={choice}")
        return

    # ===== PERGUNTA 4 =====
    if session.stage == STAGE_Q4 and prefix == "q4":
        if choice not in Q4_RESPONSE:
            return

        # Montar tela final completa com instruções de pagamento
        text = (
            Q4_RESPONSE[choice] +
            TRANSITION_TEXT +
            EXPLANATION_TEXT +
            PAYMENT_INSTRUCTIONS_TEXT +
            FINAL_TEXT
        )
        session.stage = STAGE_FINAL
        await query.edit_message_text(text, reply_markup=kb_final())
        logger.info(f"Q4 user_id={user.id} choice={choice}")
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
