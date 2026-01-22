import os
import logging
from dataclasses import dataclass
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ============================================
# CONFIGURAÇÃO
# ============================================
BOT_TOKEN_ENV = "BOT_TOKEN"
CHECKOUT_URL = "https://t.me/SEU_BOT_DE_CHECKOUT"  # TROQUE AQUI

# ============================================
# LOGGING
# ============================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# ESTÁGIOS
# ============================================
STAGE_Q1 = "q1"
STAGE_Q2 = "q2"
STAGE_Q3 = "q3"
STAGE_Q4 = "q4"
STAGE_FINAL = "final"
STAGE_REJECTED = "rejected"

# ============================================
# SESSÕES EM MEMÓRIA
# ============================================
@dataclass
class UserSession:
    stage: str
    message_id: int
    q1_answer: Optional[str] = None
    q2_answer: Optional[str] = None
    q3_answer: Optional[str] = None
    q4_answer: Optional[str] = None

SESSIONS: dict[int, UserSession] = {}

# ============================================
# TEXTOS
# ============================================
OPENING_TEXT = (
    "Que bom que você chegou.\n\n"
    "Aqui tudo acontece com calma,\n"
    "sem pressão e sem exposição.\n\n"
    "Só quero entender se isso faz sentido pra você.\n\n"
)

Q1_TEXT = (
    "Me diz uma coisa…\n"
    "você se sente mais à vontade quando a conversa é mais reservada?\n"
)

Q1_RESPONSE = {
    "sim": "Entendi.\nIsso é mais comum do que parece.\n\n",
    "depende": "Justo.\nTudo tem seu momento.\n\n"
}

Q2_TEXT = (
    "E quando a conversa flui de verdade,\n"
    "o que mais importa pra você?\n"
)

Q2_RESPONSE = {
    "calma": "Ir com calma é essencial.\nSem pressa, tudo faz mais sentido.\n\n",
    "vontade": "Se sentir à vontade muda tudo.\nÉ sobre estar confortável.\n\n",
    "discricao": "Discrição é fundamental.\nNem tudo precisa ser exposto.\n\n",
    "conexao": "Conexão de verdade é rara.\nQuando acontece, você sente.\n\n"
}

Q3_TEXT = (
    "Tem gente que gosta de tudo mais aberto,\n"
    "outras preferem algo mais discreto.\n\n"
    "Você se identifica mais com qual?\n"
)

Q3_RESPONSE = {
    "discreto": "Entendo perfeitamente.\nAlgo mais reservado tem seu valor.\n\n",
    "depende": "Faz sentido.\nCada momento pede uma coisa diferente.\n\n"
}

Q4_TEXT = (
    "Se a conversa continuar nesse clima,\n"
    "no seu tempo e sem exposição…\n\n"
    "você teria vontade de seguir?\n"
)

TRANSITION_TEXT = (
    "Ótimo.\n\n"
    "Pelo que você respondeu,\n"
    "isso combina bastante com o que acontece aqui.\n\n"
    "Então deixa eu te explicar como funciona,\n"
    "bem direto e sem enrolação.\n\n"
)

EXPLANATION_TEXT = (
    "Esse espaço é fechado justamente\n"
    "pra manter o clima, a discrição\n"
    "e evitar bagunça.\n\n"
    "Por isso, quem decide continuar\n"
    "entra por um acesso simples,\n"
    "só pra manter tudo organizado.\n\n"
    "Hoje esse acesso custa R$ 2,90.\n"
    "É só pra liberar a continuidade\n"
    "e manter tudo funcionando do jeito certo.\n\n"
)

FINAL_TEXT = (
    "Se fizer sentido pra você,\n"
    "você pode continuar agora.\n"
)

AMARELAR_TEXT = (
    "Tudo bem.\n\n"
    "Sem pressa.\n"
    "Se mudar de ideia, é só voltar e continuar no seu tempo.\n"
)

OUT_OF_STAGE = "⚠️ Essa opção não está mais disponível. Use /start para recomeçar."

# ============================================
# TECLADOS
# ============================================
def kb_q1() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔒 Sim, com certeza", callback_data="q1:sim")],
        [InlineKeyboardButton("🙂 Depende do momento", callback_data="q1:depende")]
    ])

def kb_q2() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("😌 Ir com calma", callback_data="q2:calma")],
        [InlineKeyboardButton("🫶 Me sentir à vontade", callback_data="q2:vontade")],
        [InlineKeyboardButton("🤫 Ter discrição", callback_data="q2:discricao")],
        [InlineKeyboardButton("✨ Conexão", callback_data="q2:conexao")]
    ])

def kb_q3() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤫 Algo mais discreto", callback_data="q3:discreto")],
        [InlineKeyboardButton("🤔 Depende da situação", callback_data="q3:depende")]
    ])

def kb_q4() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sim, com calma", callback_data="q4:sim")],
        [InlineKeyboardButton("👀 Talvez, quero entender melhor", callback_data="q4:talvez")]
    ])

def kb_final() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Quero continuar", url=CHECKOUT_URL)],
        [InlineKeyboardButton("🟡 Amarelar", callback_data="final:amarelar")]
    ])

def kb_voltar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Voltar", callback_data="final:voltar")]
    ])

# ============================================
# HELPERS
# ============================================
def expected_stage(callback_data: str) -> str:
    """Retorna o estágio esperado baseado no callback_data"""
    if callback_data.startswith("q1:"):
        return STAGE_Q1
    elif callback_data.startswith("q2:"):
        return STAGE_Q2
    elif callback_data.startswith("q3:"):
        return STAGE_Q3
    elif callback_data.startswith("q4:"):
        return STAGE_Q4
    elif callback_data.startswith("final:"):
        return STAGE_FINAL
    return ""

