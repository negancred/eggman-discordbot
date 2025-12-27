import os
import logging
import discord
from discord.ext import commands
import wavelink
from dotenv import load_dotenv

load_dotenv()

# --------------------
# Logging (Docker-safe)
# --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("eggman")

# --------------------
# Discord Intents
# --------------------
intents = discord.Intents.default()
intents.voice_states = True   # REQUIRED for voice
# message_content not required since you use slash commands


# --------------------
# Bot Class
# --------------------
class Eggman(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        """
        This runs BEFORE on_ready.
        Perfect place to:
        - connect to Lavalink
        - load cogs
        - sync slash commands
        """

        # --------------------
        # Connect to Lavalink
        # --------------------
        log.info("Connecting to Lavalink...")

        node = wavelink.Node(
            uri="http://lavalink:2333",      # Docker service name
            password="eggmanpassword"        # MUST match application.yml
        )

        await wavelink.Pool.connect(
            nodes=[node],
            client=self
        )

        log.info("CONNECTED TO LAVALINK")

        # --------------------
        # Load Cogs
        # --------------------
        await self.load_extension("cogs.music")
        await self.load_extension("cogs.leveling")
        await self.load_extension("cogs.message")

        log.info("All cogs loaded")

        # --------------------
        # Sync Slash Commands
        # --------------------
        await self.tree.sync()
        log.info("Slash commands synced")


# --------------------
# Bot Startup
# --------------------
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
