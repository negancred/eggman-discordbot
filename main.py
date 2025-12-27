import os
import logging
import discord
from discord.ext import commands
import wavelink
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("eggman")



intents = discord.Intents.default()
intents.voice_states = True  


class Eggman(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        log.info("Connecting to Lavalink...")

        node = wavelink.Node(
            uri="http://lavalink:2333",  
            password="eggmanpassword"      
        )

        await wavelink.Pool.connect(
            nodes=[node],
            client=self
        )

        log.info("CONNECTED TO LAVALINK")

        await self.load_extension("cogs.music")
        await self.load_extension("cogs.leveling")
        await self.load_extension("cogs.message")

        log.info("All cogs loaded")
        await self.tree.sync()
        log.info("Slash commands synced")

bot = Eggman()

@bot.event
async def on_ready():
    log.info("Eggman is online as %s (v1.1)", bot.user)


token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError(
        "Environment variable DISCORD_TOKEN is not set. Set it and retry."
    )

bot.run(token)
