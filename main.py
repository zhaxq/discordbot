import discord
from discord.ext import commands
import config
import asyncio
from flask import Flask
from threading import Thread
import os


from keep_alive import keep_alive
keep_alive()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Lista de cogs con comandos slash
SLASH_COMMAND_COGS = ["embed", "test", "sync"]
# Lista de cogs sin comandos slash (tareas, listeners, etc.)
OTHER_COGS = ["activity"]

@bot.event
async def on_ready():
    print(f'¡Bot conectado como {bot.user}!')

    await load_cogs()

    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        print(f"🔹 Se han sincronizado {len(synced)} comandos de aplicación (Slash Commands):")
        for command in synced:
            print(f"   ➜ /{command.name}")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos: {e}")

async def load_cogs():
    """Carga automáticamente los cogs en la carpeta cogs"""
    loaded_slash_cogs = []
    loaded_other_cogs = []

    for cog in SLASH_COMMAND_COGS + OTHER_COGS:  # Cargar ambas listas
        try:
            await bot.load_extension(f"cogs.{cog}")
            if cog in SLASH_COMMAND_COGS:
                loaded_slash_cogs.append(cog)
            else:
                loaded_other_cogs.append(cog)
        except Exception as e:
            print(f"❌ Error cargando {cog}: {e}")

    print(f"\n✅ Cogs con Slash Commands cargados: {', '.join(loaded_slash_cogs) if loaded_slash_cogs else 'Ninguno'}")
    print(f"🛠 Cogs sin comandos Slash (listeners/tareas): {', '.join(loaded_other_cogs) if loaded_other_cogs else 'Ninguno'}")

# 🔹 Inicia el bot
bot.run(config.TOKEN)