def is_stale_click(user_id: int, message_id: int) -> bool:
    """Verifica se o clique é de uma mensagem antiga"""
    session = SESSIONS.get(user_id)
    if not session:
        return True
    return session.message_id != message_id

# ============================================
# COMANDO /start
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia o funil"""
    user = update.effective_user
    user_id = user.id
    
    logger.info(f"User {user_id} ({user.username}) iniciou o bot")
    
    # Envia a primeira mensagem
    text = OPENING_TEXT + Q1_TEXT
    message = await update.message.reply_text(
        text=text,
        reply_markup=kb_q1()
    )
    
    # Cria/atualiza sessão
    SESSIONS[user_id] = UserSession(
        stage=STAGE_Q1,
        message_id=message.message_id
    )

# ============================================
# HANDLER DE CALLBACKS
# ============================================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa todos os callbacks de botões"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    callback_data = query.data
    message_id = query.message.message_id
    
    logger.info(f"User {user_id} clicou em: {callback_data}")
    
    # Verifica se é clique antigo (stale)
    if is_stale_click(user_id, message_id):
        logger.warning(f"Stale click detectado para user {user_id}")
        await query.answer("⚠️ Use /start para recomeçar", show_alert=True)
        return
    
    session = SESSIONS.get(user_id)
    if not session:
        await query.edit_message_text(OUT_OF_STAGE)
        return
    
    # Valida estágio
    expected = expected_stage(callback_data)
    if session.stage != expected:
        logger.warning(f"User {user_id} em stage {session.stage}, esperado {expected}")
        await query.answer("⚠️ Opção fora de ordem. Use /start", show_alert=True)
        return
    
    # Roteamento por estágio
    if callback_data.startswith("q1:"):
        await handle_q1(query, session, callback_data)
    elif callback_data.startswith("q2:"):
        await handle_q2(query, session, callback_data)
    elif callback_data.startswith("q3:"):
        await handle_q3(query, session, callback_data)
    elif callback_data.startswith("q4:"):
        await handle_q4(query, session, callback_data)
    elif callback_data.startswith("final:"):
        await handle_final(query, session, callback_data)

# ============================================
# HANDLERS POR ESTÁGIO
# ============================================
async def handle_q1(query, session: UserSession, callback_data: str) -> None:
    """Processa resposta da Q1 e mostra Q2"""
    answer = callback_data.split(":")[1]
    session.q1_answer = answer
    
    response = Q1_RESPONSE.get(answer, "")
    text = response + Q2_TEXT
    
    await query.edit_message_text(
        text=text,
        reply_markup=kb_q2()
    )
    
    session.stage = STAGE_Q2

async def handle_q2(query, session: UserSession, callback_data: str) -> None:
    """Processa resposta da Q2 e mostra Q3"""
    answer = callback_data.split(":")[1]
    session.q2_answer = answer
    
    response = Q2_RESPONSE.get(answer, "")
    text = response + Q3_TEXT
    
    await query.edit_message_text(
        text=text,
        reply_markup=kb_q3()
    )
    
    session.stage = STAGE_Q3

async def handle_q3(query, session: UserSession, callback_data: str) -> None:
    """Processa resposta da Q3 e mostra Q4"""
    answer = callback_data.split(":")[1]
    session.q3_answer = answer
    
    response = Q3_RESPONSE.get(answer, "")
    text = response + Q4_TEXT
    
    await query.edit_message_text(
        text=text,
        reply_markup=kb_q4()
    )
    
    session.stage = STAGE_Q4

async def handle_q4(query, session: UserSession, callback_data: str) -> None:
    """Processa resposta da Q4 e mostra tela final"""
    answer = callback_data.split(":")[1]
    session.q4_answer = answer
    
    text = TRANSITION_TEXT + EXPLANATION_TEXT + FINAL_TEXT
    
    await query.edit_message_text(
        text=text,
        reply_markup=kb_final()
    )
    
    session.stage = STAGE_FINAL

async def handle_final(query, session: UserSession, callback_data: str) -> None:
    """Processa ações da tela final"""
    action = callback_data.split(":")[1]
    
    if action == "amarelar":
        await query.edit_message_text(
            text=AMARELAR_TEXT,
            reply_markup=kb_voltar()
        )
        session.stage = STAGE_REJECTED
        logger.info(f"User {query.from_user.id} amarelou")
    
    elif action == "voltar":
        # Reinicia o funil inteiro
        text = OPENING_TEXT + Q1_TEXT
        await query.edit_message_text(
            text=text,
            reply_markup=kb_q1()
        )
        # Reseta a sessão
        session.stage = STAGE_Q1
        session.q1_answer = None
        session.q2_answer = None
        session.q3_answer = None
        session.q4_answer = None
        logger.info(f"User {query.from_user.id} voltou ao início")

# ============================================
# MAIN
# ============================================
def main() -> None:
    """Inicia o bot"""
    token = os.getenv(BOT_TOKEN_ENV)
    if not token:
        logger.error(f"Token não encontrado. Configure a variável {BOT_TOKEN_ENV}")
        return
    
    # Cria aplicação
    application = Application.builder().token(token).build()
    
    # Registra handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Inicia o bot
    logger.info("Bot iniciado com sucesso!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
