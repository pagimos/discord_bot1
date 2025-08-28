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

# Ghost shop command: /ghost with country selection
@bot.tree.command(name="ghost", description="Shows countries with mysterious items from the ghost shop.")
async def ghost(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # Initialize user selection if not exists
    if user_id not in ghost_selections:
        ghost_selections[user_id] = {"country": None, "items": []}
    
    # Create embed for the ghost shop
    embed = discord.Embed(
        title="👻 Ghost Shop - Choose Your Country",
        description="Welcome to the ethereal marketplace! Select a country to see its mysterious items:",
        color=0x8B008B  # Dark magenta for spooky theme
    )
    
    # Add 5 countries
    countries = [
        ("🇯🇵 Japan", "Land of the rising sun and ancient secrets"),
        ("🇫🇷 France", "Home of enchanted wines and mystical artifacts"),
        ("🇪🇬 Egypt", "Realm of pharaohs and pyramid mysteries"),
        ("🇧🇷 Brazil", "Land of Amazonian crystals and jungle magic"),
        ("🇷🇺 Russia", "Home of nesting dolls with hidden powers")
    ]
    
    for i, (country, description) in enumerate(countries, 1):
        is_selected = ghost_selections[user_id]["country"] == i
        status = "✅ SELECTED" if is_selected else ""
        embed.add_field(
            name=f"{i}. {country}",
            value=f"{description}{' ' + status if status else ''}",
            inline=False
        )
    
    # Show current selection info
    if ghost_selections[user_id]["country"]:
        country_name = countries[ghost_selections[user_id]["country"] - 1][0]
        embed.add_field(
            name="🌍 Selected Country",
            value=f"{country_name}",
            inline=False
        )
    
    if ghost_selections[user_id]["items"]:
        embed.add_field(
            name="🛒 Selected Items",
            value=f"Items: {len(ghost_selections[user_id]['items'])}/3",
            inline=False
        )
    
    embed.set_footer(text="💀 Select a country first, then choose items!")
    
    # Create interactive view
    view = CountrySelectionView(user_id)
    
    await interaction.response.send_message(embed=embed, view=view)

# Country selection view
class CountrySelectionView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.user_id = user_id
    
    @discord.ui.select(
        placeholder="Choose a country...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="1. Japan", value="1", description="Land of the rising sun and ancient secrets"),
            discord.SelectOption(label="2. France", value="2", description="Home of enchanted wines and mystical artifacts"),
            discord.SelectOption(label="3. Egypt", value="3", description="Realm of pharaohs and pyramid mysteries"),
            discord.SelectOption(label="4. Brazil", value="4", description="Land of Amazonian crystals and jungle magic"),
            discord.SelectOption(label="5. Russia", value="5", description="Home of nesting dolls with hidden powers")
        ]
    )
    async def select_country(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            # Check if this is the correct user
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
                return
            
            country_number = int(select.value)
            print(f"User {self.user_id} selected country {country_number}")
            
            # Initialize user selection if not exists
            if self.user_id not in ghost_selections:
                ghost_selections[self.user_id] = {"country": None, "items": []}
            
            # Set selected country and clear previous items
            ghost_selections[self.user_id]["country"] = country_number
            ghost_selections[self.user_id]["items"] = []
            
            # Show items for selected country
            await self.show_country_items(interaction, country_number)
        except Exception as e:
            print(f"Error in select_country: {e}")
            logging.error(f"Country selection error for user {self.user_id}: {e}")
            await interaction.response.send_message("❌ An error occurred while processing your country selection. Please try again.", ephemeral=True)
    
    async def show_country_items(self, interaction: discord.Interaction, country_number: int):
        try:
            # Get items for selected country
            country_items = self.get_country_items(country_number)
            
            embed = discord.Embed(
                title=f"👻 {self.get_country_name(country_number)} - Choose Your Items",
                description=f"✅ Selected country {country_number}! Select up to 3 items from this country:",
                color=0x4169E1
            )
            
            for i, (item_name, price, description) in enumerate(country_items, 1):
                embed.add_field(
                    name=f"{i}. {item_name}",
                    value=f"{description}\n**Price: {price}**",
                    inline=False
                )
            
            embed.set_footer(text="💀 Select up to 3 items, then confirm your purchase!")
            
            # Create item selection view
            item_view = ItemSelectionView(self.user_id, country_number)
            
            # Update the original message with the new embed and view
            await interaction.response.edit_message(embed=embed, view=item_view)
        except Exception as e:
            print(f"Error in show_country_items: {e}")
            logging.error(f"Error showing country items for user {self.user_id}, country {country_number}: {e}")
            await interaction.response.send_message("❌ An error occurred while showing country items. Please try again.", ephemeral=True)
    
    def get_country_name(self, country_number: int):
        countries = ["Japan", "France", "Egypt", "Brazil", "Russia"]
        return countries[country_number - 1]
    
    def get_country_items(self, country_number: int):
        all_items = {
            1: [  # Japan
                ("Mysterious Katana", "$150", "A legendary blade with unknown powers"),
                ("Ghost Lantern", "$75", "Illuminates the path to the spirit world"),
                ("Samurai Armor", "$200", "Protects against supernatural attacks")
            ],
            2: [  # France
                ("Enchanted Wine", "$25", "A vintage bottle with magical properties"),
                ("Eiffel Tower Charm", "$50", "Brings Parisian magic wherever you go"),
                ("Royal Crown", "$300", "Worn by ghostly French monarchs")
            ],
            3: [  # Egypt
                ("Pyramid Amulet", "$89", "Contains ancient pharaoh magic"),
                ("Sphinx Statue", "$120", "Guards your secrets with mystical power"),
                ("Mummy Bandages", "$45", "Wraps you in protective energy")
            ],
            4: [  # Brazil
                ("Amazon Crystal", "$120", "Harnesses the power of the rainforest"),
                ("Carnival Mask", "$80", "Transforms you during celebrations"),
                ("Jungle Totem", "$160", "Connects you to nature spirits")
            ],
            5: [  # Russia
                ("Nesting Doll", "$1800", "Contains multiple layers of mystery"),
                ("Winter Frost Gem", "$250", "Freezes time around you"),
                ("Ballet Slippers", "$95", "Dance through dimensions")
            ]
        }
        return all_items.get(country_number, [])

# Item selection view
class ItemSelectionView(discord.ui.View):
    def __init__(self, user_id: int, country_number: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.country_number = country_number
        
        # Dynamically generate select options based on country items
        country_items = self.get_country_items(country_number)
        select_options = []
        
        for i, (item_name, price, description) in enumerate(country_items, 1):
            # Truncate long item names to fit Discord's label limit
            label = f"{i}. {item_name[:20]}{'...' if len(item_name) > 20 else ''}"
            select_options.append(
                discord.SelectOption(
                    label=label,
                    value=str(i),
                    description=f"{price} - {description[:50]}{'...' if len(description) > 50 else ''}"
                )
            )
        
        # Create the select menu with the options
        self.add_item(discord.ui.Select(
            placeholder="Choose items (up to 3)...",
            min_values=1,
            max_values=3,
            options=select_options,
            custom_id="item_selection"
        ))
    
    async def select_items(self, interaction: discord.Interaction, select_data: dict):
        try:
            # Handle the actual selection
            selected_items = [int(value) for value in select_data.get("values", [])]
            print(f"User {self.user_id} selected items: {selected_items}")
            
            # Initialize user selection if not exists
            if self.user_id not in ghost_selections:
                ghost_selections[self.user_id] = {"country": None, "items": []}
            
            # Update selected items
            ghost_selections[self.user_id]["items"] = selected_items
            
            # Show selection summary
            await self.show_selection_summary(interaction)
        except Exception as e:
            print(f"Error in select_items: {e}")
            logging.error(f"Error in item selection for user {self.user_id}, country {self.country_number}: {e}")
            await interaction.response.send_message("❌ An error occurred while processing your selection. Please try again.", ephemeral=True)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Check if this is the correct user for all interactions
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return False
        
        # Handle select menu interactions
        if interaction.data.get("custom_id") == "item_selection":
            await self.select_items(interaction, interaction.data)
            return False  # We've handled the interaction
        
        return True
    
    @discord.ui.button(label="🛒 Confirm Purchase", style=discord.ButtonStyle.success)
    async def confirm_purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm_purchase_action(interaction)
    
    @discord.ui.button(label="🗑️ Clear Selection", style=discord.ButtonStyle.danger)
    async def clear_selection(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.clear_selection_action(interaction)
    
    async def confirm_purchase_action(self, interaction: discord.Interaction):
        # Check if this is the correct user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return
        
        if not ghost_selections.get(self.user_id, {}).get("items"):
            await interaction.response.send_message("❌ You haven't selected any items yet!", ephemeral=True)
            return
        
        # Get selected items
        country_items = self.get_country_items(self.country_number)
        selected_item_numbers = ghost_selections[self.user_id]["items"]
        selected_items = [country_items[i-1] for i in selected_item_numbers]
        
        # Calculate total
        total_dollars = sum(int(item[1].replace("$", "")) for item in selected_items)
        country_name = self.get_country_name(self.country_number)
        
        # Create confirmation embed
        embed = discord.Embed(
            title="🎉 Purchase Confirmed!",
            description=f"Congratulations {interaction.user.mention}! Your {country_name} items have been purchased.",
            color=0x00FF00
        )
        
        for item_name, price, description in selected_items:
            embed.add_field(
                name=f"{item_name} - {price}",
                value=description,
                inline=False
            )
        
        embed.add_field(
            name="💰 Total Spent",
            value=f"**Total in Dollars: ${total_dollars}**",
            inline=False
        )
        
        embed.set_footer(text="✨ Your items will be delivered to your ghost mailbox soon!")
        
        # Clear user selection after purchase
        ghost_selections[self.user_id] = {"country": None, "items": []}
        
        # Disable all buttons after purchase
        for child in self.children:
            child.disabled = True
        
        # Update the message with disabled buttons and show confirmation
        await interaction.response.edit_message(view=self, embed=embed)
    
    async def clear_selection_action(self, interaction: discord.Interaction):
        # Check if this is the correct user
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop is not for you! Use /ghost to create your own.", ephemeral=True)
            return
        
        # Clear selection
        if self.user_id in ghost_selections:
            ghost_selections[self.user_id]["items"] = []
        
        await interaction.response.send_message("🗑️ Your item selection has been cleared!", ephemeral=True)
    
    async def show_selection_summary(self, interaction: discord.Interaction):
        country_items = self.get_country_items(self.country_number)
        selected_item_numbers = ghost_selections[self.user_id]["items"]
        selected_items = [country_items[i-1] for i in selected_item_numbers]
        
        total_dollars = sum(int(item[1].replace("$", "")) for item in selected_items)
        
        embed = discord.Embed(
            title="🛒 Your Selection Summary",
            description=f"✅ Selected {len(selected_items)} items from {self.get_country_name(self.country_number)}!",
            color=0x4169E1
        )
        
        for item_name, price, description in selected_items:
            embed.add_field(
                name=f"{item_name} - {price}",
                value=description,
                inline=False
            )
        
        embed.add_field(
            name="💰 Total",
            value=f"**Total in Dollars: ${total_dollars}**",
            inline=False
        )
        
        embed.set_footer(text="Click Confirm Purchase to complete your order!")
        
        # Update the current message with the selection summary
        await interaction.response.edit_message(embed=embed)
    
    def get_country_name(self, country_number: int):
        countries = ["Japan", "France", "Egypt", "Brazil", "Russia"]
        return countries[country_number - 1]
    
    def get_country_items(self, country_number: int):
        all_items = {
            1: [  # Japan
                ("Mysterious Katana", "$150", "A legendary blade with unknown powers"),
                ("Ghost Lantern", "$75", "Illuminates the path to the spirit world"),
                ("Samurai Armor", "$200", "Protects against supernatural attacks")
            ],
            2: [  # France
                ("Enchanted Wine", "$25", "A vintage bottle with magical properties"),
                ("Eiffel Tower Charm", "$50", "Brings Parisian magic wherever you go"),
                ("Royal Crown", "$300", "Worn by ghostly French monarchs")
            ],
            3: [  # Egypt
                ("Pyramid Amulet", "$89", "Contains ancient pharaoh magic"),
                ("Sphinx Statue", "$120", "Guards your secrets with mystical power"),
                ("Mummy Bandages", "$45", "Wraps you in protective energy")
            ],
            4: [  # Brazil
                ("Amazon Crystal", "$120", "Harnesses the power of the rainforest"),
                ("Carnival Mask", "$80", "Transforms you during celebrations"),
                ("Jungle Totem", "$160", "Connects you to nature spirits")
            ],
            5: [  # Russia
                ("Nesting Doll", "$1800", "Contains multiple layers of mystery"),
                ("Winter Frost Gem", "$250", "Freezes time around you"),
                ("Ballet Slippers", "$95", "Dance through dimensions")
            ]
        }
        return all_items.get(country_number, [])

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
