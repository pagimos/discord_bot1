# bot.py
import os
import logging
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import random
import json

logging.basicConfig(level=logging.INFO)

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Bot token not found. Put DISCORD_TOKEN=... in a .env file.")

# Intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Market data
MARKET_DATA = {
    "United States": [
        {"name": "Premium Coffee Beans", "price": 24.99, "description": "Fresh roasted Arabica beans"},
        {"name": "Artisan Bread", "price": 8.50, "description": "Handcrafted sourdough loaf"},
        {"name": "Organic Honey", "price": 15.99, "description": "Pure wildflower honey"}
    ],
    "Japan": [
        {"name": "Matcha Tea Set", "price": 45.00, "description": "Traditional Japanese green tea"},
        {"name": "Sushi Rice", "price": 12.99, "description": "Premium short-grain rice"},
        {"name": "Miso Paste", "price": 18.50, "description": "Authentic fermented soybean paste"}
    ],
    "Italy": [
        {"name": "Extra Virgin Olive Oil", "price": 32.99, "description": "Cold-pressed from Tuscany"},
        {"name": "Truffle Pasta", "price": 28.00, "description": "Black truffle infused pasta"},
        {"name": "Aged Balsamic", "price": 55.99, "description": "25-year aged vinegar"}
    ],
    "France": [
        {"name": "Champagne", "price": 89.99, "description": "Vintage French sparkling wine"},
        {"name": "Camembert Cheese", "price": 22.50, "description": "Creamy Normandy cheese"},
        {"name": "Lavender Honey", "price": 19.99, "description": "Provence lavender-infused honey"}
    ],
    "Mexico": [
        {"name": "Chili Peppers", "price": 14.99, "description": "Assorted dried Mexican chilies"},
        {"name": "Tequila", "price": 65.00, "description": "Premium blue agave tequila"},
        {"name": "Mexican Chocolate", "price": 16.50, "description": "Dark chocolate with cinnamon"}
    ]
}

# Store user orders
user_orders = {}

class MarketView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.user_id = user_id
        self.selected_items = []
        
        # Initialize user order if not exists
        if user_id not in user_orders:
            user_orders[user_id] = []
    
    @discord.ui.button(label="Clear Cart", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        user_orders[self.user_id] = []
        self.selected_items = []
        await interaction.response.send_message("🛒 Cart cleared!", ephemeral=True)
    
    @discord.ui.button(label="Confirm Order", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        if not user_orders[self.user_id]:
            await interaction.response.send_message("Your cart is empty!", ephemeral=True)
            return
        
        # Calculate total
        total = sum(item["price"] for item in user_orders[self.user_id])
        
        # Create order summary
        embed = discord.Embed(
            title="🛒 Order Confirmed!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        for item in user_orders[self.user_id]:
            embed.add_field(
                name=f"${item['price']:.2f} - {item['name']}",
                value=item['description'],
                inline=False
            )
        
        embed.add_field(
            name="💰 Total",
            value=f"**${total:.2f} USD**",
            inline=False
        )
        
        embed.set_footer(text=f"Order by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
        # Clear the order after confirmation
        user_orders[self.user_id] = []
        self.selected_items = []

class CountryView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="🇺🇸 United States", style=discord.ButtonStyle.primary)
    async def usa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_country_items(interaction, "United States")
    
    @discord.ui.button(label="🇯🇵 Japan", style=discord.ButtonStyle.primary)
    async def japan(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_country_items(interaction, "Japan")
    
    @discord.ui.button(label="🇮🇹 Italy", style=discord.ButtonStyle.primary)
    async def italy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_country_items(interaction, "Italy")
    
    @discord.ui.button(label="🇫🇷 France", style=discord.ButtonStyle.primary)
    async def france(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_country_items(interaction, "France")
    
    @discord.ui.button(label="🇲🇽 Mexico", style=discord.ButtonStyle.primary)
    async def mexico(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_country_items(interaction, "Mexico")
    
    async def show_country_items(self, interaction: discord.Interaction, country: str):
        items = MARKET_DATA[country]
        
        embed = discord.Embed(
            title=f"🛍️ {country} Market",
            description="Click on items to add them to your cart!",
            color=discord.Color.blue()
        )
        
        for i, item in enumerate(items):
            embed.add_field(
                name=f"${item['price']:.2f} - {item['name']}",
                value=item['description'],
                inline=False
            )
        
        # Create item selection view
        item_view = ItemSelectionView(self.user_id, country)
        await interaction.response.edit_message(embed=embed, view=item_view)

class ItemSelectionView(discord.ui.View):
    def __init__(self, user_id: int, country: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.country = country
    
    @discord.ui.button(label="Add Item 1", style=discord.ButtonStyle.secondary, row=0)
    async def item1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_item(interaction, 0)
    
    @discord.ui.button(label="Add Item 2", style=discord.ButtonStyle.secondary, row=0)
    async def item2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_item(interaction, 1)
    
    @discord.ui.button(label="Add Item 3", style=discord.ButtonStyle.secondary, row=0)
    async def item3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_item(interaction, 2)
    
    @discord.ui.button(label="View Cart", style=discord.ButtonStyle.success, row=1)
    async def view_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_cart(interaction)
    
    async def add_item(self, interaction: discord.Interaction, item_index: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        item = MARKET_DATA[self.country][item_index]
        
        # Initialize user order if not exists
        if self.user_id not in user_orders:
            user_orders[self.user_id] = []
        
        # Add item to cart
        user_orders[self.user_id].append(item)
        
        await interaction.response.send_message(
            f"✅ Added **{item['name']}** (${item['price']:.2f}) to your cart!",
            ephemeral=True
        )
    
    async def show_cart(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        if not user_orders.get(self.user_id, []):
            await interaction.response.send_message("Your cart is empty!", ephemeral=True)
            return
        
        # Create cart view
        cart_view = MarketView(self.user_id)
        await interaction.response.edit_message(view=cart_view)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    # Sync slash (/) commands to Discord
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

# Market command
@bot.tree.command(name="market", description="Open the international market to browse items from different countries")
async def market(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌍 International Market",
        description="Welcome to the market! Choose a country to browse their unique items.",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Available Countries",
        value="🇺🇸 United States\n🇯🇵 Japan\n🇮🇹 Italy\n🇫🇷 France\n🇲🇽 Mexico",
        inline=False
    )
    
    embed.add_field(
        name="How it works",
        value="1. Select a country\n2. Choose items to add to cart\n3. View cart and confirm order",
        inline=False
    )
    
    # Create country selection view
    view = CountryView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

# A simple slash command: /ping
@bot.tree.command(name="ping", description="Replies with Pong and latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    bot.run(TOKEN)
