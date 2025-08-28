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

# Ghost shop command: /ghost with interactive buttons
@bot.tree.command(name="ghost", description="Shows 5 mysterious items from the ghost shop.")
async def ghost(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # Initialize user selection if not exists
    if user_id not in ghost_selections:
        ghost_selections[user_id] = []
    
    # Create embed for the ghost shop
    embed = discord.Embed(
        title="👻 Ghost Shop - Mysterious Items",
        description="Welcome to the ethereal marketplace! Click the buttons below to select items:",
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
    
    embed.set_footer(text="💀 Click the buttons below to select/deselect items and confirm your purchase!")
    
    # Create interactive buttons
    view = GhostShopView(user_id)
    
    await interaction.response.send_message(embed=embed, view=view)

# Interactive button view for ghost shop
class GhostShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.user_id = user_id
    
    @discord.ui.button(label="1️⃣ Japan", style=discord.ButtonStyle.secondary, custom_id="item_1")
    async def item_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_item(interaction, 1, button)
    
    @discord.ui.button(label="2️⃣ France", style=discord.ButtonStyle.secondary, custom_id="item_2")
    async def item_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_item(interaction, 2, button)
    
    @discord.ui.button(label="3️⃣ Egypt", style=discord.ButtonStyle.secondary, custom_id="item_3")
    async def item_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_item(interaction, 3, button)
    
    @discord.ui.button(label="4️⃣ Brazil", style=discord.ButtonStyle.secondary, custom_id="item_4")
    async def item_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_item(interaction, 4, button)
    
    @discord.ui.button(label="5️⃣ Russia", style=discord.ButtonStyle.secondary, custom_id="item_5")
    async def item_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_item(interaction, 5, button)
    
    @discord.ui.button(label="🛒 Confirm Purchase", style=discord.ButtonStyle.success, custom_id="confirm")
    async def confirm_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm_purchase_action(interaction)
    
    @discord.ui.button(label="🗑️ Clear All", style=discord.ButtonStyle.danger, custom_id="clear")
    async def clear_selection(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.clear_selection_action(interaction)
    
    async def toggle_item(self, interaction: discord.Interaction, item_number: int, button: discord.ui.Button):
        # Check if this is the correct user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return
        
        # Initialize user selection if not exists
        if self.user_id not in ghost_selections:
            ghost_selections[self.user_id] = []
        
        if item_number in ghost_selections[self.user_id]:
            # Remove item if already selected
            ghost_selections[self.user_id].remove(item_number)
            button.style = discord.ButtonStyle.secondary
            button.label = f"{item_number}️⃣ {'Japan' if item_number == 1 else 'France' if item_number == 2 else 'Egypt' if item_number == 3 else 'Brazil' if item_number == 4 else 'Russia'}"
            await interaction.response.send_message(f"❌ Removed item {item_number} from your selection!", ephemeral=True)
        else:
            # Add item if not selected
            if len(ghost_selections[self.user_id]) >= 5:
                await interaction.response.send_message("❌ You can only select up to 5 items!", ephemeral=True)
                return
            
            ghost_selections[self.user_id].append(item_number)
            button.style = discord.ButtonStyle.primary
            button.label = f"{item_number}️⃣ {'Japan' if item_number == 1 else 'France' if item_number == 2 else 'Egypt' if item_number == 3 else 'Brazil' if item_number == 4 else 'Russia'} ✅"
            await interaction.response.send_message(f"✅ Added item {item_number} to your selection!", ephemeral=True)
        
        # Update the embed to show current selection
        await self.update_embed(interaction)
    
    async def confirm_purchase_action(self, interaction: discord.Interaction):
        # Check if this is the correct user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return
        
        if not ghost_selections.get(self.user_id):
            await interaction.response.send_message("❌ You haven't selected any items yet! Select some items first.", ephemeral=True)
            return
        
        # Get selected items
        items = [
            ("🇯🇵 Japan", "¥15,000", "A mysterious katana with unknown powers"),
            ("🇫🇷 France", "€2,500", "An enchanted bottle of vintage wine"),
            ("🇪🇬 Egypt", "$8,900", "An ancient amulet from the pyramids"),
            ("🇧🇷 Brazil", "R$12,000", "A mystical crystal from the Amazon"),
            ("🇷🇺 Russia", "₽180,000", "A mysterious nesting doll with secrets inside")
        ]
        
        selected_items = [items[i-1] for i in ghost_selections[self.user_id]]
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
        
        # Clear user selection after purchase
        ghost_selections[self.user_id] = []
        
        # Disable all buttons after purchase
        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)
    
    async def clear_selection_action(self, interaction: discord.Interaction):
        # Check if this is the correct user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return
        
        # Clear selection
        if self.user_id in ghost_selections:
            ghost_selections[self.user_id] = []
        
        # Reset button styles
        for i, child in enumerate(self.children[:-2]):  # Exclude confirm and clear buttons
            child.style = discord.ButtonStyle.secondary
            item_names = ["Japan", "France", "Egypt", "Brazil", "Russia"]
            child.label = f"{i+1}️⃣ {item_names[i]}"
        
        await interaction.response.send_message("🗑️ Your selection has been cleared!", ephemeral=True)
        await self.update_embed(interaction)
    
    async def update_embed(self, interaction: discord.Interaction):
        # Update the embed to show current selection
        embed = interaction.message.embeds[0]
        
        # Clear existing fields except the first 5 items
        while len(embed.fields) > 5:
            embed.remove_field(5)
        
        # Update item status
        items = [
            ("🇯🇵 Japan", "¥15,000", "A mysterious katana with unknown powers"),
            ("🇫🇷 France", "€2,500", "An enchanted bottle of vintage wine"),
            ("🇪🇬 Egypt", "$8,900", "An ancient amulet from the pyramids"),
            ("🇧🇷 Brazil", "R$12,000", "A mystical crystal from the Amazon"),
            ("🇷🇺 Russia", "₽180,000", "A mysterious nesting doll with secrets inside")
        ]
        
        for i, (country, price, description) in enumerate(items):
            is_selected = i+1 in ghost_selections.get(self.user_id, [])
            status = "✅ SELECTED" if is_selected else "❌ Not selected"
            
            embed.set_field_at(i, 
                name=f"{i+1}. {country} - {price}",
                value=f"{description}\n**Status:** {status}",
                inline=False
            )
        
        # Show current selection info
        if ghost_selections.get(self.user_id):
            selected_items = [items[i-1] for i in ghost_selections[self.user_id]]
            total_price = " + ".join([f"{item[1]}" for item in selected_items])
            embed.add_field(
                name="🛒 Your Current Selection",
                value=f"Items: {len(ghost_selections[self.user_id])}/5\nTotal: {total_price}",
                inline=False
            )
        
        await interaction.message.edit(embed=embed)

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
