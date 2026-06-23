import discord
import os
import json
import logging
import sys
import random
import re
import asyncio
from datetime import timedelta
from typing import Union
from discord.ext import commands
from discord import app_commands

# ==========================================
# 0. DATABASE & CACHE SETUP
# ==========================================

HONEYPOT_FILE = "honeypots.json"
WARNINGS_FILE = "warnings.json"
SETTINGS_FILE = "settings.json"
AFK_FILE = "afk.json"
PERMS_FILE = "perms.json"
MUTED_ADMINS_FILE = "muted_admins.json" # Added for the force-mute system

# Important Role IDs
ROLE_SCRIPT_USER_ID = 1500435366812061844
ROLE_VERIFIED_ID = 1507442109735633097

# In-memory caches (clears if bot restarts)
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

def check_perms(cmd_name, **default_perms):
    async def predicate(ctx):
        if ctx.guild and (ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator):
            return True
            
        if default_perms:
            has_default = all(getattr(ctx.author.guild_permissions, k, False) == v for k, v in default_perms.items())
            if has_default:
                return True

        perms_data = load_json(PERMS_FILE, dict)
        guild_perms = perms_data.get(str(ctx.guild.id), {})
        
        for check_cmd in [cmd_name, "all"]:
            cmd_perms = guild_perms.get(check_cmd, {"roles": [], "users": []})
            
            if ctx.author.id in cmd_perms["users"]:
                return True
            if any(role.id in cmd_perms["roles"] for role in ctx.author.roles):
                return True
                
        raise commands.MissingPermissions([f"Custom Role/User Perm or {list(default_perms.keys())}"])
    return commands.check(predicate)

# ==========================================
# 4. EVENTS
# ==========================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions) or isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Error executing command: {error}")

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

    # AFK System
    afk_data = load_json(AFK_FILE, dict)
    author_id = str(message.author.id)
    if author_id in afk_data:
        del afk_data[author_id]
        save_json(AFK_FILE, afk_data)
        welcome_msg = await message.channel.send(f"Welcome back {message.author.mention}, I have removed your AFK status.")
        await welcome_msg.delete(delay=5)

    if message.mentions:
        for mentioned_user in message.mentions:
            mentioned_id = str(mentioned_user.id)
            if mentioned_id in afk_data:
                afk_msg = afk_data[mentioned_id]["message"]
                await message.channel.send(f"{mentioned_user.display_name} is currently AFK: {afk_msg}")

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

# ==========================================
# 5. COMMANDS
# ==========================================

@bot.command()
@commands.is_owner()
async def forcemute(ctx, member: discord.Member, duration_str: str = "1h", *, reason="Owner override"):
    duration = parse_duration(duration_str) or timedelta(hours=1)
    
    # Roles that should NEVER be stripped
    exempt_roles = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    
    # Find all roles the user has that are higher than @everyone, not managed (booster/bot roles), and not exempt
    roles_to_remove = [
        role for role in member.roles 
        if role.name != "@everyone" 
        and not role.is_default() 
        and not role.managed 
        and role.id not in exempt_roles
    ]
    
    # Save their role IDs so we can give them back later
    role_ids = [role.id for role in roles_to_remove]
    
    muted_data = load_json(MUTED_ADMINS_FILE, dict)
    muted_data[str(member.id)] = {"roles": role_ids}
    save_json(MUTED_ADMINS_FILE, muted_data)

    try:
        # Strip their roles (Removes Admin immunity)
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"Force mute by {ctx.author}")
        
        # Now that they aren't admin, time them out
        await member.timeout(discord.utils.utcnow() + duration, reason=reason)
        
        await ctx.send(f"Successfully stripped {len(roles_to_remove)} roles and force-muted {member.mention} for {duration_str}.")
        await send_log(ctx.guild, "Admin Force Muted", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}\n**Duration:** {duration_str}", discord.Color.red())
    except discord.Forbidden:
        await ctx.send("I still can't mute them! Make sure my Bot role is dragged higher than ALL of their roles in Server Settings.")

