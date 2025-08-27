# bot.py
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Bot tokend not found. Put DISCORD_TOKEN=... in a .env file.")

# Intents
intents = discord.Intents.default()
intents.message_content = True  # Needed if you want to read message text

# Create bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    # Sync slash (/) commands to Discord
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

# A simple slash command: /ping
@bot.tree.command(name="ping", description="Replies with Pong and latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

# A classic prefix command: !echo your text
@bot.command(name="echo", help="Echoes your message back.")
async def echo(ctx, *, message: str):
    await ctx.send(message)

# Respond when someone says "hello"
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.lower().startswith("hello"):
        await message.channel.send(f"Hi {message.author.mention}! 👋")
    # Make sure other commands still work
    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
