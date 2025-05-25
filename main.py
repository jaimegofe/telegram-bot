import asyncio
import logging
import random
import nest_asyncio
import aiohttp
import os
from aiohttp import web
from telegram import Update, Message
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Aplica el parche para evitar errores con event loop
nest_asyncio.apply()

# Logging
logging.basicConfig(level=logging.INFO)

# Token desde variable de entorno
TOKEN = os.environ["TOKEN"]

# Lista en memoria para guardar mensajes multimedia
media_messages = []

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! El bot está funcionando y el servidor web también.")

# Comando /azar
async def azar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not media_messages:
        await update.message.reply_text("Aún no he visto ningún archivo multimedia.")
        return

    random_msg: Message = random.choice(media_messages)

    try:
        if random_msg.photo:
            await update.message.reply_photo(random_msg.photo[-1].file_id)
        elif random_msg.video:
            await update.message.reply_video(random_msg.video.file_id)
        elif random_msg.animation:
            await update.message.reply_animation(random_msg.animation.file_id)
        else:
            await update.message.reply_text("Ocurrió un error al intentar enviar el archivo.")
    except Exception as e:
        logging.error(f"Error al enviar multimedia: {e}")
        await update.message.reply_text("No pude reenviar el archivo.")

# Handler para guardar multimedia
async def save_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.photo or msg.video or msg.animation:
        media_messages.append(msg)
        logging.info("📥 Archivo multimedia guardado.")

# Ruta web para mantener el bot despierto
async def handle_web(request):
    return web.Response(text="El bot de Telegram está activo ✅")

# Keep alive ping a Railway
async def keep_alive_ping():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://TU-NOMBRE.up.railway.app") as resp:
                    if resp.status == 200:
                        logging.info("✅ Auto-ping exitoso para mantener activo.")
        except Exception as e:
            logging.warning(f"⚠️ Error en auto-ping: {e}")
        await asyncio.sleep(300)

# Función principal
async def main():
    print("Iniciando servidor web y bot...")

    # Servidor aiohttp
    web_app = web.Application()
    web_app.router.add_get("/", handle_web)
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Servidor web activo en el puerto {port}")

    # Inicializa el bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("azar", azar))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.ANIMATION, save_media))

    # Ejecuta el bot
    asyncio.create_task(app.run_polling())
    asyncio.create_task(keep_alive_ping())

    # Mantener vivo
    while True:
        await asyncio.sleep(3600)

# Ejecutar todo
asyncio.run(main())