@bot.command()
@commands.is_owner()
async def forceunmute(ctx, member: discord.Member):
    muted_data = load_json(MUTED_ADMINS_FILE, dict)
    user_id = str(member.id)
    
    if user_id in muted_data:
        # Get their old roles back
        roles_to_add = []
        for role_id in muted_data[user_id]["roles"]:
            role = ctx.guild.get_role(role_id)
            if role:
                roles_to_add.append(role)
                
        try:
            # Remove timeout
            await member.timeout(None, reason="Force unmute")
            # Restore roles
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Restoring roles after force mute")
            
            del muted_data[user_id]
            save_json(MUTED_ADMINS_FILE, muted_data)
            
            await ctx.send(f"Restored {len(roles_to_add)} roles and unmuted {member.mention}.")
            await send_log(ctx.guild, "Admin Force Unmuted", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}", discord.Color.green())
        except discord.Forbidden as e:
            await ctx.send(f"I lack permission to restore their roles. Discord error details: {e}")
    else:
        await ctx.send("This user is not in the force-mute database.")


@bot.command()
@commands.has_permissions(administrator=True)
async def perm(ctx, command_name: str, target: Union[discord.Role, discord.Member]):
    command_name = command_name.lower()
    
    valid_commands = [c.name for c in bot.commands] + ["all"]
    if command_name not in valid_commands:
        return await ctx.send(f"Command '{command_name}' does not exist.")
        
    perms_data = load_json(PERMS_FILE, dict)
    guild_id = str(ctx.guild.id)
    
    if guild_id not in perms_data:
        perms_data[guild_id] = {}
    if command_name not in perms_data[guild_id]:
        perms_data[guild_id][command_name] = {"roles": [], "users": []}
        
    cmd_perms = perms_data[guild_id][command_name]
    
    if isinstance(target, discord.Role):
        if target.id in cmd_perms["roles"]:
            cmd_perms["roles"].remove(target.id)
            action = "Revoked"
        else:
            cmd_perms["roles"].append(target.id)
            action = "Granted"
        target_name = f"role {target.mention}"
    else:
        if target.id in cmd_perms["users"]:
            cmd_perms["users"].remove(target.id)
            action = "Revoked"
        else:
            cmd_perms["users"].append(target.id)
            action = "Granted"
        target_name = f"user {target.mention}"
        
    save_json(PERMS_FILE, perms_data)
    await ctx.send(f"{action} permission to use '{command_name}' for {target_name}.")

@bot.command()
@check_perms("honeypot_setup", administrator=True)
async def honeypot_setup(ctx):
    embed = discord.Embed(title="honeypot configuration panel", description="Use the options below to manage security.", color=0xFF0000)
    await ctx.send(embed=embed, view=HoneypotView())

@bot.command()
@check_perms("verify_setup", administrator=True)
async def verify_setup(ctx):
    embed = discord.Embed(title="Server Verification", description="Click below to verify.", color=0x5865F2)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
async def menu(ctx):
    await ctx.send("Please select a script from below:", view=JJSView())

@bot.command()
@check_perms("verify", manage_roles=True)
async def verify(ctx, member: discord.Member):
    script_role = ctx.guild.get_role(ROLE_SCRIPT_USER_ID)
    verified_role = ctx.guild.get_role(ROLE_VERIFIED_ID)
    
    roles_to_add = []
    if script_role: roles_to_add.append(script_role)
    if verified_role: roles_to_add.append(verified_role)
    
    if not roles_to_add:
        return await ctx.send("Error: Could not find the required roles in this server.")
        
    try:
        await member.add_roles(*roles_to_add, reason=f"Manual verification by {ctx.author}")
        await ctx.send(f"Successfully verified {member.mention}.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to add roles to this user. Make sure my bot role is placed higher than the roles I am trying to assign.")

@bot.command()
@check_perms("impersonate", manage_webhooks=True)
async def impersonate(ctx, member: discord.Member, channel: discord.TextChannel, *, message: str):
    webhooks = await channel.webhooks()
    webhook = discord.utils.get(webhooks, name="Sedse Impersonator")
    
    if not webhook:
        webhook = await channel.create_webhook(name="Sedse Impersonator")
        
    try:
        await webhook.send(
            content=message,
            username=member.display_name,
            avatar_url=member.display_avatar.url if member.display_avatar else None,
            wait=False
        )
        
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
            
        confirmation = await ctx.send(f"Successfully impersonated {member.display_name} in {channel.mention}.")
        await confirmation.delete(delay=3)
        
    except Exception as e:
        await ctx.send(f"Failed to impersonate: {e}")

@bot.command()
async def afk(ctx, *, message="AFK"):
    afk_data = load_json(AFK_FILE, dict)
    afk_data[str(ctx.author.id)] = {"message": message}
    save_json(AFK_FILE, afk_data)
    await ctx.send(f"{ctx.author.mention}, I have set your AFK status to: {message}")

