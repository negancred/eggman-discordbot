import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio
from typing import Dict, List


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        
        
        self.queues: Dict[int, List[wavelink.Playable]] = {}
        
        
        self.play_tasks: Dict[int, asyncio.Task] = {}
        
        
        self.COLOR = discord.Color.from_rgb(88, 66, 124)
    
    
    @app_commands.command(name="play", description="Play music (SoundCloud-first)")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message(
                embed=_make_error_embed("Join a voice channel first.")
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                embed=_make_error_embed("This command must be used in a server.")
            )
            return
        
        
        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect(cls=wavelink.Player)

        player: wavelink.Player = interaction.guild.voice_client

        tracks = await wavelink.Playable.search(
            normalize_query(query),
            source=wavelink.TrackSource.SoundCloud
        )

        if not tracks:
            await interaction.response.send_message(
                embed=_make_error_embed("No results found.")
            )
            return

        track = tracks[0]
        guild_id = interaction.guild.id
        
        
        queue = self.queues.setdefault(guild_id, [])
        
        
        if player.playing or player.paused:
            queue.append(track)

            embed = discord.Embed(
                title="Added to Queue",
                description=f"**{track.title}**\nPosition: **#{len(queue)}**",
                color=self.COLOR
            )
            embed.set_footer(text="Queued")
            await interaction.response.send_message(embed=embed)
            return

        
        
        await player.play(track)
        await interaction.response.send_message(
            embed=_make_now_playing_embed(track, self.COLOR)
        )
        
        
        if guild_id not in self.play_tasks or self.play_tasks[guild_id].done():
            self.play_tasks[guild_id] = asyncio.create_task(
                self._playback_loop(interaction.guild, player)
            )
    
    
    @app_commands.command(name="queue_list", description="Show the current queue")
    async def queue_list(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        player: wavelink.Player | None = interaction.guild.voice_client

        queue = self.queues.get(guild_id, [])
        lines = []

        if player and player.current:
            lines.append(f"1. **{player.current.title}** (Now Playing)")

        for i, track in enumerate(queue[:15], start=2):
            lines.append(f"{i}. {track.title}")

        if not lines:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Queue",
                    description="The queue is empty.",
                    color=self.COLOR
                )
            )
            return

        embed = discord.Embed(
            title="Queue",
            description="\n".join(lines),
            color=self.COLOR
        )
        embed.set_footer(text="Showing up to 15 tracks")
        await interaction.response.send_message(embed=embed)

    
    
    @app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        player: wavelink.Player | None = interaction.guild.voice_client

        if not player or not player.playing:
            await interaction.response.send_message(
                embed=_make_error_embed("Nothing is playing.")
            )
            return

        await player.pause()
        embed = discord.Embed(
            title="Playback Paused",
            description=f"**{player.current.title}**",
            color=self.COLOR
        )
        embed.set_footer(text=f"Paused by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    
    
    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        player: wavelink.Player | None = interaction.guild.voice_client

        if not player or not player.paused:
            await interaction.response.send_message(
                embed=_make_error_embed("Nothing is paused.")
            )
            return

        await player.resume()
        embed = discord.Embed(
            title="Now Playing",
            description=f"**{player.current.title}**",
            color=self.COLOR
        )
        embed.set_footer(text=f"Resumed by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    
    
    @app_commands.command(name="leave", description="Stop playback and leave VC")
    async def leave(self, interaction: discord.Interaction):
        player: wavelink.Player | None = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if not player:
            await interaction.response.send_message(
                embed=_make_error_embed("I'm not in a voice channel.")
            )
            return

        self.queues.pop(guild_id, None)

        task = self.play_tasks.pop(guild_id, None)
        if task:
            task.cancel()

        await player.disconnect()

        embed = discord.Embed(
            title="Playback Stopped",
            description="Playback stopped and the queue was cleared.",
            color=self.COLOR
        )
        embed.set_footer(text=f"Left by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    
    
    async def _playback_loop(self, guild: discord.Guild, player: wavelink.Player):
        guild_id = guild.id

        try:
            while True:
                if not self.queues.get(guild_id):
                    break

                next_track = self.queues[guild_id].pop(0)
                await player.play(next_track)

                await self._announce_now_playing(guild, next_track)

                while player.playing or player.paused:
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass
        finally:
            self.play_tasks.pop(guild_id, None)
            if not self.queues.get(guild_id):
                self.queues.pop(guild_id, None)

    async def _announce_now_playing(self, guild: discord.Guild, track):
        channel = guild.system_channel or next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
            None
        )
        if channel:
            await channel.send(
                embed=_make_now_playing_embed(track, self.COLOR)
            )


def normalize_query(query: str) -> str:
    blacklist = ["official video", "lyrics", "audio", "hd", "4k", "mv"]
    q = query.lower()
    for word in blacklist:
        q = q.replace(word, "")
    return " ".join(q.split())


def _make_now_playing_embed(track, color):
    embed = discord.Embed(
        title="Now Playing",
        description=f"**{track.title}**",
        color=color
    )
    embed.add_field(name="Source", value="SoundCloud", inline=True)
    embed.set_footer(text="Playback started")
    return embed


def _make_error_embed(message: str):
    return discord.Embed(
        title="Error",
        description=message,
        color=discord.Color.dark_red()
    )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
