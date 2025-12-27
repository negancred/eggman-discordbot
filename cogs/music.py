import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from collections import deque

from .music_helpers import extract_audio, play_next, FFMPEG_OPTIONS


JOYFUL_LINES = [
    "HO HO HO! Let’s gooo! 🎄🎶",
    "Eggman is vibing! 🎧",
    "Music time! This one’s a banger 💃",
    "Oho! A fine choice indeed 🎵",
    "Hehe~ I like this one 🎶"
]

QUEUE_LINES = [
    "Added to the lineup! 🎶",
    "Queued and ready to roll! 🎵",
    "Next up! Eggman approves 😌",
    "Stacked neatly in the queue 📀"
]


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, deque] = {}

    def get_queue(self, guild_id: int) -> deque:
        self.queues.setdefault(guild_id, deque())
        return self.queues[guild_id]

    # ───────── EMBEDS ─────────

    def error_embed(self, msg: str) -> discord.Embed:
        return discord.Embed(
            title="❌ Eggman tripped!",
            description=msg,
            color=discord.Color.red()
        )

    def joyful_embed(self, title: str, msg: str) -> discord.Embed:
        e = discord.Embed(
            title=title,
            description=msg,
            color=discord.Color.blurple()
        )
        e.set_footer(text=random.choice(JOYFUL_LINES))
        return e

    def queue_embed(self, title: str, msg: str) -> discord.Embed:
        e = discord.Embed(
            title=title,
            description=msg,
            color=discord.Color.green()
        )
        e.set_footer(text=random.choice(QUEUE_LINES))
        return e

    # ───────── CORE PLAY LOGIC ─────────

    async def handle_play(self, interaction: discord.Interaction, query: str):
        user_voice = interaction.user.voice
        if not user_voice:
            await interaction.response.send_message(
                embed=self.error_embed("Hop into a voice channel first! 🐣"),
                ephemeral=True
            )
            return

        channel = user_voice.channel
        voice = interaction.guild.voice_client

        if voice and voice.channel != channel:
            await interaction.response.send_message(
                embed=self.error_embed(
                    f"I'm already singing in **#{voice.channel.name}** 🎤"
                ),
                ephemeral=True
            )
            return

        if not voice:
            voice = await channel.connect()

        await interaction.response.defer()

        try:
            url, title = await extract_audio(query)
        except Exception:
            await interaction.followup.send(
                embed=self.error_embed("Eggman couldn’t grab that tune 😢"),
                ephemeral=True
            )
            return

        queue = self.get_queue(interaction.guild.id)

        if voice.is_playing() or voice.is_paused():
            queue.append((url, title))
            await interaction.followup.send(
                embed=self.queue_embed(
                    "🎶 Queued!",
                    f"**{title}** is ready for its turn!"
                )
            )
        else:
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            voice.play(
                source,
                after=lambda _: self.bot.loop.call_soon_threadsafe(
                    asyncio.create_task,
                    play_next(self.bot, interaction.guild, queue)
                )
            )

            await interaction.followup.send(
                embed=self.joyful_embed(
                    "🎵 Now Playing",
                    f"**{title}**\n📍 **#{channel.name}**"
                )
            )

    # ───────── COMMANDS ─────────

    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, query: str):
        await self.handle_play(interaction, query)

    @app_commands.command(name="queue")
    async def queue_list(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)

        if not queue:
            await interaction.response.send_message(
                embed=self.joyful_embed(
                    "📭 Queue Empty!",
                    "No songs waiting right now! Toss one in 😄"
                ),
                ephemeral=True
            )
            return

        lines = [
            f"**{i}.** {title}"
            for i, (_, title) in enumerate(queue, start=1)
        ]

        await interaction.response.send_message(
            embed=discord.Embed(
                title="📜 Eggman’s Queue",
                description="\n".join(lines),
                color=discord.Color.gold()
            )
        )

    @app_commands.command(name="skip")
    async def skip(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_playing():
            await interaction.response.send_message(
                embed=self.error_embed("Nothing to skip 🤷"),
                ephemeral=True
            )
            return

        voice.stop()
        await interaction.response.send_message(
            embed=self.joyful_embed("⏭ Skipped!", "Next bop incoming 🎶")
        )

    @app_commands.command(name="stop")
    async def stop(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message(
                embed=self.error_embed("I'm not singing right now 😴"),
                ephemeral=True
            )
            return

        self.get_queue(interaction.guild.id).clear()
        voice.stop()

        await interaction.response.send_message(
            embed=self.joyful_embed("🛑 All Stopped!", "Eggman bows 🎩")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
