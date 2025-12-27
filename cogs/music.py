import discord
from discord.ext import commands
from discord import app_commands
import wavelink


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="play", description="Play music (SoundCloud-first)")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Join a voice channel first.",
                ephemeral=True
            )
            return

        # Connect if not connected
        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect(
                cls=wavelink.Player
            )

        player: wavelink.Player = interaction.guild.voice_client

        clean_query = normalize_query(query)

        # 🔒 SoundCloud-first search
        tracks = await wavelink.Playable.search(
            clean_query,
            source=wavelink.TrackSource.SoundCloud
        )

        if not tracks:
            await interaction.response.send_message(
                f"❌ No results found on SoundCloud for: `{clean_query}`"
            )
            return

        track = tracks[0]
        await player.play(track)

        await interaction.response.send_message(
            f"🎵 Now playing **{track.title}** *(via SoundCloud)*"
        )


    @app_commands.command(name="stop", description="Stop music and leave VC")
    async def stop(self, interaction: discord.Interaction):
        player: wavelink.Player | None = interaction.guild.voice_client

        if not player:
            await interaction.response.send_message(
                "I'm not in a voice channel.",
                ephemeral=True
            )
            return

        await player.disconnect()
        await interaction.response.send_message("Stopped.")

def normalize_query(query: str) -> str:
    blacklist = [
        "official video",
        "official music video",
        "lyrics",
        "lyric video",
        "audio",
        "hd",
        "4k",
        "mv"
    ]

    q = query.lower()
    for word in blacklist:
        q = q.replace(word, "")

    # collapse multiple spaces
    q = " ".join(q.split())
    return q.strip()

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
