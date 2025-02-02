import discord
from discord.ext import commands
from discord import app_commands

class SyncCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Forza la sincronización de los comandos del bot.")
    async def sync(self, interaction: discord.Interaction):
        """Sincroniza manualmente los comandos slash sin necesidad de reinvitar el bot."""

        # Responder primero para evitar que la interacción expire
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("Solo el dueño del servidor puede sincronizar los comandos.", ephemeral=True)
            return

        try:
            synced = await self.bot.tree.sync()  # Sincroniza globalmente
            await interaction.followup.send(f"Se han sincronizado {len(synced)} comandos.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error al sincronizar: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SyncCog(bot))
