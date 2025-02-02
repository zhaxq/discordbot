import os

# Verifica si está en Replit (usando Replit Secrets)
if "REPL_OWNER" in os.environ:  
    from replit import db  # Solo se importa si estás en Replit
    TOKEN = os.environ.get("TOKEN")  # Replit almacena secrets en os.environ
else:
    # Si no está en Replit, usa la variable de entorno de Railway
    TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ ERROR: No se encontró el TOKEN en las variables de entorno.")
GENERAL_CHANNEL_ID = 1333473708538331169  # Canal donde se enviará el mensaje
BOTCOMMANDS_ROLE_ID = 1333479147082612938  # ID del rol de admin
REPOST_CHANNEL_ID = 1333478891267817586  # ID del canal donde se publicará el embed
SERVER_ID = 1333473708538331166  # ID de tu servidor