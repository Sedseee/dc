import discord
import os
import json
import logging
import sys
import random
import re
import asyncio
from datetime import timedelta
from discord.ext import commands
from discord import app_commands

# ==========================================
# 0. DATABASE & CACHE SETUP
# ==========================================

HONEYPOT_FILE = "honeypots.json"
WARNINGS_FILE = "warnings.json"
SETTINGS_FILE = "settings.json"
AFK_FILE = "afk.json"

# In-memory caches (clears if bot restarts)
purged_messages_cache = {}
active_unpurges = {}

def load_json(filename, default_type=list):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_type()

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_honeypots(): return load_json(HONEYPOT_FILE, list)
def save_honeypots(data): save_json(HONEYPOT_FILE, data)

# ==========================================
# 1. DROPDOWN & BUTTON SETUP
# ==========================================

VERIFICATION_URL = "https://sedse.pages.dev"

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Verify with Discord", url=VERIFICATION_URL, style=discord.ButtonStyle.link
        ))

class JJSDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sedse JJS Script", description="Click here for the Sedse JJS Script", value="sedse_jjs"),
            discord.SelectOption(label="JJS Piano", description="Click here for info on JJS Piano", value="jjs_piano"),
            discord.SelectOption(label="JJS Piano Open Source", description="Click here for info on the Open Source version", value="jjs_piano_os")
        ]
        super().__init__(placeholder="Choose a script...", min_values=1, max_values=1, options=options, custom_id="persistent_jjs_dropdown")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "sedse_jjs":
            response_text = "Here is the Sedse JJS Script:\n`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/SedseXD/sedsejjs/refs/heads/main/sedse's%20scripts\"))()`"
        elif self.values[0] == "jjs_piano":
            response_text = "Here is the information and link for JJS Piano:\n `loadstring(game:HttpGet('https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua'))()`"
        elif self.values[0] == "jjs_piano_os":
            response_text = "Here is the GitHub link and info for JJS Piano Open Source: https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua"
        await interaction.response.send_message(response_text, ephemeral=True)

class JJSView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(JJSDropdown())

