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
    "Guns": [
        {"name": "Combat Pistol", "price": 54500, "description": "Standard sidearm for combat situations"},
        {"name": "MK2 Pistol", "price": 65000, "description": "Advanced pistol with improved accuracy"},
        {"name": "Glock18c", "price": 95000, "description": "High-rate automatic pistol"},
        {"name": "Micro SMG", "price": 99500, "description": "Compact submachine gun"},
        {"name": "Combat PDW", "price": 129500, "description": "Personal defense weapon"},
        {"name": "Shotgun", "price": 120000, "description": "Close-range combat shotgun"},
        {"name": "Ammo Pistol", "price": 1500, "description": "Ammunition for pistols"},
        {"name": "Ammo SMG", "price": 2000, "description": "Ammunition for submachine guns"},
        {"name": "Ammo Shotgun", "price": 2000, "description": "Ammunition for shotguns"}
    ],
    "Drugs": [
        {"name": "Pallet Coke", "price": 1050000, "description": "High-grade cocaine pallet"},
        {"name": "Pallet Weed", "price": 800000, "description": "Premium cannabis pallet"}
    ],
    "Heist Pack": [
        {"name": "Fleeca Heist Pack", "price": 60000, "description": "Equipment pack for bank heists"},
        {"name": "Bijoux Heist Pack", "price": 100000, "description": "Specialized jewelry store heist kit"},
        {"name": "Paleto Heist Pack", "price": 100000, "description": "Advanced heist equipment package"}
    ]
}

# Store user orders
user_orders = {}

class CategorySelect(discord.ui.Select):
    def __init__(self, user_id: int):
        self.user_id = user_id
        
        options = [
            discord.SelectOption(
                label="Guns",
                description="Firearms and ammunition",
                emoji="🔫",
                value="Guns"
            ),
            discord.SelectOption(
                label="Drugs",
                description="Narcotics and substances",
                emoji="💊",
                value="Drugs"
            ),
            discord.SelectOption(
                label="Heist Pack",
                description="Heist equipment packages",
                emoji="💰",
                value="Heist Pack"
            )
        ]
        
        super().__init__(
            placeholder="🛒 Choose a category to browse...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This market is not for you!", ephemeral=True)
            return
        
        category = self.values[0]
        
        embed = discord.Embed(
            title=f"🛍️ {category}",
            description="Select multiple items to add to your cart from the dropdown below!",
            color=discord.Color.blue()
        )
        
        # Create item selection view
        item_view = ItemSelectionView(self.user_id, category)
        await interaction.response.edit_message(embed=embed, view=item_view)

class ItemSelect(discord.ui.Select):
    def __init__(self, user_id: int, category: str):
        self.user_id = user_id
        self.category = category
        
        items = MARKET_DATA[category]
        options = []
        
        for i, item in enumerate(items):
            options.append(
                discord.SelectOption(
                    label=f"{item['name']} - ${item['price']:.2f}",
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
            item = MARKET_DATA[self.category][int(item_index)]
            selected_items.append(item)
        
        # Show quantity input modal directly
        modal = QuantityModal(self.user_id, self.category, selected_items)
        await interaction.response.send_modal(modal)

class QuantityModal(discord.ui.Modal):
    def __init__(self, user_id: int, category: str, selected_items: list):
        super().__init__(title="Enter Quantities")
        self.user_id = user_id
        self.category = category
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
            description=f"Successfully added items from **{self.category}**:",
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
            value="• Browse other categories\n• View your cart\n• Continue shopping",
            inline=False
        )
        
        # Return to item selection view for this category
        item_view = ItemSelectionView(self.user_id, self.category)
        await interaction.response.edit_message(embed=embed, view=item_view)



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
            title="🏪 Black Market",
            description="Welcome back! Choose a category to browse available items.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Available Categories",
            value="🔫 Guns\n💊 Drugs\n💰 Heist Pack",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="1. Select a category from dropdown\n2. Choose multiple items to add to cart\n3. Enter quantities\n4. View cart and confirm order",
            inline=False
        )
        
        # Create category selection view
        view = CategoryView(interaction.user.id)
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
        
        # Create cart display string for order confirmation
        order_display = ""
        for item_data in item_counts.values():
            item = item_data['item']
            count = item_data['count']
            subtotal = item['price'] * count
            order_display += f"- {count} {item['name']} : ${subtotal:.2f}\n"
        
        order_display += f"\nTotal : ${total:.2f}"
        
        # Create order summary
        embed = discord.Embed(
            title="🎉 Order Confirmed!",
            description=f"Thank you for your purchase! Here's your order summary:\n\n{order_display}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
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

class CategoryView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.add_item(CategorySelect(user_id))

class ItemSelectionView(discord.ui.View):
    def __init__(self, user_id: int, category: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.category = category
        self.add_item(ItemSelect(user_id, category))
    
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
        
        # Create cart display string
        cart_display = ""
        for item_data in item_counts.values():
            item = item_data['item']
            count = item_data['count']
            subtotal = item['price'] * count
            cart_display += f"- {count} {item['name']} : ${subtotal:.2f}\n"
        
        cart_display += f"\nTotal : ${total:.2f}"
        
        embed = discord.Embed(
            title="🛒 Your Shopping Cart",
            description=cart_display,
            color=discord.Color.blue()
        )
        
        # Create cart management view with continue shopping
        cart_view = CartManagementView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=cart_view)
    
    @discord.ui.button(label="Browse Other Categories", style=discord.ButtonStyle.secondary, emoji="🏪")
    async def browse_categories(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This market is not for you!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏪 Black Market",
            description="Welcome to the black market! Choose a category to browse available items.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Available Categories",
            value="🔫 Guns\n💊 Drugs\n💰 Heist Pack",
            inline=False
        )
        
        embed.add_field(
            name="How it works",
            value="1. Select a category from dropdown\n2. Choose multiple items to add to cart\n3. View cart and confirm order",
            inline=False
        )
        
        # Create category selection view
        view = CategoryView(interaction.user.id)
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
@bot.tree.command(name="market", description="Open the black market to browse guns, drugs, and heist packs")
async def market(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏪 Black Market",
        description="Welcome to the black market! Choose a category to browse available items.",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="Available Categories",
        value="🔫 Guns\n💊 Drugs\n💰 Heist Pack",
        inline=False
    )
    
    embed.add_field(
        name="How it works",
        value="1. Select a category\n2. Choose items to add to cart\n3. View cart and confirm order",
        inline=False
    )
    
    # Create category selection view
    view = CategoryView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view)

# A simple slash command: /ping
@bot.tree.command(name="ping", description="Replies with Pong and latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    bot.run(TOKEN)
