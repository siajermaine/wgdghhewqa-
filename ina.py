import io
import os
import discord
import asyncio
from discord.ext import commands, tasks
from discord import app_commands, Embed, File
from dotenv import load_dotenv
from datetime import datetime, time, timedelta
import pytz
import aiohttp
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Get the bot token from the environment
TOKEN = os.getenv("BOT_TOKEN")  # Put your bot token in the .env file
GUILD_ID = int(os.getenv("GUILD_ID"))  # Set your guild ID
ROLE_ID = int(os.getenv("ROLE_ID"))  # Role ID that can use the command and dropdown
QUEUE_CHANNEL_ID = int(os.getenv("QUEUE_CHANNEL_ID"))  # Queue channel ID
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Specify the target channel ID

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent for !vouch command
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True  # Required to manage roles

# Set up the bot with both intents
bot = commands.Bot(command_prefix="/", intents=intents)

autoresponses = {}  # Store autoresponses in memory
MAX_AUTORESPONSES = 10

# Dictionary to store AFK status
afk_users = {}
reaction_roles = {}  # Stores reaction-role mappings

# Scheduled Messages (from the first code)
SCHEDULED_HOURS = [(8, 0), (21, 0)]  # Specify the hours in Manila Time (14:10 and 14:11)

MESSAGES = {
    (8, 0): """
:¨ ·.· ¨:
 `· . shop is now open <:cinna_shine:1335109271620292639> 

♡ ping <@&1330392036712386571> for fast replies
♡ no rushing of orders & no rude buyers 
♡ feel free to ask for inquiries [here](https://discord.com/channels/1330329576722923620/1330340000931254354)
♡ ready to order? order [here](https://discord.com/channels/1330329576722923620/1332153820838629376)

||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||||||||||
<@&1335091701282373708> @everyone @here""",
    (21, 0): """
:¨ ·.· ¨:
 `· . shop is now closed <:cinna_shine:1335109271620292639> 

♡ thank you for your support today!
♡ feel free to ask for inquiries [here](https://discord.com/channels/1330329576722923620/1330340000931254354)
♡ if you still want to order, order [here](https://discord.com/channels/1330329576722923620/1332153820838629376)
♡ please expect late replies 

||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||||||||||
<@&1335091701282373708> @everyone @here"""
}

statuses = [
    "cinna shop",
    "cinnamoroll",
    "by Sia",
    "cinna helper",
    "cinnamoroll shop"
]

# Function to calculate the next scheduled time
def time_until_next_run():
    tz = pytz.timezone("Asia/Manila")
    now = datetime.now(tz)
    next_run = min((datetime.combine(now.date(), time(h, m), tz) for h, m in SCHEDULED_HOURS if now < datetime.combine(now.date(), time(h, m), tz)), default=None)
    if next_run is None:
        next_run = datetime.combine(now.date() + timedelta(days=1), time(*SCHEDULED_HOURS[0]), tz)
    return (next_run - now).total_seconds()

async def change_status():
    i = 0
    while True:
        # Rotate the status every 10 seconds
        await bot.change_presence(activity=discord.Game(name=statuses[i]))
        i = (i + 1) % len(statuses)  # Loop back to the first status
        await asyncio.sleep(60)  # Wait 60 seconds before changing status
        
@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)  # Define guild
        await bot.tree.sync(guild=guild)  # Sync only for this guild (fastest method)
        bot.loop.create_task(change_status())
        
        # Fetch and print all registered commands
        commands = await bot.tree.fetch_commands(guild=guild)
        print(f"✅ Synced commands: {[cmd.name for cmd in commands]}")

        print(f"🤖 {bot.user} is online and ready!")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    
    schedule_purge.start()  # Start the scheduled message task

@tasks.loop(seconds=60)
async def schedule_purge():
    now = datetime.now(pytz.timezone("Asia/Manila"))
    if (now.hour, now.minute) in MESSAGES:
        await purge_and_send_message()

async def purge_and_send_message():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Error: Could not find channel with ID {CHANNEL_ID}")
        return
    now = datetime.now(pytz.timezone("Asia/Manila"))
    msg = MESSAGES.get((now.hour, now.minute))
    if msg:
        try:
            await channel.purge()  # Purge previous messages
            await channel.send(msg)  # Send new message
            print("Messages purged and new message sent.")
        except Exception as e:
            print(f"Error sending message: {e}")

