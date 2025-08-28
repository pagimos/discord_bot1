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

# Store user selections for the ghost shop
ghost_selections = {}

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
    user_id = interaction.user.id
    
    # Initialize user selection if not exists
    if user_id not in ghost_selections:
        ghost_selections[user_id] = []
    
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
    
    for i, (country, price, description) in enumerate(items, 1):
        # Check if item is selected
        is_selected = i in ghost_selections[user_id]
        status = "✅ SELECTED" if is_selected else "❌ Not selected"
        
        embed.add_field(
            name=f"{i}. {country} - {price}",
            value=f"{description}\n**Status:** {status}",
            inline=False
        )
    
    # Show current selection info
    if ghost_selections[user_id]:
        selected_items = [items[i-1] for i in ghost_selections[user_id]]
        total_price = " + ".join([f"{item[1]}" for item in selected_items])
        embed.add_field(
            name="🛒 Your Current Selection",
            value=f"Items: {len(ghost_selections[user_id])}/5\nTotal: {total_price}",
            inline=False
        )
    
    embed.set_footer(text="💀 Use /select <number> to choose items, /confirm to purchase, /clear to reset")
    
    await interaction.response.send_message(embed=embed)

# Select item command
@bot.tree.command(name="select", description="Select an item from the ghost shop (1-5)")
async def select(interaction: discord.Interaction, item_number: int):
    user_id = interaction.user.id
    
    if user_id not in ghost_selections:
        ghost_selections[user_id] = []
    
    if item_number < 1 or item_number > 5:
        await interaction.response.send_message("❌ Please select a number between 1 and 5!", ephemeral=True)
        return
    
    if item_number in ghost_selections[user_id]:
        # Remove item if already selected
        ghost_selections[user_id].remove(item_number)
        await interaction.response.send_message(f"❌ Removed item {item_number} from your selection!", ephemeral=True)
    else:
        # Add item if not selected
        if len(ghost_selections[user_id]) >= 5:
            await interaction.response.send_message("❌ You can only select up to 5 items!", ephemeral=True)
            return
        
        ghost_selections[user_id].append(item_number)
        await interaction.response.send_message(f"✅ Added item {item_number} to your selection!", ephemeral=True)
    
    # Show updated selection
    await show_selection(interaction.channel, user_id)

# Confirm purchase command
@bot.tree.command(name="confirm", description="Confirm your ghost shop purchase")
async def confirm(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id not in ghost_selections or not ghost_selections[user_id]:
        await interaction.response.send_message("❌ You haven't selected any items yet! Use /ghost to see items and /select to choose them.", ephemeral=True)
        return
    
    # Get selected items
    items = [
        ("🇯🇵 Japan", "¥15,000", "A mysterious katana with unknown powers"),
        ("🇫🇷 France", "€2,500", "An enchanted bottle of vintage wine"),
        ("🇪🇬 Egypt", "$8,900", "An ancient amulet from the pyramids"),
        ("🇧🇷 Brazil", "R$12,000", "A mystical crystal from the Amazon"),
        ("🇷🇺 Russia", "₽180,000", "A mysterious nesting doll with secrets inside")
    ]
    
    selected_items = [items[i-1] for i in ghost_selections[user_id]]
    total_price = " + ".join([f"{item[1]}" for item in selected_items])
    
    # Create confirmation embed
    embed = discord.Embed(
        title="🎉 Purchase Confirmed!",
        description=f"Congratulations {interaction.user.mention}! Your ghost shop items have been purchased.",
        color=0x00FF00  # Green for success
    )
    
    for country, price, description in selected_items:
        embed.add_field(
            name=f"{country} - {price}",
            value=description,
            inline=False
        )
    
    embed.add_field(
        name="💰 Total Spent",
        value=total_price,
        inline=False
    )
    
    embed.set_footer(text="✨ Your items will be delivered to your ghost mailbox soon!")
    
    await interaction.response.send_message(embed=embed)
    
    # Clear user selection after purchase
    ghost_selections[user_id] = []

# Clear selection command
@bot.tree.command(name="clear", description="Clear your current ghost shop selection")
async def clear(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if user_id in ghost_selections:
        ghost_selections[user_id] = []
        await interaction.response.send_message("🗑️ Your selection has been cleared!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You don't have any items selected!", ephemeral=True)

# Helper function to show current selection
async def show_selection(channel, user_id):
    if user_id not in ghost_selections or not ghost_selections[user_id]:
        return
    
    items = [
        ("🇯🇵 Japan", "¥15,000", "A mysterious katana with unknown powers"),
        ("🇫🇷 France", "€2,500", "An enchanted bottle of vintage wine"),
        ("🇪🇬 Egypt", "$8,900", "An ancient amulet from the pyramids"),
        ("🇧🇷 Brazil", "R$12,000", "A mystical crystal from the Amazon"),
        ("🇷🇺 Russia", "₽180,000", "A mysterious nesting doll with secrets inside")
    ]
    
    selected_items = [items[i-1] for i in ghost_selections[user_id]]
    total_price = " + ".join([f"{item[1]}" for item in selected_items])
    
    embed = discord.Embed(
        title="🛒 Your Current Selection",
        description="Here's what you've selected so far:",
        color=0x4169E1  # Royal blue
    )
    
    for country, price, description in selected_items:
        embed.add_field(
            name=f"{country} - {price}",
            value=description,
            inline=False
        )
    
    embed.add_field(
        name="💰 Total",
        value=total_price,
        inline=False
    )
    
    embed.set_footer(text="Use /confirm to purchase or /select to modify your selection")
    
    await channel.send(embed=embed)

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
