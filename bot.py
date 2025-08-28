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

class CountrySelect(discord.ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        
        options = [
            discord.SelectOption(
                label="United States",
                description="Browse American specialty items",
                emoji="🇺🇸",
                value="United States"
            ),
            discord.SelectOption(
                label="Japan",
                description="Discover Japanese delicacies",
                emoji="🇯🇵",
                value="Japan"
            ),
            discord.SelectOption(
                label="Italy",
                description="Italian gourmet products",
                emoji="🇮🇹",
                value="Italy"
            ),
            discord.SelectOption(
                label="France",
                description="French luxury items",
                emoji="🇫🇷",
                value="France"
            ),
            discord.SelectOption(
                label="Mexico",
                description="Mexican traditional products",
                emoji="🇲🇽",
                value="Mexico"
            )
        ]
        
        super().__init__(
            placeholder="🌍 Choose a country to browse...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This market is not for you!", ephemeral=True)
            return
        
        country = self.values[0]
        items = MARKET_DATA[country]
        
        embed = discord.Embed(
            title=f"🛍️ {country} Market",
            description="Select multiple items to add to your cart!",
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

class ItemSelect(discord.ui.Select):
    def __init__(self, user_id: int, country: str):
        self.user_id = user_id
        self.country = country
        
        items = MARKET_DATA[country]
        options = []
        
        for i, item in enumerate(items):
            options.append(
                discord.SelectOption(
                    label=item['name'],
                    description=item['description'],
                    value=str(i)
                )
            )
        
        super().__init__(
            placeholder="🛒 Select items to add to your cart (you can select multiple)...",
            min_values=1,
            max_values=len(options),  # Allow selecting multiple items
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        # Store selected items for quantity selection
        selected_items = []
        for item_index in self.values:
            item = MARKET_DATA[self.country][int(item_index)]
            selected_items.append(item)
        
        # Show quantity selection view
        quantity_view = QuantitySelectionView(self.user_id, self.country, selected_items)
        
        embed = discord.Embed(
            title="📦 Select Quantities",
            description="Choose the quantity for each selected item:",
            color=discord.Color.orange()
        )
        
        for item in selected_items:
            embed.add_field(
                name=f"${item['price']:.2f} - {item['name']}",
                value=item['description'],
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=quantity_view)

class QuantityModal(discord.ui.Modal):
    def __init__(self, user_id: int, country: str, selected_items: list):
        super().__init__(title="Enter Quantities")
        self.user_id = user_id
        self.country = country
        self.selected_items = selected_items
        
        # Add text inputs for each item (max 5 due to Discord limits)
        for i, item in enumerate(selected_items[:5]):
            text_input = discord.ui.TextInput(
                label=f"Quantity for {item['name']}",
                placeholder="Enter quantity (1-99)",
                default="1",
                min_length=1,
                max_length=2,
                required=True
            )
            self.add_item(text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        # Initialize user order if not exists
        if self.user_id not in user_orders:
            user_orders[self.user_id] = []
        
        added_items = []
        
        # Get quantities from text inputs
        for i, item in enumerate(self.selected_items):
            if i < len(self.children):
                try:
                    quantity_text = self.children[i].value.strip()
                    quantity = int(quantity_text)
                    
                    # Validate quantity
                    if quantity < 1:
                        quantity = 1
                    elif quantity > 99:
                        quantity = 99
                    
                    # Add items based on quantity
                    for _ in range(quantity):
                        user_orders[self.user_id].append(item)
                    added_items.append(f"**{item['name']}** x{quantity}")
                except ValueError:
                    # Default to 1 if invalid input
                    user_orders[self.user_id].append(item)
                    added_items.append(f"**{item['name']}** x1 (invalid input, defaulted to 1)")
        
        # Create confirmation embed
        embed = discord.Embed(
            title="✅ Items Added to Cart!",
            description=f"Successfully added items from **{self.country}**:",
            color=discord.Color.green()
        )
        
        for item_text in added_items:
            embed.add_field(
                name="📦 Added:",
                value=item_text,
                inline=False
            )
        
        embed.add_field(
            name="🛒 Next Steps:",
            value="• Browse other countries\n• View your cart\n• Continue shopping",
            inline=False
        )
        
        # Return to item selection view for this country
        item_view = ItemSelectionView(self.user_id, self.country)
        await interaction.response.edit_message(embed=embed, view=item_view)

class QuantitySelectionView(discord.ui.View):
    def __init__(self, user_id: int, country: str, selected_items: list):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.country = country
        self.selected_items = selected_items
    
    @discord.ui.button(label="Enter Quantities", style=discord.ButtonStyle.success, emoji="📝")
    async def enter_quantities(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        # Show quantity input modal
        modal = QuantityModal(self.user_id, self.country, self.selected_items)
        await interaction.response.send_modal(modal)

class CartManagementView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.user_id = user_id
        
        # Initialize user order if not exists
        if user_id not in user_orders:
            user_orders[user_id] = []
    
    @discord.ui.button(label="Continue Shopping", style=discord.ButtonStyle.primary, emoji="🌍")
    async def continue_shopping(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This market is not for you!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🌍 International Market",
            description="Welcome back! Choose a country to browse their unique items.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Available Countries",
            value="🇺🇸 United States\n🇯🇵 Japan\n🇮🇹 Italy\n🇫🇷 France\n🇲🇽 Mexico",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="1. Select a country from dropdown\n2. Choose multiple items to add to cart\n3. Enter quantities\n4. View cart and confirm order",
            inline=False
        )
        
        # Create country selection view
        view = CountryView(interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Clear Cart", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        user_orders[self.user_id] = []
        
        embed = discord.Embed(
            title="🗑️ Cart Cleared!",
            description="Your shopping cart has been cleared.",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="What's next?",
            value="You can start shopping again by clicking 'Continue Shopping' or use `/market` command.",
            inline=False
        )
        
        # Show continue shopping option
        continue_view = discord.ui.View(timeout=300)
        continue_button = discord.ui.Button(
            label="Start Shopping",
            style=discord.ButtonStyle.primary,
            emoji="🛍️"
        )
        
        async def start_shopping_callback(button_interaction):
            if button_interaction.user.id != self.user_id:
                await button_interaction.response.send_message("This market is not for you!", ephemeral=True)
                return
            
            market_embed = discord.Embed(
                title="🌍 International Market",
                description="Welcome to the market! Choose a country to browse their unique items.",
                color=discord.Color.gold()
            )
            
            market_embed.add_field(
                name="Available Countries",
                value="🇺🇸 United States\n🇯🇵 Japan\n🇮🇹 Italy\n🇫🇷 France\n🇲🇽 Mexico",
                inline=False
            )
            
            country_view = CountryView(button_interaction.user.id)
            await button_interaction.response.edit_message(embed=market_embed, view=country_view)
        
        continue_button.callback = start_shopping_callback
        continue_view.add_item(continue_button)
        
        await interaction.response.edit_message(embed=embed, view=continue_view)
    
    @discord.ui.button(label="Confirm Order", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        if not user_orders[self.user_id]:
            await interaction.response.send_message("Your cart is empty!", ephemeral=True)
            return
        
        # Calculate total and group items
        total = 0
        item_counts = {}
        
        for item in user_orders[self.user_id]:
            item_key = (item['name'], item['price'])
            if item_key in item_counts:
                item_counts[item_key]['count'] += 1
            else:
                item_counts[item_key] = {
                    'item': item,
                    'count': 1
                }
            total += item['price']
        
        # Create order summary
        embed = discord.Embed(
            title="🎉 Order Confirmed!",
            description="Thank you for your purchase! Here's your order summary:",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        for item_data in item_counts.values():
            item = item_data['item']
            count = item_data['count']
            subtotal = item['price'] * count
            
            if count > 1:
                embed.add_field(
                    name=f"${item['price']:.2f} x{count} = ${subtotal:.2f} - {item['name']}",
                    value=item['description'],
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"${item['price']:.2f} - {item['name']}",
                    value=item['description'],
                    inline=False
                )
        
        embed.add_field(
            name="💰 Final Total",
            value=f"**${total:.2f} USD**",
            inline=False
        )
        
        embed.add_field(
            name="📞 Order Status",
            value="Your order has been processed successfully!\nThank you for shopping with us! 🙏",
            inline=False
        )
        
        embed.set_footer(text=f"Order by {interaction.user.display_name}")
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clear the order after confirmation
        user_orders[self.user_id] = []

class MarketView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.user_id = user_id
        
        # Initialize user order if not exists
        if user_id not in user_orders:
            user_orders[user_id] = []
    
    @discord.ui.button(label="Clear Cart", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        user_orders[self.user_id] = []
        await interaction.response.send_message("🛒 Cart cleared!", ephemeral=True)
    
    @discord.ui.button(label="Confirm Order", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm_order(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        if not user_orders[self.user_id]:
            await interaction.response.send_message("Your cart is empty!", ephemeral=True)
            return
        
        # Calculate total and group items
        total = 0
        item_counts = {}
        
        for item in user_orders[self.user_id]:
            item_key = (item['name'], item['price'])
            if item_key in item_counts:
                item_counts[item_key]['count'] += 1
            else:
                item_counts[item_key] = {
                    'item': item,
                    'count': 1
                }
            total += item['price']
        
        # Create order summary
        embed = discord.Embed(
            title="🛒 Order Confirmed!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        
        for item_data in item_counts.values():
            item = item_data['item']
            count = item_data['count']
            subtotal = item['price'] * count
            
            if count > 1:
                embed.add_field(
                    name=f"${item['price']:.2f} x{count} = ${subtotal:.2f} - {item['name']}",
                    value=item['description'],
                    inline=False
                )
            else:
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

class CountryView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CountrySelect(user_id))

class ItemSelectionView(discord.ui.View):
    def __init__(self, user_id: int, country: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.country = country
        self.add_item(ItemSelect(user_id, country))
    
    @discord.ui.button(label="View Cart", style=discord.ButtonStyle.success, emoji="🛒")
    async def view_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your cart!", ephemeral=True)
            return
        
        if not user_orders.get(self.user_id, []):
            await interaction.response.send_message("Your cart is empty!", ephemeral=True)
            return
        
        # Show current cart contents WITH prices and total
        cart_items = user_orders[self.user_id]
        total = sum(item["price"] for item in cart_items)
        
        # Group items by name for display
        item_counts = {}
        for item in cart_items:
            item_key = (item['name'], item['price'])
            if item_key in item_counts:
                item_counts[item_key]['count'] += 1
            else:
                item_counts[item_key] = {
                    'item': item,
                    'count': 1
                }
        
        embed = discord.Embed(
            title="🛒 Your Shopping Cart",
            description="Review your items and total below.",
            color=discord.Color.blue()
        )
        
        for item_data in item_counts.values():
            item = item_data['item']
            count = item_data['count']
            subtotal = item['price'] * count
            
            if count > 1:
                embed.add_field(
                    name=f"${item['price']:.2f} x{count} = ${subtotal:.2f}",
                    value=f"**{item['name']}** - {item['description']}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"${item['price']:.2f}",
                    value=f"**{item['name']}** - {item['description']}",
                    inline=False
                )
        
        embed.add_field(
            name="💰 Current Total",
            value=f"**${total:.2f} USD**",
            inline=False
        )
        
        # Create cart management view with continue shopping
        cart_view = CartManagementView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=cart_view)
    
    @discord.ui.button(label="Browse Other Countries", style=discord.ButtonStyle.secondary, emoji="🌍")
    async def browse_countries(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This market is not for you!", ephemeral=True)
            return
        
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
            value="1. Select a country from dropdown\n2. Choose multiple items to add to cart\n3. View cart and confirm order",
            inline=False
        )
        
        # Create country selection view
        view = CountryView(interaction.user.id)
        await interaction.response.edit_message(embed=embed, view=view)

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
