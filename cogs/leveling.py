import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "leveling.json"

if not DATA_FILE.exists():
    DATA_FILE.write_text("{}")


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class Leveling(commands.Cog):
    """Simple XP/Leveling system.

    - Awards XP for normal messages (5-15 XP).
    - Persists per-guild, per-user XP and level to `data/leveling.json`.
    - Provides `/xp` and `/profile` slash commands.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()

    def _get_member_record(self, guild_id: int, user_id: int):
        g = str(guild_id)
        u = str(user_id)
        self.data.setdefault(g, {})
        self.data[g].setdefault(u, {"xp": 0, "level": 0})
        return self.data[g][u]

    def _xp_for_next_level(self, level: int):
        # Simple linear scaling: next level requires 100 * (level + 1) XP
        return 100 * (level + 1)

    def _add_xp(self, guild_id: int, user_id: int, amount: int):
        rec = self._get_member_record(guild_id, user_id)
        rec["xp"] += int(amount)
        leveled = False
        while rec["xp"] >= self._xp_for_next_level(rec["level"]):
            rec["xp"] -= self._xp_for_next_level(rec["level"])
            rec["level"] += 1
            leveled = True
        save_data(self.data)
        return leveled, rec["level"]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        # Award XP for contentful messages
        xp_gain = random.randint(5, 15)
        leveled, new_level = self._add_xp(message.guild.id, message.author.id, xp_gain)

        if leveled:
            try:
                await message.channel.send(
                    embed=discord.Embed(
                        title=f"🎉 {message.author.display_name} leveled up!",
                        description=f"Reached level **{new_level}** — congrats!",
                        color=discord.Color.green()
                    )
                )
            except Exception:
                # Don't fail the listener if sending fails
                pass

    @app_commands.command(name="xp")
    async def xp(self, interaction: discord.Interaction):
        """View your current XP and level."""
        if not interaction.guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        rec = self._get_member_record(interaction.guild.id, interaction.user.id)
        next_xp = self._xp_for_next_level(rec["level"]) - rec["xp"]

        e = discord.Embed(
        title="-- XP Overview --",
        description=f"**{interaction.user.display_name}**",
        color=discord.Color.blurple()
        )

        progress_bar_length = 10
        progress = int((rec["xp"] / self._xp_for_next_level(rec["level"])) * progress_bar_length)
        bar = "🟩" * progress + "⬛" * (progress_bar_length - progress)

        e.add_field(
            name="🏆 Level",
            value=f"**{rec['level']}**",
            inline=True
        )

        e.add_field(
            name="✨ XP Progress",
            value=f"`{bar}`\n{rec['xp']} / {self._xp_for_next_level(rec['level'])} XP",
            inline=False
        )

        e.set_thumbnail(url=interaction.user.display_avatar.url)
        e.set_footer(text=f"{next_xp} XP needed for next level")

        await interaction.response.send_message(embed=e, ephemeral=True)


    @app_commands.command(name="profile")
    @app_commands.describe(user="User to view (defaults to you)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        """View a user's profile with join date, level and XP."""
        if not interaction.guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        member = user or interaction.user
        rec = self._get_member_record(interaction.guild.id, member.id)
        next_xp = self._xp_for_next_level(rec["level"]) - rec["xp"]

        e = discord.Embed(
        title="👤 User Profile",
        description=f"**{member.display_name}**",
        color=discord.Color.gold()
        )

        joined = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"

        progress_bar_length = 10
        progress = int((rec["xp"] / self._xp_for_next_level(rec["level"])) * progress_bar_length)
        bar = "🟩" * progress + "⬛" * (progress_bar_length - progress)

        e.add_field(
            name="📛 Username",
            value=str(member),
            inline=True
        )

        e.add_field(
            name="📅 Joined Server",
            value=joined,
            inline=True
        )

        e.add_field(
            name="🏆 Level",
            value=f"**{rec['level']}**",
            inline=True
        )

        e.add_field(
            name="✨ XP Progress",
            value=f"`{bar}`\n{rec['xp']} / {self._xp_for_next_level(rec['level'])} XP",
            inline=False
        )

        e.set_thumbnail(url=member.display_avatar.url)
        e.set_footer(text=f"{next_xp} XP to next level")

        await interaction.response.send_message(embed=e)



async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
