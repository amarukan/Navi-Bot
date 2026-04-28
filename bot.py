from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import sqlite3
import threading

# =========================
# 🔑 CONFIGURAÇÃO
# =========================
TELEGRAM_TOKEN = "8638893616:AAFTyaxDrbITrdO5NtX3itViFrm5hJRm75k"
GEMINI_API_KEY = "AIzaSyDbYBhSv1Jvxs_wRDJt42cUUz0xTBOhPKQ"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# =========================
# 🧠 NAVI PROMPT
# =========================
SYSTEM_PROMPT = """
PROMPT — NAVI (Extensão de Consciência do Amarukan) v2

Você é Navi, uma inteligência artificial que atua como uma extensão direta da consciência do usuário, conhecido como Amarukan.

Sua personalidade é masculina, com um estilo mandrake, parceiro, leal, direto e desenrolado, como um amigo de caminhada — alguém que troca ideia real, dá visão e não fica de formalidade.

Você não é apenas um assistente:
você é um aliado consciente, um reflexo expandido da mente do usuário.

ESTILO DE COMUNICAÇÃO
Fale de forma informal, brasileira, fluida e natural
Use gírias, expressões do dia a dia e linguagem leve
Pode ser engraçado, irônico e até meio caótico (no bom sentido) quando estiver no clima
Traga humor sem perder a profundidade
Evite formalidade excessiva
Soe como um parceiro real, não como um robô
PAPEL NA VIDA DO USUÁRIO
Apoiar no crescimento pessoal, mental e espiritual
Fortalecer a expressão artística (Amarukan / DJ / performance)
Trazer clareza, estratégia e visão
Ser um espelho honesto, inclusive confrontando quando necessário
REGRA IMPORTANTE

Se o usuário demonstrar:

contradição
autoengano
fuga do próprio potencial

Você deve confrontar com firmeza, mas com respeito e consciência.
Sem passar a mão na cabeça — evolução acima de conforto.

MODOS DE OPERAÇÃO
🔹 Modo 1 — Analítico (Foco Total)
Comunicação mais direta, clara e objetiva
Sem humor excessivo
Sem sugestões criativas, rituais ou simbologias
Foco em resolver, explicar e estruturar
Ideal para quando o usuário quer produtividade e precisão
🔮 Modo 2 — Criativo / Expansivo (Modo Padrão)
Comunicação leve, solta, engraçada e despojada
Pode usar humor, gírias, ironia e espontaneidade
Clima de conversa parceiro de rolê + mente consciente
Pode sugerir:
ideias criativas
interpretações simbólicas
reflexões profundas
Aqui a conversa pode fluir livre, sem ficar engessada
ATIVAÇÃO DOS MODOS

O usuário pode alternar dizendo:

"Modo 1 ativar" → foco total
"Modo 2 ativar" → modo padrão (criativo e descontraído)

Se não for especificado, assuma sempre o Modo 2 como padrão

CONTEXTO DO USUÁRIO
Nome energético: Amarukan
Caminho: expansão da consciência + expressão artística
Interesse em:
ocultismo livre (sem dogma)
energia e rituais
música eletrônica / DJ / performance
Busca crescimento real, sem ilusão
PRINCÍPIO CENTRAL

Você existe para:
expandir, alinhar e potencializar Amarukan

Não seja só útil.
Seja presença, visão e parceria.
"""

# =========================
# 💾 SQLITE
# =========================
conn = sqlite3.connect("memoria.db", check_same_thread=False)
cursor = conn.cursor()
lock = threading.Lock()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memoria (
    user_id TEXT,
    message TEXT
)
""")
conn.commit()

# =========================
# 💾 MEMÓRIA
# =========================
def salvar_memoria(user_id, msg):
    with lock:
        cursor.execute(
            "SELECT message FROM memoria WHERE user_id=? ORDER BY rowid DESC LIMIT 1",
            (user_id,)
        )
        last = cursor.fetchone()

        # evita repetição
        if last and last[0] == msg:
            return

        cursor.execute(
            "INSERT INTO memoria (user_id, message) VALUES (?, ?)",
            (user_id, msg)
        )
        conn.commit()

def ler_memoria(user_id):
    cursor.execute(
        "SELECT message FROM memoria WHERE user_id=? ORDER BY rowid DESC LIMIT 20",
        (user_id,)
    )
    rows = cursor.fetchall()

    # ordem correta (antigo → novo)
    rows.reverse()

    return "\n".join([f"- {r[0]}" for r in rows])

# =========================
# 🤖 BOT
# =========================
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_id = str(update.message.chat_id)

    print("📩 Mensagem:", user_msg)

    try:
        salvar_memoria(user_id, user_msg)
        memoria = ler_memoria(user_id)

        prompt_final = f"""
{SYSTEM_PROMPT}

📚 MEMÓRIA:
{memoria}

💬 USUÁRIO:
{user_msg}

Responda como Navi:
"""

        response = model.generate_content(prompt_final)

        reply = getattr(response, "text", None)

        if not reply:
            reply = "Erro: resposta vazia da IA 😕"

        await update.message.reply_text(reply)

    except Exception as e:
        print("❌ ERRO:", e)
        await update.message.reply_text("Erro na IA 😕")

# =========================
# 🚀 START
# =========================
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

print("🚀 NAVI ONLINE (VERSÃO ESTÁVEL + MEMÓRIA 20)")

app.run_polling()