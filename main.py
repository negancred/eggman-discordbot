import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


intents = discord.Intents.default()

class Eggman(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):
        await self.load_extension("cogs.music")
        await self.load_extension("cogs.leveling")
        await self.load_extension("cogs.message")
        await self.tree.sync()
        print("Slash commands synced.")

bot = Eggman()

@bot.event
async def on_ready():
    print(f"Eggman is online as {bot.user} as s1.0")

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("Environment variable DISCORD_TOKEN is not set. Set it and retry.")

bot.run(token)
