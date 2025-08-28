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
    raise RuntimeError("Bot token not found. Put DISCORD_TOKEN=... in a .env file.")

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

# Ghost shop command: /ghost
@bot.tree.command(name="ghost", description="Shows 5 mysterious items from the ghost shop.")
async def ghost(interaction: discord.Interaction):
    # Create embed for the ghost shop
    embed = discord.Embed(
        title="👻 Ghost Shop - Mysterious Items",
        description="Welcome to the ethereal marketplace! Here are today's offerings:",
        color=0x8B008B  # Dark magenta for spooky theme
    )
    
    # Add 5 items named after countries with prices
    items = [
        ("🇯🇵 Japan", "¥15,000", "A mysterious katana with unknown powers"),
        ("🇫🇷 France", "€2,500", "An enchanted bottle of vintage wine"),
        ("🇪🇬 Egypt", "$8,900", "An ancient amulet from the pyramids"),
        ("🇧🇷 Brazil", "R$12,000", "A mystical crystal from the Amazon"),
        ("🇷🇺 Russia", "₽180,000", "A mysterious nesting doll with secrets inside")
    ]
    
    for country, price, description in items:
        embed.add_field(
            name=f"{country} - {price}",
            value=description,
            inline=False
        )
    
    embed.set_footer(text="💀 Items may have supernatural properties. Purchase at your own risk!")
    
    await interaction.response.send_message(embed=embed)

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
