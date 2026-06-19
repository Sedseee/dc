import discord
import os
import json
import logging # <-- NEW: Added for debugging
import sys     # <-- NEW: Added for debugging
from discord.ext import commands
from discord import app_commands

# ==========================================
# 0. HONEYPOT DATABASE SETUP
# ==========================================

HONEYPOT_FILE = "honeypots.json"

def load_honeypots():
    """Loads the list of honeypot channel IDs from a JSON file."""
    try:
        with open(HONEYPOT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_honeypots(data):
    """Saves the honeypot channel IDs to a JSON file."""
    with open(HONEYPOT_FILE, "w") as f:
        json.dump(data, f)

# ==========================================
# 1. DROPDOWN & BUTTON SETUP
# ==========================================

# ⚠️ REPLACE THIS LINK WITH YOUR ACTUAL CLOUDFLARE PAGES URL
VERIFICATION_URL = "https://sedse.pages.dev"

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Verify with Discord",
            url=VERIFICATION_URL,
            style=discord.ButtonStyle.link,
            emoji="🛡️"
        ))

class JJSDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Sedse JJS Script", 
                description="Click here for the Sedse JJS Script", 
                emoji="📜",
                value="sedse_jjs"
            ),
            discord.SelectOption(
                label="JJS Piano", 
                description="Click here for info on JJS Piano", 
                emoji="🎹",
                value="jjs_piano"
            ),
            discord.SelectOption(
                label="JJS Piano Open Source", 
                description="Click here for info on the Open Source version", 
                emoji="💻",
                value="jjs_piano_os"
            )
        ]
        super().__init__(
            placeholder="Choose a script...", 
            min_values=1, 
            max_values=1, 
            options=options, 
            custom_id="persistent_jjs_dropdown" 
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "sedse_jjs":
            response_text = "Here is the **Sedse JJS Script**!:\n`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/SedseXD/sedsejjs/refs/heads/main/sedse's%20scripts\"))()`"
        elif self.values[0] == "jjs_piano":
            response_text = "Here is the information and link for **JJS Piano**!:\n `loadstring(game:HttpGet('https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua'))()`"
        elif self.values[0] == "jjs_piano_os":
            response_text = "Here is the GitHub link and info for **JJS Piano Open Source**!: https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua"

        await interaction.response.send_message(response_text, ephemeral=True)

class JJSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JJSDropdown())