@bot.command()
@check_perms("kick", kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
    await send_log(ctx.guild, "User Kicked", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.orange())

@bot.command()
@check_perms("ban", ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")
    await send_log(ctx.guild, "User Banned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.red())

@bot.command()
@check_perms("softban", ban_members=True)
async def softban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=f"Softban: {reason}", delete_message_seconds=604800)
    await ctx.guild.unban(member, reason="Softban release")
    await ctx.send(f"{member.mention} has been softbanned (Kicked + Messages deleted).")
    await send_log(ctx.guild, "User Softbanned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.orange())

@bot.command()
@check_perms("unban", ban_members=True)
async def unban(ctx, user: discord.User):
    await ctx.guild.unban(user, reason=f"Unbanned by {ctx.author}")
    await ctx.send(f"{user.mention} has been unbanned.")
    await send_log(ctx.guild, "User Unbanned", f"**User:** {user.mention}\n**Mod:** {ctx.author.mention}", discord.Color.green())

@bot.command(aliases=["mute"])
@check_perms("timeout", moderate_members=True)
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
        await ctx.send("I don't have permission to timeout this user. If they are an Administrator, use `!sedse forcemute <user> [time]` instead (Owner only).")

@bot.command(aliases=["unmute"])
@check_perms("untimeout", moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"Untimeout by {ctx.author}")
    await ctx.send(f"{member.mention} has been untimed out/unmuted.")
    await send_log(ctx.guild, "User Untimed Out", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}", discord.Color.green())

@bot.command()
@check_perms("purge", manage_messages=True)
async def purge(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("Amount must be greater than 0.")
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msgs_to_save = [msg for msg in deleted if msg.id != ctx.message.id][:100]
    
    purged_messages_cache[ctx.channel.id] = msgs_to_save
    await ctx.send(f"Purged {len(msgs_to_save)} messages. Use '!sedse unpurge' to undo.", delete_after=5)

@bot.command()
@check_perms("unpurge", manage_messages=True)
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
        if not active_unpurges.get(ctx.channel.id, False):
            await ctx.send(f"Unpurge stopped early. Restored {restored} messages.")
            purged_messages_cache[ctx.channel.id] = []
            return

        if msg.content or msg.embeds:
            try:
                await webhook.send(
                    content=msg.content or None, embeds=msg.embeds,
                    username=msg.author.display_name,
                    avatar_url=msg.author.display_avatar.url if msg.author.display_avatar else None,
                    wait=False
                )
                restored += 1
                await asyncio.sleep(0.1) 
            except Exception: pass
                
    active_unpurges[ctx.channel.id] = False
    purged_messages_cache[ctx.channel.id] = []
    await ctx.send(f"Successfully restored {restored} messages.")

@bot.command()
@check_perms("warn", manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    warnings = load_json(WARNINGS_FILE, dict)
    user_id = str(member.id)
    
    if user_id not in warnings: warnings[user_id] = []
    warnings[user_id].append({"reason": reason, "mod": ctx.author.name, "date": str(discord.utils.utcnow())[:19]})
    save_json(WARNINGS_FILE, warnings)
    
    await ctx.send(f"Warned {member.mention} for: {reason}")
    await send_log(ctx.guild, "User Warned", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}\n**Reason:** {reason}", discord.Color.yellow())

@bot.command()
@check_perms("warnings", manage_messages=True)
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
@check_perms("lock", manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(f"{channel.mention} has been locked.")

@bot.command()
@check_perms("unlock", manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(f"{channel.mention} has been unlocked.")

@bot.command()
@check_perms("nick", manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, name: str):
    await member.edit(nick=name)
    await ctx.send(f"Changed {member.mention}'s nickname to **{name}**.")

@bot.command()
@check_perms("log_channel", administrator=True)
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
@check_perms("annihilate", administrator=True)
async def annihilate(ctx, member: discord.Member):
    allowed_role_ids = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    roles_to_remove = [r for r in member.roles if r.id not in allowed_role_ids and r.name != "@everyone"]
    
    if not roles_to_remove:
        return await ctx.send(f"{member.mention} has no eligible roles to strip.")
        
    try:
        await member.remove_roles(*roles_to_remove, reason="Annihilation command")
        await ctx.send(f"Annihilated {member.mention}. Removed {len(roles_to_remove)} roles.")
        await send_log(ctx.guild, "User Annihilated", f"**User:** {member.mention}\n**Mod:** {ctx.author.mention}", discord.Color.dark_red())
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove some of this user's roles.")

@bot.command()
async def badapple(ctx, action: str = "start"):
    global active_badapples
    
    if action.lower() in ["end", "stop"]:
        if active_badapples.get(ctx.channel.id):
            active_badapples[ctx.channel.id] = False
            await ctx.send("Stopping Bad Apple playback...")
        else:
            await ctx.send("No Bad Apple playback is currently active in this channel.")
        return
        
    if action.lower() == "start":
        if active_badapples.get(ctx.channel.id):
            return await ctx.send("Bad Apple is already playing in this channel! Use '!sedse badapple end' to stop it.")

        frames_file = "bad_apple.json"
        frames = []
        if not os.path.exists(frames_file):
            frames = [
                "#####\n#...#\n#.#.#\n#...#\n#####",
                ".....\n.###.\n.#.#.\n.###.\n.....",
                "[bad_apple.json not found! This is a placeholder animation.]"
            ]
            await ctx.send("[bad_apple.json not found! Playing a placeholder animation. Please add the frames file.]")
        else:
            try:
                with open(frames_file, "r", encoding="utf-8") as f:
                    frames = json.load(f)
            except Exception as e:
                return await ctx.send(f"Error loading frames: {e}")

        active_badapples[ctx.channel.id] = True
        msg = await ctx.send("```\nLoading Bad Apple...\n```")

        for i, frame in enumerate(frames):
            if not active_badapples.get(ctx.channel.id):
                try:
                    await msg.edit(content="```\nBad Apple playback stopped.\n```")
                except discord.NotFound:
                    pass
                break

            content = f"```\n{frame[:1980]}\n```" 
            
            try:
                await msg.edit(content=content)
                await asyncio.sleep(1.5) 
            except discord.errors.HTTPException as e:
                if e.status == 429: 
                    await asyncio.sleep(5) 
                else:
                    break 
        
        active_badapples[ctx.channel.id] = False

@bot.command()
@check_perms("hamzbid", manage_webhooks=True)
async def hamzbid(ctx):
    target_id = 1425810901490991104
    target_messages = []
    
    # Scan up to 200 recent messages in the channel to find the user's last 10
    async for msg in ctx.channel.history(limit=200):
        if msg.author.id == target_id and msg.content.strip():
            target_messages.append(msg)
            if len(target_messages) == 10:
                break
    
    if not target_messages:
        return await ctx.send("No recent messages found from that user to combine.")
        
    # Reverse the list so it combines them in chronological order (oldest to newest)
    target_messages.reverse()
    combined_text = " ".join([m.content for m in target_messages])
    
    # Ensure it doesn't exceed Discord's 2000 character limit
    if len(combined_text) > 2000:
        combined_text = combined_text[:1997] + "..."
        
    user = target_messages[0].author
    
    # Fetch or create the webhook
    webhooks = await ctx.channel.webhooks()
    webhook = discord.utils.get(webhooks, name="Sedse Impersonator")
    if not webhook:
        webhook = await ctx.channel.create_webhook(name="Sedse Impersonator")
        
    try:
        await webhook.send(
            content=combined_text,
            username=user.display_name,
            avatar_url=user.display_avatar.url if user.display_avatar else None,
            wait=False
        )
        
        # Delete the command invocation message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
            
    except Exception as e:
        await ctx.send(f"Failed to execute hamzbid: {e}")


@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member = None):
    # If they only tag one person, ship them with themselves
    if user2 is None:
        user2 = ctx.author

    # Use the users' IDs as a random seed so the percentage stays the same for those two specific people
    random.seed(user1.id + user2.id)
    percentage = random.randint(0, 100)
    
    # Reset random seed back to normal time-based seed
    random.seed()

    # Determine message based on percentage
    if percentage == 100:
        status = "Get married already! 💍"
    elif percentage > 75:
        status = "A perfect match! ❤️"
    elif percentage > 50:
        status = "There's some potential here! 💕"
    elif percentage > 25:
        status = "Might want to just stay friends... 😬"
    else:
        status = "Absolutely not. Keep them away from each other. 🛑"

    embed = discord.Embed(
        title="Love Calculator 💘", 
        description=f"**{user1.display_name}** & **{user2.display_name}**\n\nCompatibility: **{percentage}%**\n*{status}*",
        color=discord.Color.pink()
    )
    await ctx.send(embed=embed)

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