# Set AFK status
@bot.tree.command(name="afk", description="Set your AFK status.")
@app_commands.describe(message="The message to display when someone mentions you.")
async def afk(interaction: discord.Interaction, message: str = "AFK"):
    user = interaction.user
    afk_users[user.id] = message  # Store AFK status
    await interaction.response.send_message(f"{user.mention} is now AFK: {message}")

# Check if an AFK user is mentioned
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    # Debug: Print detected message
    print(f"Message received: {message.content}")

    mentioned_afk_users = [user for user in message.mentions if user.id in afk_users]
    
    if mentioned_afk_users:
        afk_replies = [f"{user.mention} is AFK: {afk_users[user.id]}" for user in mentioned_afk_users]
        await message.channel.send("\n".join(afk_replies))

    # Autoresponse functionality
    if message.content.lower() in autoresponses:
        await message.channel.send(autoresponses[message.content.lower()])

    await bot.process_commands(message)  # Ensure bot can still process commands

# Add an autoresponse
@bot.tree.command(name="addauto", description="Add an autoresponse trigger and response.")
async def addauto(interaction: discord.Interaction, trigger: str, response: str):
    if len(autoresponses) >= MAX_AUTORESPONSES:
        await interaction.response.send_message('You have reached the maximum of 10 autoresponses.', ephemeral=True)
        return
    
    autoresponses[trigger.lower()] = response
    await interaction.response.send_message(f'Autoresponse added: "{trigger}" -> "{response}"')

# Delete an autoresponse
@bot.tree.command(name="delauto", description="Delete an autoresponse trigger.")
async def delauto(interaction: discord.Interaction, trigger: str):
    if trigger.lower() in autoresponses:
        del autoresponses[trigger.lower()]
        await interaction.response.send_message(f'Autoresponse "{trigger}" deleted.')
    else:
        await interaction.response.send_message('Trigger not found.', ephemeral=True)

# Order command and views
@bot.tree.command(name="order", description="Place an order")
async def order(interaction: discord.Interaction):
    embed = discord.Embed(title="REMINDER", color=0x2b2d31,
                          description="⠀‧⠀Ignorance of our rules is not an excuse\n⠀‧⠀Strictly no rush orders\n⠀‧⠀Kindly wait for our staff to assist you.\n\nChoose below an item you will buy\nSubmit another /order if an error occurred")
    
    view = OrderSelectView()
    await interaction.response.send_message(embed=embed, view=view)

class OrderSelectView(discord.ui.View):
    @discord.ui.select(
        placeholder="Choose a product category",
        options=[
            discord.SelectOption(label="Discord Items", description="N-tro, Server Boost, Decors", value="discord_items"),
            discord.SelectOption(label="Game Credits", description="VP, RP, ML Dias, Genesis Crystals, and more.", value="game_credits"),
            discord.SelectOption(label="Commissions", description="Custom commissions", value="commissions")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.send_modal(OrderForm(select.values[0]))

class OrderForm(discord.ui.Modal, title="Order Form"):
    username = discord.ui.TextInput(label="Your Username", placeholder="your username", required=True)
    
    def __init__(self, category):
        super().__init__()
        self.category = category
        
        if category == "discord_items":
            self.add_item(discord.ui.TextInput(label="Item", placeholder="the item that you want to order", required=True))
            self.add_item(discord.ui.TextInput(label="Quantity", placeholder="the quantity of your order", required=True))
            self.add_item(discord.ui.TextInput(label="Permanent Link (For Server Boost Only)", placeholder="optional", required=False))
        elif category == "game_credits":
            self.add_item(discord.ui.TextInput(label="Game Credits", placeholder="the game credits that you want to order", required=True))
            self.add_item(discord.ui.TextInput(label="Quantity", placeholder="the quantity of your order", required=True))
            self.add_item(discord.ui.TextInput(label="UID/IGN", placeholder="your UID/IGN", required=True))
        elif category == "commissions":
            self.add_item(discord.ui.TextInput(label="Commission", placeholder="the commission that you want to order", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="ORDER CONFIRMATION", color=0x2b2d31)
        embed.description = f"⠀‧⠀{self.username.value}\n⠀‧⠀{self.children[1].value}\n⠀‧⠀{self.children[2].value if len(self.children) > 2 else 'N/A'}"
        
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view)

class ConfirmView(discord.ui.View):
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="ORDER CONFIRMED", color=0x2b2d31, description=interaction.message.embeds[0].description)
        view = PaymentView()
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.channel.edit(name=f"{interaction.user.name}・{embed.description.split('\n')[1].strip()}")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()

class PaymentView(discord.ui.View):
    @discord.ui.button(label="Payment", style=discord.ButtonStyle.primary)
    async def payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="PAYMENT METHOD", color=0x2b2d31,
                              description="**notes:**\n⠀‧⠀double-check the amount to be paid\n⠀‧⠀must send the receipt\n⠀‧⠀no receipt = no transaction")
        embed.set_image(url="https://media.discordapp.net/attachments/1330394204643393607/1333048828479275050/Add_a_subheading.png")
        view = CopyNumberView()
        await interaction.response.send_message(embed=embed, view=view)

