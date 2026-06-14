import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from services.user_service import guardar_cuenta, obtener_cuenta
from main import verificar_transferencia

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TEMP_DIR = "temp/imagenes"

# Asegurar que el directorio temporal existe
os.makedirs(TEMP_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respuesta al comando /start"""
    mensaje = (
        "Bot de verificación CEP activo.\n\n"
        "Para registrar tu cuenta utiliza:\n\n"
        "/cuenta 123456789012345678\n\n"
        "Después envía una fotografía del comprobante."
    )
    await update.message.reply_text(mensaje)

async def cuenta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respuesta al comando /cuenta <cuenta>"""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Por favor, proporciona el número de cuenta. Ejemplo: /cuenta 123456789012345678")
        return

    nueva_cuenta = context.args[0]
    
    # El service ya limpia caracteres no numéricos, pero validamos que haya algo
    if any(c.isdigit() for c in nueva_cuenta):
        guardar_cuenta(user_id, nueva_cuenta)
        await update.message.reply_text("Cuenta registrada correctamente.")
    else:
        await update.message.reply_text("Error: La cuenta debe contener números.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa las fotografías enviadas por los usuarios."""
    user_id = update.effective_user.id
    cuenta = obtener_cuenta(user_id)

    if not cuenta:
        mensaje = (
            "No tienes una cuenta registrada.\n\n"
            "Utiliza:\n\n"
            "/cuenta 123456789012345678"
        )
        await update.message.reply_text(mensaje)
        return

    # Obtener la foto de mayor resolución
    photo_file = await update.message.photo[-1].get_file()
    file_id = photo_file.file_id
    ruta_imagen = os.path.join(TEMP_DIR, f"{user_id}_{file_id}.jpg")

    # Descargar imagen
    await update.message.reply_text("Procesando comprobante...")
    await photo_file.download_to_drive(ruta_imagen)

    try:
        # Ejecutar verificación
        resultado = await verificar_transferencia(
            ruta_imagen=ruta_imagen,
            cuenta_beneficiaria=cuenta
        )

        if resultado["exito"]:
            # Formatear datos extraídos para mostrar al usuario
            datos = resultado.get("datos_extraidos", {})
            info_datos = (
                f"📅 Fecha: {datos.get('fecha')}\n"
                f"💰 Monto: {datos.get('monto')}\n"
                f"🏦 Origen: {datos.get('banco_origen')}\n"
                f"🏦 Destino: {datos.get('banco_destino')}\n"
                f"🔢 Rastreo: {datos.get('clave_rastreo') or 'N/A'}"
            )
            
            await update.message.reply_text(
                f"✅ Verificación completada\n\n"
                f"{resultado['mensaje']}\n\n"
                f"Datos extraídos:\n{info_datos}"
            )
        else:
            await update.message.reply_text(
                f"❌ Verificación fallida\n\n"
                f"{resultado['mensaje']}"
            )

    except Exception as e:
        logging.error(f"Error procesando imagen del usuario {user_id}: {e}")
        await update.message.reply_text("Ocurrió un error durante la verificación.")
    
    finally:
        # Limpieza
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)

if __name__ == '__main__':
    if not TOKEN or TOKEN == "xxxxxxxxxxxxxxxx":
        print("⚠️ Error: TELEGRAM_BOT_TOKEN no configurado en el archivo .env")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        cuenta_handler = CommandHandler('cuenta', cuenta)
        photo_handler = MessageHandler(filters.PHOTO, handle_photo)
        
        application.add_handler(start_handler)
        application.add_handler(cuenta_handler)
        application.add_handler(photo_handler)
        
        print("Bot iniciado. Presiona Ctrl+C para detener.")
        application.run_polling()