# --- NEW: HONEYPOT PANEL VIEW ---
class HoneypotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enable Honeypot", style=discord.ButtonStyle.green, custom_id="hp_enable_btn", emoji="🕸️")
    async def enable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only administrators can manage honeypots.", ephemeral=True)
        
        if interaction.channel.id not in bot.honeypot_channels:
            bot.honeypot_channels.append(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("✅ **Honeypot Enabled!** Anyone (except admins) sending an image here will be softbanned.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ This channel is already a honeypot.", ephemeral=True)

    @discord.ui.button(label="Disable Honeypot", style=discord.ButtonStyle.red, custom_id="hp_disable_btn", emoji="🛑")
    async def disable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only administrators can manage honeypots.", ephemeral=True)
        
        if interaction.channel.id in bot.honeypot_channels:
            bot.honeypot_channels.remove(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("🛑 **Honeypot Disabled!** Members can now safely send images here.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ This channel is not a honeypot.", ephemeral=True)

# ==========================================
# 2. BOT CLASS
# ==========================================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True # Ensure bot can see members to ban them properly
        super().__init__(command_prefix="!", intents=intents)
        
        # Load active honeypot channels into the bot's memory
        self.honeypot_channels = load_honeypots()

    async def setup_hook(self):
        # Keeps buttons active after bot restarts
        self.add_view(JJSView())
        self.add_view(VerifyView())
        self.add_view(HoneypotView()) # Keeps the honeypot panel persistent
        
        print("Attempting to auto-sync slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"✅ Auto-sync successful! Registered {len(synced)} command(s).")
        except Exception as e:
            print(f"❌ Auto-sync failed: {e}")

bot = MyBot()

# ==========================================
# 3. COMMANDS & EVENTS
# ==========================================

# --- NEW: HONEYPOT SCAM TRAP EVENT ---
@bot.event
async def on_message(message):
    # Ignore messages from bots to prevent loops
    if message.author.bot:
        return
    
    # Check if the channel is an active honeypot
    if message.channel.id in bot.honeypot_channels:
        # Check if the message contains an image/attachment
        if message.attachments:
            # Exempt the Server Owner and Administrators
            if message.author != message.guild.owner and not message.author.guild_permissions.administrator:
                try:
                    # Softban: Ban the user (deleting last 7 days of their messages), then instantly unban them
                    await message.guild.ban(message.author, reason="Triggered MrBeast Scam Honeypot", delete_message_seconds=604800)
                    await message.guild.unban(message.author, reason="Softban completed")
                    
                    # Send a quick log into the channel
                    alert = await message.channel.send(f"🚨 **SCAM PREVENTED!** Softbanned `{message.author}` for triggering the honeypot.")
                    await alert.delete(delay=10) # Clean up the alert after 10 seconds
                except discord.Forbidden:
                    print("ERROR: I do not have permissions to ban members!")
                
                return # Stop processing anything else for this scam message

    # IMPORTANT: Since we overrode on_message, we must process other prefix commands
    await bot.process_commands(message)


# --- NEW: HONEYPOT SETUP COMMAND ---
@bot.tree.command(name="honeypot-setup", description="Spawn the panel to configure a MrBeast scam honeypot")
@app_commands.checks.has_permissions(administrator=True)
async def honeypot_setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🕸️ Anti-Scam Honeypot Setup",
        description="Use the buttons below to toggle honeypot mode for this channel.\n\n**How it works:** If a regular user sends an image/attachment in an enabled channel, they will instantly be softbanned (Kicked + Messages Deleted).",
        color=0xFF0000
    )
    await interaction.response.send_message(embed=embed, view=HoneypotView())

@bot.command()
@commands.has_permissions(administrator=True)
async def honeypot_setup(ctx):
    """Spawn the panel to configure a MrBeast scam honeypot"""
    embed = discord.Embed(
        title="🕸️ Anti-Scam Honeypot Setup",
        description="Use the buttons below to toggle honeypot mode for this channel.\n\n**How it works:** If a regular user sends an image/attachment in an enabled channel, they will instantly be softbanned (Kicked + Messages Deleted).",
        color=0xFF0000
    )
    await ctx.send(embed=embed, view=HoneypotView())


# --- VERIFICATION SETUP COMMANDS ---
@bot.tree.command(name="verify-setup", description="Send the verification button to this channel")
@app_commands.checks.has_permissions(administrator=True)
async def verify_setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Server Verification",
        description="To access the rest of the server channels, please click the button below to verify your account and complete the security check.",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, view=VerifyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_setup_cmd(ctx):
    """Send the verification button to this channel"""
    embed = discord.Embed(
        title="Server Verification",
        description="To access the rest of the server channels, please click the button below to verify your account and complete the security check.",
        color=0x5865F2
    )
    await ctx.send(embed=embed, view=VerifyView())

# --- EXISTING SCRIPT SELECTION COMMANDS ---
@bot.tree.command(name="script", description="Open the script selection menu")
async def script(interaction: discord.Interaction):
    await interaction.response.send_message("Please select a script from below:", view=JJSView(), ephemeral=True)

@bot.command()
async def sync(ctx):
    """Manual sync in case auto-sync fails"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Manually synced {len(synced)} command(s)!")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.command()
async def menu(ctx):
    """Works even if slash commands aren't showing up yet"""
    await ctx.send("Please select a script from below:", view=JJSView())

@bot.event
async def on_ready():
    print("!!! UPDATE TEST: THE NEW CODE IS FINALLY WORKING !!!")
    print(f"Bot logged in as {bot.user}")

# ==========================================
# 4. RUN & DEBUGGING
# ==========================================

# Set up logging so Discord.py prints detailed errors to Railway logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("=== DEBUG: Bot script has started executing ===")

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN:
    print(f"=== DEBUG: Token found in environment! (Length: {len(TOKEN)} characters) ===")
    
    try:
        print("=== DEBUG: Attempting to connect to Discord... ===")
        # log_handler=None prevents discord.py from overriding our custom logging above
        bot.run(TOKEN, log_handler=None) 
        
    except discord.errors.LoginFailure:
        print("❌ CRITICAL ERROR: The Discord Token is invalid! Check your Railway variables.")
    except discord.errors.PrivilegedIntentsRequired:
        print("❌ CRITICAL ERROR: Privileged Intents are missing!")
        print("-> Go to Discord Developer Portal > Your Bot > Bot Tab")
        print("-> Turn ON 'Server Members Intent' and 'Message Content Intent'")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: An unexpected error occurred: {e}")
else:
    print("❌ CRITICAL ERROR: No DISCORD_TOKEN found in Railway Variables!")
    print("-> Please go to Railway > Variables and add DISCORD_TOKEN")
