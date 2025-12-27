import discord
import yt_dlp
import asyncio

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "default_search": "ytsearch",
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
    loop = asyncio.get_running_loop()

    def _extract():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)

            if not info or "entries" not in info or not info["entries"]:
                raise Exception("No results found")

            info = info["entries"][0]

            # Prefer direct HTTP(S) stream URLs
            if info.get("url", "").startswith(("http://", "https://")):
                return info["url"], info.get("title", "Unknown Title")

            for f in info.get("formats", []):
                url = f.get("url")
                if url and url.startswith(("http://", "https://")):
                    return url, info.get("title", "Unknown Title")

            raise Exception("No playable stream URL found")

    return await loop.run_in_executor(None, _extract)


async def play_next(bot, guild, queue):
    voice = guild.voice_client
    if not voice or voice.is_playing() or not queue:
        return

    url, title = queue.popleft()
    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    voice.play(
        source,
        after=lambda _: bot.loop.call_soon_threadsafe(
            asyncio.create_task,
            play_next(bot, guild, queue)
        )
    )
