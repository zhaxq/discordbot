import discord
from discord.ext import commands
from discord import app_commands
import config
from datetime import datetime

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Crea un embed desde un mensaje dado su enlace o ID.")
    @app_commands.describe(message_link="Enlace o ID del mensaje")
    async def embed(self, interaction: discord.Interaction, message_link: str):
        guild = interaction.guild
        member = guild.get_member(interaction.user.id)

        if not member:
            await interaction.response.send_message("No se pudo encontrar tu información como miembro.", ephemeral=True)
            return

        # Verificar si el usuario tiene el rol necesario
        if config.BOTCOMMANDS_ROLE_ID not in [role.id for role in member.roles]:
            await interaction.response.send_message("No tienes el rol necesario para usar este comando.", ephemeral=True)
            return

        # Intentar obtener el mensaje del enlace o ID
        try:
            if "/" in message_link:
                parts = message_link.split("/")
                channel_id = int(parts[-2])
                message_id = int(parts[-1])
            else:
                channel_id = interaction.channel.id
                message_id = int(message_link)

            channel = guild.get_channel(channel_id)
            if not channel:
                raise ValueError("No se encontró el canal.")

            message = await channel.fetch_message(message_id)
        except Exception:
            await interaction.response.send_message("No se pudo obtener el mensaje. Verifica el enlace o el ID.", ephemeral=True)
            return

        # Crear el embed con los nuevos nombres de variables
        embed = discord.Embed(
            title=f"Repost de {message.author.name}",
            description=message.content if message.content else "Sin texto",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar.url if message.author.avatar else None)
        embed.set_footer(text=f"Publicado el {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Adjuntar imagen o video si el mensaje tiene archivos
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and ("image" in attachment.content_type or "video" in attachment.content_type):
                    embed.set_image(url=attachment.url)
                    break

        # Obtener el canal de repost y enviar el embed
        target_channel = guild.get_channel(config.REPOST_CHANNEL_ID)
        if not target_channel:
            await interaction.response.send_message("No se encontró el canal para publicar el mensaje.", ephemeral=True)
            return

        await target_channel.send(embed=embed)
        await interaction.response.send_message("Embed creado y publicado correctamente en el canal de repost.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))