class HoneypotView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="enable honeypot", style=discord.ButtonStyle.green, custom_id="hp_enable_btn")
    async def enable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("this function is restricted to administrative personnel only.", ephemeral=True)
        
        if interaction.channel.id not in bot.honeypot_channels:
            bot.honeypot_channels.append(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("the honeypot mechanism has been successfully activated for this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("the honeypot mechanism is already active within this channel.", ephemeral=True)

    @discord.ui.button(label="disable honeypot", style=discord.ButtonStyle.red, custom_id="hp_disable_btn")
    async def disable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("this function is restricted to administrative personnel only.", ephemeral=True)
        
        if interaction.channel.id in bot.honeypot_channels:
            bot.honeypot_channels.remove(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("the honeypot mechanism has been deactivated for this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("the honeypot mechanism is not currently active within this channel.", ephemeral=True)

# ==========================================
# 2. BOT CLASS
# ==========================================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True 
        super().__init__(command_prefix=["!sedse ", "!"], intents=intents)
        self.honeypot_channels = load_honeypots()

    async def setup_hook(self):
        self.add_view(JJSView())
        self.add_view(VerifyView())
        self.add_view(HoneypotView()) 
        
        print("Attempting to auto-sync slash commands...")
        try:
            synced = await self.tree.sync()
            print(f"Auto-sync successful. Registered {len(synced)} command(s).")
        except Exception as e:
            print(f"Auto-sync failed: {e}")

bot = MyBot()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

async def send_log(guild, title, description, color):
    settings = load_json(SETTINGS_FILE, dict)
    log_channel_id = settings.get(str(guild.id), {}).get("log_channel")
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
        if channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=discord.utils.utcnow())
            await channel.send(embed=embed)

def parse_duration(duration_str):
    if not duration_str: return None
    pattern = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
    match = pattern.fullmatch(duration_str)
    if not match: return None
    kwargs = {k: int(v) for k, v in match.groupdict().items() if v}
    return timedelta(**kwargs) if kwargs else None

# ==========================================
# 4. EXISTING COMMANDS & EVENTS
# ==========================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Honeypot Check
    if message.channel.id in bot.honeypot_channels:
        if message.author != message.guild.owner and not message.author.guild_permissions.administrator:
            try:
                await message.guild.ban(message.author, reason="unauthorized transmission in a designated security channel", delete_message_seconds=604800)
                await message.guild.unban(message.author, reason="automatic security unban completed")
                
                alert = await message.channel.send(f"security protocol triggered. account `{message.author}` has been temporarily restricted.")
                await alert.delete(delay=10) 
            except discord.Forbidden:
                pass
            return 

    # AFK System: Remove AFK status if the user types a message
    afk_data = load_json(AFK_FILE, dict)
    author_id = str(message.author.id)
    if author_id in afk_data:
        del afk_data[author_id]
        save_json(AFK_FILE, afk_data)
        welcome_msg = await message.channel.send(f"Welcome back {message.author.mention}, I have removed your AFK status.")
        await welcome_msg.delete(delay=5)

    # AFK System: Reply if an AFK user is mentioned
    if message.mentions:
        for mentioned_user in message.mentions:
            mentioned_id = str(mentioned_user.id)
            if mentioned_id in afk_data:
                afk_msg = afk_data[mentioned_id]["message"]
                await message.channel.send(f"{mentioned_user.display_name} is currently AFK: {afk_msg}")

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def honeypot_setup(ctx):
    embed = discord.Embed(title="honeypot configuration panel", description="Use the options below to manage security.", color=0xFF0000)
    await ctx.send(embed=embed, view=HoneypotView())

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_setup(ctx):
    embed = discord.Embed(title="Server Verification", description="Click below to verify.", color=0x5865F2)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
async def menu(ctx):
    await ctx.send("Please select a script from below:", view=JJSView())

# ==========================================
# 5. NEW SEDSE MODERATION & AFK COMMANDS
# ==========================================

@bot.command()
async def afk(ctx, *, message="AFK"):
    afk_data = load_json(AFK_FILE, dict)
    afk_data[str(ctx.author.id)] = {"message": message}
    save_json(AFK_FILE, afk_data)
    await ctx.send(f"{ctx.author.mention}, I have set your AFK status to: {message}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
    await send_log(ctx.guild, "User Kicked", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.orange())

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")
    await send_log(ctx.guild, "User Banned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.red())

@bot.command()
@commands.has_permissions(ban_members=True)
async def softban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=f"Softban: {reason}", delete_message_seconds=604800)
    await ctx.guild.unban(member, reason="Softban release")
    await ctx.send(f"{member.mention} has been softbanned (Kicked + Messages deleted).")
    await send_log(ctx.guild, "User Softbanned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.orange())

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: discord.User):
    await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
    await ctx.send(f"{user.mention} has been unbanned.")
    await send_log(ctx.guild, "User Unbanned", f"**User:** {user.mention}\n**Mod:** {ctx.author.mention}", discord.Color.green())

@bot.command(aliases=["mute"])
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration_str: str = None, *, reason="No reason provided"):
    duration = None
    actual_reason = reason

    if duration_str:
        duration = parse_duration(duration_str)
        if not duration:
            actual_reason = f"{duration_str} {reason}".strip()
            if actual_reason.endswith("No reason provided"):
                actual_reason = actual_reason.replace(" No reason provided", "")
            duration = timedelta(days=27, hours=23)
    else:
        duration = timedelta(days=27, hours=23)

    try:
        await member.timeout(discord.utils.utcnow() + duration, reason=actual_reason)
        await ctx.send(f"{member.mention} has been timed out/muted. Reason: {actual_reason}")
        await send_log(ctx.guild, "User Timed Out", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {actual_reason}", discord.Color.gold())
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this user.")

@bot.command(aliases=["unmute"])
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"Untimeout by {ctx.author}")
    await ctx.send(f"{member.mention} has been untimed out/unmuted.")
    await send_log(ctx.guild, "User Untimed Out", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}", discord.Color.green())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("Amount must be greater than 0.")
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msgs_to_save = [msg for msg in deleted if msg.id != ctx.message.id][:100]
    
    purged_messages_cache[ctx.channel.id] = msgs_to_save
    await ctx.send(f"Purged {len(msgs_to_save)} messages. Use '!sedse unpurge' to undo.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unpurge(ctx, action: str = None):
    global active_unpurges

    if action and action.lower() == "stop":
        if active_unpurges.get(ctx.channel.id, False):
            active_unpurges[ctx.channel.id] = False
            await ctx.send("Stopping the unpurge process...")
        else:
            await ctx.send("No active unpurge is running in this channel.")
        return

    msgs = purged_messages_cache.get(ctx.channel.id, [])
    if not msgs:
        return await ctx.send("No recently purged messages found in this channel to restore.")
        
    active_unpurges[ctx.channel.id] = True
    await ctx.send(f"Restoring {len(msgs)} messages... (Type '!sedse unpurge stop' to cancel early)")
    
    webhooks = await ctx.channel.webhooks()
    webhook = discord.utils.get(webhooks, name="Sedse Restore")
    if not webhook:
        webhook = await ctx.channel.create_webhook(name="Sedse Restore")
        
    restored = 0
    for msg in reversed(msgs):
        # Stop check
        if not active_unpurges.get(ctx.channel.id, False):
            await ctx.send(f"Unpurge stopped early. Restored {restored} messages.")
            purged_messages_cache[ctx.channel.id] = []
            return

        if msg.content or msg.embeds:
            try:
                # wait=False significantly speeds this up by bypassing the HTTP response wait
                await webhook.send(
                    content=msg.content or None, embeds=msg.embeds,
                    username=msg.author.display_name,
                    avatar_url=msg.author.display_avatar.url if msg.author.display_avatar else None,
                    wait=False
                )
                restored += 1
                await asyncio.sleep(0.1) # Brief pause to allow the bot to listen for the stop command
            except Exception: pass
                
    active_unpurges[ctx.channel.id] = False
    purged_messages_cache[ctx.channel.id] = []
    await ctx.send(f"Successfully restored {restored} messages.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    warnings = load_json(WARNINGS_FILE, dict)
    user_id = str(member.id)
    
    if user_id not in warnings: warnings[user_id] = []
    warnings[user_id].append({"reason": reason, "mod": ctx.author.name, "date": str(discord.utils.utcnow())[:19]})
    save_json(WARNINGS_FILE, warnings)
    
    await ctx.send(f"Warned {member.mention} for: {reason}")
    await send_log(ctx.guild, "User Warned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.yellow())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warnings(ctx, member: discord.Member):
    warnings_data = load_json(WARNINGS_FILE, dict)
    user_warns = warnings_data.get(str(member.id), [])
    
    if not user_warns:
        return await ctx.send(f"{member.display_name} has no warnings.")
        
    embed = discord.Embed(title=f"Warnings for {member.display_name}", color=discord.Color.gold())
    for i, w in enumerate(user_warns, 1):
        embed.add_field(name=f"Warning {i} - by {w['mod']}", value=f"**Reason:** {w['reason']}\n**Date:** {w['date']}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(f"{channel.mention} has been locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(f"{channel.mention} has been unlocked.")

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, name: str):
    await member.edit(nick=name)
    await ctx.send(f"Changed {member.mention}'s nickname to **{name}**.")

@bot.command()
@commands.has_permissions(administrator=True)
async def log_channel(ctx, channel: discord.TextChannel):
    settings = load_json(SETTINGS_FILE, dict)
    if str(ctx.guild.id) not in settings: settings[str(ctx.guild.id)] = {}
    settings[str(ctx.guild.id)]["log_channel"] = channel.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(f"Moderation logs will now be sent to {channel.mention}")

@bot.command(aliases=["conflip"])
async def coinflip(ctx):
    outcome = random.choice(["Heads", "Tails"])
    await ctx.send(f"The coin landed on: **{outcome}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def annihilate(ctx, member: discord.Member):
    allowed_roles = ["verified", "script user"]
    roles_to_remove = [r for r in member.roles if r.name.lower() not in allowed_roles and r.name != "@everyone"]
    
    if not roles_to_remove:
        return await ctx.send(f"{member.mention} has no eligible roles to strip.")
        
    try:
        await member.remove_roles(*roles_to_remove, reason="Annihilation command")
        await ctx.send(f"Annihilated {member.mention}. Removed {len(roles_to_remove)} roles.")
        await send_log(ctx.guild, "User Annihilated", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}", discord.Color.dark_red())
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove some of this user's roles.")

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

# ==========================================
# 6. RUN & DEBUGGING
# ==========================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    try:
        bot.run(TOKEN, log_handler=None) 
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
else:
    print("CRITICAL ERROR: No DISCORD_TOKEN found!")
