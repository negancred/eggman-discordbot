import discord
from discord.ext import commands
from discord import app_commands

class MsgGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="msg", description="Message moderation commands")

    @app_commands.command(name="purge")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(count="Number of recent messages to delete (1-100)")
    async def purge(self, interaction: discord.Interaction, count: int):
        if not interaction.guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        if count < 1 or count > 100:
            await interaction.response.send_message("`count` must be between 1 and 100.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("This command must be used in a text channel.", ephemeral=True)
            return

        try:
            deleted = await channel.purge(limit=count)
            await interaction.followup.send(f"Deleted {len(deleted)} message(s).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Failed to purge messages: {e}", ephemeral=True)


class MessageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    bot.tree.add_command(MsgGroup())
    await bot.add_cog(MessageCog(bot))
