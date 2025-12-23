import discord
import yt_dlp
import asyncio

import discord
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn"
}


async def extract_audio(query: str):
    def _extract():
        search = f"ytmusicsearch1:{query}"

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search, download=False)

            if "entries" in info:
                info = info["entries"][0]

            return info["url"], info["title"]

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract)


async def play_next(bot, guild, queue):
    voice = guild.voice_client
    if not voice or not queue:
        return

    url, _ = queue.popleft()
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    def after(_):
        asyncio.run_coroutine_threadsafe(
            play_next(bot, guild, queue),
            bot.loop
        )

    voice.play(source, after=after)
