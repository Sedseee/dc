import discord
import os
import json
import logging
import sys
import random
import re
import asyncio
import aiohttp
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
BADAPPLE_FILE = "badapple.json"

ROLE_SCRIPT_USER_ID = 1500435366812061844
ROLE_VERIFIED_ID = 1507442109735633097

purged_messages_cache = {}
active_unpurges = {}
active_badapples = {}

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
# 1. UI COMPONENTS
# ==========================================

VERIFICATION_URL = "https://sedse.pages.dev"

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Verify with Discord", url=VERIFICATION_URL, style=discord.ButtonStyle.link))

class JJSDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Sedse JJS Script", value="sedse_jjs"),
            discord.SelectOption(label="JJS Piano", value="jjs_piano"),
            discord.SelectOption(label="JJS Piano Open Source", value="jjs_piano_os")
        ]
        super().__init__(placeholder="Choose a script...", min_values=1, max_values=1, options=options, custom_id="persistent_jjs_dropdown")

    async def callback(self, interaction: discord.Interaction):
        responses = {
            "sedse_jjs": "Here is the Sedse JJS Script:\n`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/SedseXD/sedsejjs/refs/heads/main/sedse's%20scripts\"))()`",
            "jjs_piano": "Here is the JJS Piano info:\n `loadstring(game:HttpGet('https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua'))()`",
            "jjs_piano_os": "GitHub Link: https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua"
        }
        await interaction.response.send_message(responses[self.values[0]], ephemeral=True)

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
            return await interaction.response.send_message("Administrative personnel only.", ephemeral=True)
        if interaction.channel.id not in bot.honeypot_channels:
            bot.honeypot_channels.append(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("Honeypot activated for this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("Honeypot is already active.", ephemeral=True)

    @discord.ui.button(label="disable honeypot", style=discord.ButtonStyle.red, custom_id="hp_disable_btn")
    async def disable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Administrative personnel only.", ephemeral=True)
        if interaction.channel.id in bot.honeypot_channels:
            bot.honeypot_channels.remove(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("Honeypot deactivated.", ephemeral=True)

# ==========================================
# 2. BOT CORE
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
        await self.tree.sync()

bot = MyBot()

# ==========================================
# 3. HELPERS
# ==========================================

async def send_log(guild, title, description, color):
    settings = load_json(SETTINGS_FILE, dict)
    log_id = settings.get(str(guild.id), {}).get("log_channel")
    if log_id:
        channel = guild.get_channel(log_id)
        if channel:
            await channel.send(embed=discord.Embed(title=title, description=description, color=color))

def parse_duration(d_str):
    if not d_str: return None
    match = re.fullmatch(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?', d_str)
    if not match: return None
    args = {k: int(v) for k, v in match.groupdict().items() if v}
    return timedelta(**args) if args else None

# ==========================================
# 4. EVENTS
# ==========================================

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    if message.channel.id in bot.honeypot_channels:
        if message.author != message.guild.owner and not message.author.guild_permissions.administrator:
            try:
                await message.guild.ban(message.author, reason="Honeypot Trigger", delete_message_seconds=604800)
                await message.guild.unban(message.author)
            except: pass
            return 

    afk_data = load_json(AFK_FILE, dict)
    uid = str(message.author.id)
    if uid in afk_data:
        del afk_data[uid]
        save_json(AFK_FILE, afk_data)
        await (await message.channel.send(f"Welcome back {message.author.mention}, AFK removed.")).delete(delay=5)

    for mention in message.mentions:
        if str(mention.id) in afk_data:
            await message.channel.send(f"{mention.display_name} is AFK: {afk_data[str(mention.id)]['message']}")

    await bot.process_commands(message)

# ==========================================
# 5. COMMANDS
# ==========================================

@bot.command()
async def badapple(ctx, action: str = "start"):
    global active_badapples
    if action.lower() == "stop":
        active_badapples[ctx.channel.id] = False
        return await ctx.send("Stopping playback.")

    if active_badapples.get(ctx.channel.id): return await ctx.send("Already playing.")
    active_badapples[ctx.channel.id] = True

    if not os.path.exists(BADAPPLE_FILE):
        status = await ctx.send("Downloading frames...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://raw.githubusercontent.com/Coding-with-Adam/Dash-by-Plotly/master/Other/Data-Dash-app-gallery/badapple_frames.json") as r:
                # FIX: Read as text first to avoid ContentType errors
                text_data = await r.text()
                data = json.loads(text_data)
                save_json(BADAPPLE_FILE, data)
        await status.delete()

    frames = load_json(BADAPPLE_FILE, list)
    if isinstance(frames, dict): frames = [frames[k] for k in sorted(frames.keys(), key=lambda x: int(x))]
    
    msg = await ctx.send("Loading...")
    for i in range(0, len(frames), 15):
        if not active_badapples.get(ctx.channel.id): break
        try:
            await msg.edit(content=f"```\n{frames[i]}\n```")
            await asyncio.sleep(1.5)
        except: break
    active_badapples[ctx.channel.id] = False

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx, member: discord.Member, index: int):
    data = load_json(WARNINGS_FILE, dict)
    uid = str(member.id)
    if uid in data and 0 < index <= len(data[uid]):
        removed = data[uid].pop(index - 1)
        save_json(WARNINGS_FILE, data)
        await ctx.send(f"Removed warning {index} from {member.mention}: {removed['reason']}")
    else:
        await ctx.send("Invalid warning index.")

@bot.command()
async def afk(ctx, *, message="AFK"):
    data = load_json(AFK_FILE, dict)
    data[str(ctx.author.id)] = {"message": message}
    save_json(AFK_FILE, data)
    await ctx.send(f"{ctx.author.mention} is now AFK: {message}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="None"):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member.mention}")
    await send_log(ctx.guild, "Kick", f"User: {member}\nMod: {ctx.author}\nReason: {reason}", 0xFFA500)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="None"):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member.mention}")
    await send_log(ctx.guild, "Ban", f"User: {member}\nMod: {ctx.author}\nReason: {reason}", 0xFF0000)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user: discord.User):
    await ctx.guild.unban(user)
    await ctx.send(f"Unbanned {user}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, time_str: str = None, *, reason="None"):
    dur = parse_duration(time_str) or timedelta(days=27)
    await member.timeout(discord.utils.utcnow() + dur, reason=reason)
    await ctx.send(f"Timed out {member.mention} for {time_str or '28d'}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    purged_messages_cache[ctx.channel.id] = [m for m in deleted if m.id != ctx.message.id][:100]
    await (await ctx.send(f"Purged {amount} messages.")).delete(delay=3)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def unpurge(ctx, action: str = None):
    global active_unpurges
    if action == "stop":
        active_unpurges[ctx.channel.id] = False
        return
    msgs = purged_messages_cache.get(ctx.channel.id, [])
    if not msgs: return await ctx.send("Nothing to restore.")
    active_unpurges[ctx.channel.id] = True
    hook = discord.utils.get(await ctx.channel.webhooks(), name="Sedse Restore") or await ctx.channel.create_webhook(name="Sedse Restore")
    for m in reversed(msgs):
        if not active_unpurges.get(ctx.channel.id): break
        await hook.send(content=m.content, username=m.author.display_name, avatar_url=m.author.display_avatar.url, wait=False)
        await asyncio.sleep(0.1)
    await ctx.send("Unpurge complete.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="None"):
    data = load_json(WARNINGS_FILE, dict)
    uid = str(member.id)
    if uid not in data: data[uid] = []
    data[uid].append({"reason": reason, "mod": ctx.author.name, "date": str(discord.utils.utcnow())[:19]})
    save_json(WARNINGS_FILE, data)
    await ctx.send(f"Warned {member.mention}")

@bot.command()
async def warnings(ctx, member: discord.Member):
    user_warns = load_json(WARNINGS_FILE, dict).get(str(member.id), [])
    if not user_warns: return await ctx.send("No warnings.")
    e = discord.Embed(title=f"Warnings: {member.name}", color=0xFFD700)
    for i, w in enumerate(user_warns, 1): e.add_field(name=f"{i}. {w['mod']}", value=w['reason'], inline=False)
    await ctx.send(embed=e)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx, ch: discord.TextChannel = None):
    await (ch or ctx.channel).set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Channel locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx, ch: discord.TextChannel = None):
    await (ch or ctx.channel).set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Channel unlocked.")

@bot.command()
@commands.has_permissions(administrator=True)
async def log_channel(ctx, ch: discord.TextChannel):
    s = load_json(SETTINGS_FILE, dict)
    if str(ctx.guild.id) not in s: s[str(ctx.guild.id)] = {}
    s[str(ctx.guild.id)]["log_channel"] = ch.id
    save_json(SETTINGS_FILE, s)
    await ctx.send(f"Logs set to {ch.mention}")

@bot.command()
async def coinflip(ctx):
    await ctx.send(f"Result: {random.choice(['Heads', 'Tails'])}")

@bot.command()
@commands.has_permissions(administrator=True)
async def annihilate(ctx, member: discord.Member):
    safe = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    to_rem = [r for r in member.roles if r.id not in safe and r.name != "@everyone"]
    await member.remove_roles(*to_rem)
    await ctx.send(f"Annihilated {member.mention}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def verify(ctx, member: discord.Member):
    r1, r2 = ctx.guild.get_role(ROLE_SCRIPT_USER_ID), ctx.guild.get_role(ROLE_VERIFIED_ID)
    if r1 and r2: await member.add_roles(r1, r2)
    await ctx.send(f"Verified {member.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def honeypot_setup(ctx):
    await ctx.send(embed=discord.Embed(title="Honeypot Panel", color=0xFF0000), view=HoneypotView())

@bot.command()
async def menu(ctx):
    await ctx.send("Select a script:", view=JJSView())

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Synced.")

# ==========================================
# 6. RUN
# ==========================================

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN, log_handler=None)
