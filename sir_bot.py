import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ── CONFIG ──────────────────────────────────────────────
TOKEN = "8953248482:AAF38jKrgaFxRPpekvHjEWOW6ffiXtJAfYs"
DATA_FILE = "reportes.json"

logging.basicConfig(level=logging.INFO)

# ── ESTADOS DEL FLUJO ────────────────────────────────────
TIPO, NOMBRE, TELEFONO, DIRECCION, DESCRIPCION = range(5)

TIPOS = [
    ["📡 Sin servicio", "🐢 Lentitud"],
    ["🛠️ Instalación", "📦 Traslado"],
    ["🔧 Corte programado", "💬 Otro"]
]

# ── UTILIDADES ───────────────────────────────────────────
def cargar_reportes():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_reportes(reportes):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reportes, f, ensure_ascii=False, indent=2)

def formato_reporte(r):
    estado_emoji = {"Pendiente": "🟡", "En proceso": "🔵", "Resuelto": "🟢"}.get(r["estado"], "⚪")
    return (
        f"{estado_emoji} *Reporte #{r['id']}*\n"
        f"👤 {r['nombre']}\n"
        f"📞 {r['telefono']}\n"
        f"📍 {r['direccion']}\n"
        f"🔧 {r['tipo']}\n"
        f"📝 {r['descripcion']}\n"
        f"📅 {r['fecha']}\n"
        f"Estado: *{r['estado']}*"
    )

# ── COMANDO /start ───────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al bot de *SIR Telecomunicaciones*\n\n"
        "Comandos disponibles:\n"
        "📋 /nuevo — Registrar reporte\n"
        "📄 /lista — Ver todos los reportes\n"
        "🟡 /pendientes — Ver pendientes\n"
        "🔵 /enproceso — Ver en proceso\n"
        "🟢 /resueltos — Ver resueltos\n"
        "✅ /resolver <id> — Marcar como resuelto\n"
        "🔵 /proceso <id> — Marcar en proceso\n"
        "🗑️ /eliminar <id> — Eliminar reporte",
        parse_mode="Markdown"
    )

# ── FLUJO NUEVO REPORTE ──────────────────────────────────
async def nuevo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Nuevo reporte*\n\n¿Cuál es el tipo de solicitud?",
        reply_markup=ReplyKeyboardMarkup(TIPOS, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return TIPO

async def recibir_tipo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["tipo"] = update.message.text
    await update.message.reply_text(
        "👤 ¿Cuál es el *nombre del cliente*?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return NOMBRE

async def recibir_nombre(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["nombre"] = update.message.text
    await update.message.reply_text("📞 ¿Cuál es el *teléfono*?", parse_mode="Markdown")
    return TELEFONO

async def recibir_telefono(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["telefono"] = update.message.text
    await update.message.reply_text("📍 ¿Cuál es la *dirección o barrio*?", parse_mode="Markdown")
    return DIRECCION

async def recibir_direccion(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["direccion"] = update.message.text
    await update.message.reply_text(
        "📝 ¿Algún detalle adicional? (escribe *ninguno* si no hay)",
        parse_mode="Markdown"
    )
    return DESCRIPCION

async def recibir_descripcion(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reportes = cargar_reportes()
    nuevo_id = (reportes[-1]["id"] + 1) if reportes else 1
    reporte = {
        "id": nuevo_id,
        "tipo": ctx.user_data["tipo"],
        "nombre": ctx.user_data["nombre"],
        "telefono": ctx.user_data["telefono"],
        "direccion": ctx.user_data["direccion"],
        "descripcion": update.message.text,
        "estado": "Pendiente",
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    reportes.append(reporte)
    guardar_reportes(reportes)
    await update.message.reply_text(
        f"✅ *Reporte #{nuevo_id} guardado*\n\n{formato_reporte(reporte)}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancelar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Reporte cancelado.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ── LISTADOS ─────────────────────────────────────────────
async def lista(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reportes = cargar_reportes()
    if not reportes:
        await update.message.reply_text("📭 No hay reportes registrados.")
        return
    for r in reportes[-10:]:
        await update.message.reply_text(formato_reporte(r), parse_mode="Markdown")

async def pendientes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reportes = [r for r in cargar_reportes() if r["estado"] == "Pendiente"]
    if not reportes:
        await update.message.reply_text("✅ No hay reportes pendientes.")
        return
    for r in reportes:
        await update.message.reply_text(formato_reporte(r), parse_mode="Markdown")

async def en_proceso(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reportes = [r for r in cargar_reportes() if r["estado"] == "En proceso"]
    if not reportes:
        await update.message.reply_text("📭 No hay reportes en proceso.")
        return
    for r in reportes:
        await update.message.reply_text(formato_reporte(r), parse_mode="Markdown")

async def resueltos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    reportes = [r for r in cargar_reportes() if r["estado"] == "Resuelto"]
    if not reportes:
        await update.message.reply_text("📭 No hay reportes resueltos.")
        return
    for r in reportes:
        await update.message.reply_text(formato_reporte(r), parse_mode="Markdown")

# ── CAMBIAR ESTADO ───────────────────────────────────────
async def resolver(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cambiar_estado(update, ctx, "Resuelto", "🟢")

async def proceso(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cambiar_estado(update, ctx, "En proceso", "🔵")

async def cambiar_estado(update, ctx, estado, emoji):
    if not ctx.args:
        await update.message.reply_text(f"Uso: /{estado.lower().replace(' ','')} <id>")
        return
    try:
        rid = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")
        return
    reportes = cargar_reportes()
    for r in reportes:
        if r["id"] == rid:
            r["estado"] = estado
            guardar_reportes(reportes)
            await update.message.reply_text(f"{emoji} Reporte #{rid} marcado como *{estado}*", parse_mode="Markdown")
            return
    await update.message.reply_text(f"❌ Reporte #{rid} no encontrado.")

async def eliminar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Uso: /eliminar <id>")
        return
    try:
        rid = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")
        return
    reportes = cargar_reportes()
    nuevos = [r for r in reportes if r["id"] != rid]
    if len(nuevos) == len(reportes):
        await update.message.reply_text(f"❌ Reporte #{rid} no encontrado.")
        return
    guardar_reportes(nuevos)
    await update.message.reply_text(f"🗑️ Reporte #{rid} eliminado.")

# ── MAIN ─────────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("nuevo", nuevo)],
        states={
            TIPO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tipo)],
            NOMBRE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            TELEFONO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)],
            DIRECCION:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_direccion)],
            DESCRIPCION:[MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("lista", lista))
    app.add_handler(CommandHandler("pendientes", pendientes))
    app.add_handler(CommandHandler("enproceso", en_proceso))
    app.add_handler(CommandHandler("resueltos", resueltos))
    app.add_handler(CommandHandler("resolver", resolver))
    app.add_handler(CommandHandler("proceso", proceso))
    app.add_handler(CommandHandler("eliminar", eliminar))

    print("🤖 Bot SIR activo...")
    app.run_polling()

if __name__ == "__main__":
    main()