class CopyNumberView(discord.ui.View):
    @discord.ui.button(label="Copy Number", style=discord.ButtonStyle.secondary)
    async def copy_number(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("**0929-796-2515**", ephemeral=True)

# Vouch command
@bot.tree.command(name="vouch", description="Vouch with a message and an attachment")
async def vouch(interaction: discord.Interaction, message: str, attachment: discord.Attachment):
    await interaction.response.defer()  # Defer the response to prevent timeout

    author = interaction.user
    
    # Download the image file
    async with aiohttp.ClientSession() as session:
        async with session.get(attachment.url) as response:
            file = await response.read()

    # Send the vouch message with the attachment
    await interaction.followup.send(
        content=f"{author.mention} vouched: {message}",  # Send the vouch message
        file=discord.File(io.BytesIO(file), filename=attachment.filename)  # Send the downloaded file
    )

class StatusDropdown(discord.ui.Select):
    def __init__(self, message):
        self.message = message
        options = [
            discord.SelectOption(label="Paid", value="Paid"),
            discord.SelectOption(label="Noted", value="Noted"),
            discord.SelectOption(label="Processing", value="Processing"),
            discord.SelectOption(label="Completed", value="Completed"),
        ]
        super().__init__(placeholder="Update Status", options=options)

    async def callback(self, interaction: discord.Interaction):
        if ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("You don't have permission to change the status.", ephemeral=True)

        new_status = self.values[0]
        content = self.message.content.split("\n")
        content[-1] = f"Status: {new_status}"
        await self.message.edit(content="\n".join(content))

        if new_status == "Completed":
            self.view.clear_items()  # Remove dropdown
            await self.message.edit(view=self.view)  # Update message to remove dropdown

        await interaction.response.send_message(f"Status updated to **{new_status}**", ephemeral=True)

class StatusView(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.add_item(StatusDropdown(message))

# Slash command: Add order to queue
@bot.tree.command(name="queue", description="Add an order to the queue", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    buyer="Select the buyer", item="Enter the item", quantity="Enter the quantity",
    channel="Select the order channel", price_paid="Enter the paid price", payment_meth="Enter the payment method"
)
@app_commands.checks.has_role(ROLE_ID)
async def queue(interaction: discord.Interaction, buyer: discord.Member, item: str, quantity: int, channel: discord.TextChannel, price_paid: int, payment_meth: str):
    queue_channel = bot.get_channel(QUEUE_CHANNEL_ID)
    if not queue_channel:
        return await interaction.response.send_message("Queue channel not found.", ephemeral=True)

    formatted_message = f"""
୨ৎ⠀{channel.mention}﹕ {buyer.mention}
୭⠀ ( {quantity} ) {item}
ʚɞ⠀  ₱{price_paid} ﹕  ♡⠀({payment_meth})
Status: 
"""
    queue_message = await queue_channel.send(formatted_message)
    await queue_message.edit(view=StatusView(queue_message))
    
    confirmation_message = f"""
**Status: Payment Received~**
Hello there, {buyer.mention} *!* Please take note that processing orders might take time depending on your order. Thank you~
"""
    await interaction.channel.send(confirmation_message)
    await interaction.response.send_message("Queue entry added successfully!", ephemeral=True)

@queue.error
async def queue_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

@bot.tree.command(name="reactionroleadd", description="Add a reaction role to an existing message.")
@app_commands.describe(
    emoji="The emoji for the reaction role",
    role="The role to assign",
    message_id="The message ID to apply the reaction role",
    channel="Optional: The channel where the message is located"
)
@app_commands.checks.has_role(ROLE_ID)
async def reactionroleadd(interaction: discord.Interaction, emoji: str, role: discord.Role, message_id: str, channel: discord.TextChannel = None):
    """Adds a reaction role to an existing message."""
    await interaction.response.defer(ephemeral=True)  # Acknowledge command

    # Check if bot has 'Manage Roles' permission
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.followup.send("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    # Ensure the bot's role is higher than the role it is assigning/removing
    if interaction.guild.me.top_role.position <= role.position:
        await interaction.followup.send(f"❌ My role needs to be higher than {role.name} to assign/remove it.", ephemeral=True)
        return

    channel = channel or interaction.channel  # Default to the command channel
    try:
        message = await channel.fetch_message(int(message_id))
    except discord.NotFound:
        await interaction.followup.send("❌ Message not found. Check the message ID.", ephemeral=True)
        return
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to access this message.", ephemeral=True)
        return

    await message.add_reaction(emoji)
    reaction_roles[message.id] = {"emoji": emoji, "role_id": role.id}
    await interaction.followup.send(f"✅ Reaction role added! {emoji} → {role.mention} on [this message]({message.jump_url})", ephemeral=True)

@bot.tree.command(name="reactionroleremove", description="Remove a reaction role from an existing message.")
@app_commands.describe(
    message_id="The message ID from which the reaction role should be removed"
)
@app_commands.checks.has_role(ROLE_ID)
async def reactionroleremove(interaction: discord.Interaction, message_id: str):
    """Removes a reaction role from an existing message."""
    await interaction.response.defer(ephemeral=True)  # Acknowledge command

    # Check if bot has 'Manage Roles' permission
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.followup.send("❌ I don't have permission to manage roles!", ephemeral=True)
        return

    message_id = int(message_id)
    
    if message_id in reaction_roles:
        del reaction_roles[message_id]
        await interaction.followup.send(f"✅ Reaction role removed from message ID `{message_id}`.", ephemeral=True)
    else:
        await interaction.followup.send("❌ No reaction role found for this message ID.", ephemeral=True)


@bot.event
async def on_raw_reaction_add(payload):
    """Toggles role when a user reacts."""
    if payload.message_id in reaction_roles:
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        role_id = reaction_roles[payload.message_id]["role_id"]
        emoji = reaction_roles[payload.message_id]["emoji"]

        if str(payload.emoji) == emoji:
            member = guild.get_member(payload.user_id)
            if member:
                role = guild.get_role(role_id)

                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        print(f"❌ Removed role {role.name} from {member.display_name}")
                    except discord.Forbidden:
                        print(f"❌ I don't have permission to remove {role.name} from {member.display_name}")
                else:
                    try:
                        await member.add_roles(role)
                        print(f"✅ Added role {role.name} to {member.display_name}")
                    except discord.Forbidden:
                        print(f"❌ I don't have permission to add {role.name} to {member.display_name}")


@bot.event
async def on_raw_reaction_remove(payload):
    """Toggles role when a user unreacts."""
    if payload.message_id in reaction_roles:
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return

        role_id = reaction_roles[payload.message_id]["role_id"]
        emoji = reaction_roles[payload.message_id]["emoji"]

        if str(payload.emoji) == emoji:
            member = guild.get_member(payload.user_id)
            if member:
                role = guild.get_role(role_id)

                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        print(f"❌ Removed role {role.name} from {member.display_name}")
                    except discord.Forbidden:
                        print(f"❌ I don't have permission to remove {role.name} from {member.display_name}")
                else:
                    try:
                        await member.add_roles(role)
                        print(f"✅ Added role {role.name} to {member.display_name}")
                    except discord.Forbidden:
                        print(f"❌ I don't have permission to add {role.name} to {member.display_name}")

@reactionroleadd.error
@reactionroleremove.error
async def reaction_role_error(interaction: discord.Interaction, error: Exception):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command. You need the appropriate role.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("An error occurred while processing your request.", ephemeral=True)

# Slash command: Say a custom message
@bot.tree.command(name="say", description="Make the bot say a message in the same channel.")
@app_commands.describe(message="The message you want the bot to send.")
async def say(interaction: discord.Interaction, message: str):
    """Sends a custom message in the channel where the command was used."""
    # Check if the user has the required role (optional)
    if ROLE_ID not in [role.id for role in interaction.user.roles]:
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
    
    # Send the message in the same channel
    await interaction.response.send_message(message)

@bot.tree.command(name="say", description="Sends a message to the channel")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Sending your message...")

    # Send the message to the same channel where the command was issued
    await interaction.channel.send(message)

# Run the bot with the token from the .env file
bot.run(TOKEN)
