import discord
from discord.ext import commands, tasks
import json
import config  # Se mantiene la importación de config
from collections import defaultdict
import os
from datetime import datetime, timedelta

# Variables de configuración
IGNORED_CHANNELS = [1334959400070287390]  # Canales donde los mensajes no contarán
GENERAL_CHANNEL_ID = config.GENERAL_CHANNEL_ID  # Usa el canal definido en config.py
LOG_ACTIVITY = True  # Si es True, se mostrarán los mensajes contados en la consola
LOG_LEADERBOARD = True  # Si es True, cada X minutos se imprimirá en la consola un ranking de actividad
LEADERBOARD_INTERVAL = 5  # Intervalo de tiempo (en minutos) para mostrar el ranking
SAVE_INTERVAL = 30  # Guardar datos cada 30 segundos
WEEKLY_RESET_HOURS = 168  # 168 horas = 1 semana (7 días)

DATA_FILE = "activity_data.json"  # Archivo principal
BACKUP_FILE = "activity_data_backup.json"  # Archivo de respaldo

class ActivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_counts = defaultdict(int)
        self.week_start_time = None
        self.load_data()  # Cargar datos previos

        # Iniciar tareas
        self.save_data_loop.start()
        self.check_week_reset.start()  # Nueva tarea para verificar si se cumplió la semana
        self.print_leaderboard.start()  # Se añadió nuevamente la tarea de leaderboard en consola

    def cog_unload(self):
        """Detiene las tareas cuando se descarga el cog."""
        self.save_data_loop.cancel()
        self.check_week_reset.cancel()
        self.print_leaderboard.cancel()
        self.save_data()

    def load_data(self):
        """Carga los datos almacenados desde el archivo JSON o su respaldo."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.message_counts = defaultdict(int, {int(k): v for k, v in data.get("message_counts", {}).items()})
                    self.week_start_time = datetime.fromisoformat(data.get("week_start_time")) if data.get("week_start_time") else datetime.utcnow()
                    print("📂 Datos de mensajes cargados correctamente desde el archivo principal.")

                    # Verificar si ya pasó la semana al iniciar
                    if datetime.utcnow() - self.week_start_time >= timedelta(hours=WEEKLY_RESET_HOURS):
                        print("⏳ La semana ha terminado, iniciando nuevo ciclo.")
                        self.publish_weekly_winner()
                        self.reset_week_data()

                    return
            except (json.JSONDecodeError, ValueError):
                print("❌ Error al leer el archivo de datos, intentando restaurar desde el backup.")

        # Intentar cargar desde el backup si el principal está corrupto
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    self.message_counts = defaultdict(int, {int(k): v for k, v in data.get("message_counts", {}).items()})
                    self.week_start_time = datetime.fromisoformat(data.get("week_start_time")) if data.get("week_start_time") else datetime.utcnow()
                    print("🔄 Se ha restaurado el respaldo correctamente.")
                    return
            except Exception:
                print("❌ No se pudo restaurar el respaldo, iniciando nueva actividad.")

        # Si ambos archivos están corruptos, iniciar desde cero
        self.reset_week_data()

    def reset_week_data(self):
        """Reinicia los datos para una nueva semana."""
        self.message_counts = defaultdict(int)
        self.week_start_time = datetime.utcnow()
        self.save_data()
        print("🔄 Se ha iniciado un nuevo ciclo de conteo semanal.")

    def save_data(self):
        """Guarda los datos actuales en el archivo principal y su respaldo."""
        try:
            data = {
                "message_counts": {str(k): v for k, v in self.message_counts.items()},
                "week_start_time": self.week_start_time.isoformat() if self.week_start_time else None
            }

            with open(DATA_FILE, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)

            with open(BACKUP_FILE, "w", encoding="utf-8") as backup_file:
                json.dump(data, backup_file, indent=4)

            print("💾 Datos de mensajes guardados correctamente y backup actualizado.")
        except Exception as e:
            print(f"❌ Error al guardar datos: {e}")

    @tasks.loop(minutes=LEADERBOARD_INTERVAL)
    async def print_leaderboard(self):
        """Muestra en la consola un ranking de los 5 usuarios más activos de la semana."""
        if not LOG_LEADERBOARD or not self.message_counts:
            return

        sorted_users = sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        guild = self.bot.get_guild(config.SERVER_ID)

        print("\n🏆 **LEADERBOARD DE ACTIVIDAD (TOP 5 USUARIOS MÁS ACTIVOS DE LA SEMANA)** 🏆")
        for rank, (user_id, count) in enumerate(sorted_users, start=1):
            user = guild.get_member(user_id) or await self.bot.fetch_user(user_id)
            user_name = user.name if user else "Usuario desconocido"
            print(f"  {rank}. {user_name} - {count} mensajes")

    @tasks.loop(minutes=1)
    async def check_week_reset(self):
        """Verifica si se cumplió una semana y reinicia los datos si es necesario."""
        if datetime.utcnow() - self.week_start_time >= timedelta(hours=WEEKLY_RESET_HOURS):
            print("⏳ Se ha cumplido la semana, publicando el usuario más activo.")
            await self.publish_weekly_winner()
            self.reset_week_data()

    async def publish_weekly_winner(self):
        """Publica en Discord quién fue el usuario más activo de la semana con el mensaje solicitado."""
        if not self.message_counts:
            return

        sorted_users = sorted(self.message_counts.items(), key=lambda x: x[1], reverse=True)
        guild = self.bot.get_guild(config.SERVER_ID)
        general_channel = guild.get_channel(GENERAL_CHANNEL_ID)

        if sorted_users:
            top_user_id, top_messages = sorted_users[0]
            top_user = guild.get_member(top_user_id) or await self.bot.fetch_user(top_user_id)
            top_user_name = top_user.mention if top_user else "Usuario desconocido"

            message_text = f"{top_user_name} is the faggot of this week with `{top_messages}` messages"
            print(f"{message_text}")

            if general_channel:
                await general_channel.send(message_text)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Escucha cada mensaje enviado en el servidor y cuenta mensajes."""
        if message.author.bot:  # Ignorar mensajes de bots
            return

        if message.channel.id in IGNORED_CHANNELS:  # Ignorar los canales especificados
            return

        # Registrar mensaje en el conteo del usuario
        user_id = int(message.author.id)
        self.message_counts[user_id] += 1

        # Si LOG_ACTIVITY está activado, imprimir en la consola el mensaje del usuario con el nuevo formato
        if LOG_ACTIVITY:
            print(f"new message of {message.author.name} on {message.channel.name}. {self.message_counts[user_id]} messages")

    @tasks.loop(seconds=SAVE_INTERVAL)
    async def save_data_loop(self):
        """Guarda los datos en un intervalo de tiempo para evitar corrupción."""
        self.save_data()

async def setup(bot):
    await bot.add_cog(ActivityTracker(bot))
