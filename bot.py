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
MUTED_ADMINS_FILE = "muted_admins.json"
UWULOCK_FILE = "uwulock.json"
QUOTAS_FILE = "quotas.json"
WHITELIST_FILE = "whitelist.json"
PRIORITY_WHITELIST_FILE = "priority_whitelist.json"
UMARIZZ_FILE = "umarizz.json"

# Auto-generate umarizz.json if it's missing (with the fixed syntax)
UMARIZZ_DEFAULT_DATA = {
  "umamusume_pickup_lines": [
    {"id": 1, "category": "The Trainer's Menu (General Lines)", "line": "Are you a Trainer? Because my heart starts racing the moment you're around."},
    {"id": 2, "category": "The Trainer's Menu (General Lines)", "line": "Are you the URA Finals? Because you're my ultimate goal."},
    {"id": 3, "category": "The Trainer's Menu (General Lines)", "line": "My stamina might be at an E, but my love for you is always S+."},
    {"id": 4, "category": "The Trainer's Menu (General Lines)", "line": "Forget the training menu—my only plan today is spending time with you."},
    {"id": 5, "category": "The Trainer's Menu (General Lines)", "line": "Are you a rainbow gate? Because seeing you guarantees it's going to be a good day."},
    {"id": 6, "category": "The Trainer's Menu (General Lines)", "line": "I must have maxed out my wisdom stat, because choosing you was the smartest thing I've ever done."},
    {"id": 7, "category": "The Trainer's Menu (General Lines)", "line": "Are you an alarm clock? Because you just gave me a second chance at love."},
    {"id": 8, "category": "The Trainer's Menu (General Lines)", "line": "My motivation just went from \"Hopeless\" to \"Perfect\" the second you walked in."},
    {"id": 9, "category": "The Trainer's Menu (General Lines)", "line": "I don't need a high-speed summer training camp if I can just spend the season with you."},
    {"id": 10, "category": "The Trainer's Menu (General Lines)", "line": "You must be an Inherited Factor, because you’ve completely changed my traits for the better."},
    {"id": 11, "category": "Character-Specific Charmers", "line": "Are you Special Week? Because you're the best in Japan in my eyes."},
    {"id": 12, "category": "Character-Specific Charmers", "line": "Are you Silence Suzuka? Because you took my breath away on the very first turn."},
    {"id": 13, "category": "Character-Specific Charmers", "line": "Call me Gold Ship, because I'm ready to drop-kick my way directly into your heart."},
    {"id": 14, "category": "Character-Specific Charmers", "line": "Are you Tokai Teio? Because you’ve got me skipping with joy."},
    {"id": 15, "category": "Character-Specific Charmers", "line": "Are you Oguri Cap? Because my hunger for your love is absolutely insatiable."},
    {"id": 16, "category": "Character-Specific Charmers", "line": "Are you Rice Shower? Because you’ve blessed my life, no matter what anyone else says."},
    {"id": 17, "category": "Character-Specific Charmers", "line": "Are you Mejiro McQueen? Because you’ve got elegance written all over you—let me buy you some sweets."},
    {"id": 18, "category": "Character-Specific Charmers", "line": "Are you Twin Turbo? Because I’m going all-out from the very start with you."},
    {"id": 19, "category": "Character-Specific Charmers", "line": "Are you Mihono Bourbon? Because my heart is programmed to love only you."},
    {"id": 20, "category": "Character-Specific Charmers", "line": "Are you Daiwa Scarlet? Because you’ll always be number one to me."},
    {"id": 21, "category": "Character-Specific Charmers", "line": "Are you Vodka? Because you’re absolutely intoxicating."},
    {"id": 22, "category": "Character-Specific Charmers", "line": "Are you Gold City? Because you look like a literal runway model."},
    {"id": 23, "category": "Character-Specific Charmers", "line": "Are you Agnes Tachyon? Because the chemistry between us is undeniable."},
    {"id": 24, "category": "Character-Specific Charmers", "line": "Are you Manhattan Cafe? Because you're brewing up a lot of deep feelings in me."},
    {"id": 25, "category": "Character-Specific Charmers", "line": "Are you El Condor Pasa? Because our love is burning like a fiery luchador."},
    {"id": 26, "category": "Character-Specific Charmers", "line": "Are you Grass Wonder? Because you look calm, but you've completely conquered my heart."},
    {"id": 27, "category": "Character-Specific Charmers", "line": "Are you King Halo? Because you deserve a royal place in my life."},
    {"id": 28, "category": "Character-Specific Charmers", "line": "Are you Nice Nature? Because even if you think you're third place, you're always first to me."},
    {"id": 29, "category": "Character-Specific Charmers", "line": "Are you Symboli Rudolf? Because you’re the absolute Emperor of my heart."},
    {"id": 30, "category": "Character-Specific Charmers", "line": "Are you Maruzensky? Because you're super-car fast at stealing my feelings."},
    {"id": 31, "category": "Character-Specific Charmers", "line": "Are you Mayano Top Gun? Because you've got me flying high in the clouds."},
    {"id": 32, "category": "Character-Specific Charmers", "line": "Are you Super Creek? Because I could really use some of your pampering right now."},
    {"id": 33, "category": "Character-Specific Charmers", "line": "Are you Tamamo Cross? Because you're a small package with a whole lot of impact."},
    {"id": 34, "category": "Character-Specific Charmers", "line": "Are you Fine Motion? Because our connection feels like a royal decree."},
    {"id": 35, "category": "Character-Specific Charmers", "line": "Are you Air Groove? Because you've got absolute control over my heart's climate."},
    {"id": 36, "category": "Character-Specific Charmers", "line": "Are you Eishin Flash? Because everything with you is perfectly timed and precise."},
    {"id": 37, "category": "Character-Specific Charmers", "line": "Are you Smart Falcon? Because you're the ultimate center idol of my world."},
    {"id": 38, "category": "Character-Specific Charmers", "line": "Are you Curren Chan? Because you’ve completely captured my feed and my heart."},
    {"id": 39, "category": "Character-Specific Charmers", "line": "Are you Kitasan Black? Because you bring festival energy wherever you go."},
    {"id": 40, "category": "Character-Specific Charmers", "line": "Are you Satono Diamond? Because you're a rare gem I want to cherish forever."},
    {"id": 41, "category": "Track Conditions & Race Strategy", "line": "Are you a turf track? Because I'm falling for you smoothly."},
    {"id": 42, "category": "Track Conditions & Race Strategy", "line": "Even if the track condition is \"Bad,\" my feelings for you are always \"Good.\""},
    {"id": 43, "category": "Track Conditions & Race Strategy", "line": "Are you the final straight? Because I’m giving it everything I've got to catch up to you."},
    {"id": 44, "category": "Track Conditions & Race Strategy", "line": "Forget the inner track, I want to take the long way around just to spend more time with you."},
    {"id": 45, "category": "Track Conditions & Race Strategy", "line": "Are you the Arima Kinen? Because you're the grand finale I've been waiting for all year."},
    {"id": 46, "category": "Track Conditions & Race Strategy", "line": "Are you the Japan Cup? Because you’ve attracted international attention, but I only have eyes for you."},
    {"id": 47, "category": "Track Conditions & Race Strategy", "line": "I'd run through a muddy dirt track just to see you smile."},
    {"id": 48, "category": "Track Conditions & Race Strategy", "line": "Are you an uphill slope? Because you make my heart beat faster and harder."},
    {"id": 49, "category": "Track Conditions & Race Strategy", "line": "Are you the starting gate? Because I’m ready to burst out and chase you down."},
    {"id": 50, "category": "Track Conditions & Race Strategy", "line": "You must be a 2400m race, because I'm in this relationship for the long haul."},
    {"id": 51, "category": "Skills & Stat Check", "line": "Did you just activate \"Maestro of the Corner\"? Because you smoothly navigated right into my heart."},
    {"id": 52, "category": "Skills & Stat Check", "line": "You must have the \"Charisma\" skill, because I literally cannot look away."},
    {"id": 53, "category": "Skills & Stat Check", "line": "My speed stat just broke the limit when you smiled at me."},
    {"id": 54, "category": "Skills & Stat Check", "line": "Are you a unique skill? Because you're absolutely one of a kind."},
    {"id": 55, "category": "Skills & Stat Check", "line": "I don't need \"Sprint Turbo\" to rush over to your side."},
    {"id": 56, "category": "Skills & Stat Check", "line": "You must have \"Tailwind,\" because you're pushing me in all the right directions."},
    {"id": 57, "category": "Skills & Stat Check", "line": "Are you a debuff skill? Because you’ve completely paralyzed me with your looks."},
    {"id": 58, "category": "Skills & Stat Check", "line": "I’ve got max stamina, but you still somehow leave me completely breathless."},
    {"id": 59, "category": "Skills & Stat Check", "line": "Are you \"Guts\"? Because you give me the strength to keep going when things get tough."},
    {"id": 60, "category": "Skills & Stat Check", "line": "Let's trigger a dynamic camera angle, because you look stunning from every single direction."},
    {"id": 61, "category": "Winning Live & Idol Status", "line": "Are you the center position? Because you're the star of my show."},
    {"id": 62, "category": "Winning Live & Idol Status", "line": "I’d win every G1 race on the calendar just to see you perform in the Winning Live."},
    {"id": 63, "category": "Winning Live & Idol Status", "line": "Are you \"Make debut\"? Because this is the start of something beautiful."},
    {"id": 64, "category": "Winning Live & Idol Status", "line": "My heart rate matches the beat of \"GIRLS' LEGEND U\" whenever you're near."},
    {"id": 65, "category": "Winning Live & Idol Status", "line": "Are you a glow stick? Because you light up my entire world."},
    {"id": 66, "category": "Winning Live & Idol Status", "line": "Forget the concert crowd, I'm only cheering for you."},
    {"id": 67, "category": "Winning Live & Idol Status", "line": "Are you a Triple Crown? Because you’re a rare achievement I'd love to win."},
    {"id": 68, "category": "Winning Live & Idol Status", "line": "You don't need a microphone to make your voice the only thing I hear."},
    {"id": 69, "category": "Winning Live & Idol Status", "line": "Let's duet on the center stage of my heart."},
    {"id": 70, "category": "Winning Live & Idol Status", "line": "You're the encore I'll always ask for."},
    {"id": 71, "category": "Items, Food & Fuel", "line": "Are you a giant carrot? Because you're exactly what I've been looking for."},
    {"id": 72, "category": "Items, Food & Fuel", "line": "You're sweeter than a freshly baked Mejiro macaron."},
    {"id": 73, "category": "Items, Food & Fuel", "line": "Are you a carrot burger? Because you’re the perfect treat after a long, exhausting day."},
    {"id": 74, "category": "Items, Food & Fuel", "line": "I’d share my very last carrot juice with you."},
    {"id": 75, "category": "Items, Food & Fuel", "line": "Are you a lucky charm? Because my chances of success skyrocket when you're around."},
    {"id": 76, "category": "Items, Food & Fuel", "line": "You must be a royal parfait, because you just maxed out my motivation levels."},
    {"id": 77, "category": "Items, Food & Fuel", "line": "Forget the training weights, you're the only thing heavy on my mind."},
    {"id": 78, "category": "Items, Food & Fuel", "line": "Are you a strategy playbook? Because I want to study your every move."},
    {"id": 79, "category": "Items, Food & Fuel", "line": "You're like a high-grade energy drink—one look at you and I'm fully charged."},
    {"id": 80, "category": "Items, Food & Fuel", "line": "Are you a secret stash of snacks? Because finding you made my whole week."},
    {"id": 81, "category": "Playful Puns & Pacing", "line": "Are you a front-runner? Because you're way ahead of anyone else."},
    {"id": 82, "category": "Playful Puns & Pacing", "line": "I might be a betweener, but I’m ready to make a definitive move on you."},
    {"id": 83, "category": "Playful Puns & Pacing", "line": "Are you a chaser? Because you've been running through my mind all day long."},
    {"id": 84, "category": "Playful Puns & Pacing", "line": "I promise I won't block your path; I just want to run right beside you."},
    {"id": 85, "category": "Playful Puns & Pacing", "line": "Are you a photo finish? Because it’s incredibly close, but you win every single time."},
    {"id": 86, "category": "Playful Puns & Pacing", "line": "You must be Tazuna-san, because you always know exactly how to guide me back on track."},
    {"id": 87, "category": "Playful Puns & Pacing", "line": "Are you President Akikawa? Because you’ve got \"fan-favorite\" written all over you."},
    {"id": 88, "category": "Playful Puns & Pacing", "line": "My love for you has a 100% success rate—absolutely zero training failure risk here."},
    {"id": 89, "category": "Playful Puns & Pacing", "line": "Are you the green light on the gate? Because you've got me ready to go."},
    {"id": 90, "category": "Playful Puns & Pacing", "line": "I must be out of stamina, because I'm falling incredibly hard for you."},
    {"id": 91, "category": "Playful Puns & Pacing", "line": "Are you a 5-star awakening? Because you've reached peak absolute perfection."},
    {"id": 92, "category": "Playful Puns & Pacing", "line": "You don't need lucky horseshoes to leave a permanent impression on my heart."},
    {"id": 93, "category": "Playful Puns & Pacing", "line": "Are you a critical hit in training? Because you just boosted my stats immensely."},
    {"id": 94, "category": "Playful Puns & Pacing", "line": "Even if I get a bad status condition, you're the only cure I'll ever need."},
    {"id": 95, "category": "Playful Puns & Pacing", "line": "Are you the URA trophy? Because I want to hold you high for everyone to see."},
    {"id": 96, "category": "Playful Puns & Pacing", "line": "You’ve got me running at a record-breaking pace just to keep up with your beauty."},
    {"id": 97, "category": "Playful Puns & Pacing", "line": "Are you a limited-time gacha banner? Because I’m willing to spend everything I have to get you."},
    {"id": 98, "category": "Playful Puns & Pacing", "line": "My heart is doing a full sprint, and there's no deceleration in sight."},
    {"id": 99, "category": "Playful Puns & Pacing", "line": "Are you a stable? Because I feel completely safe and at home with you."},
    {"id": 100, "category": "Playful Puns & Pacing", "line": "Let's cross the finish line together, because you're my ultimate prize."}
  ]
}

if not os.path.exists(UMARIZZ_FILE):
    with open(UMARIZZ_FILE, "w", encoding="utf-8") as f:
        json.dump(UMARIZZ_DEFAULT_DATA, f, indent=4)

# Important Role IDs
ROLE_SCRIPT_USER_ID = 1500435366812061844
ROLE_VERIFIED_ID = 1507442109735633097

# In-memory caches
purged_messages_cache = {}
active_unpurges = {}
active_badapples = {}
user_cooldowns = {}
mod_slur_warnings = {} 

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

class DynamicRateLimitError(commands.CheckFailure):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# ==========================================
# 1. VIEWS & MODALS
# ==========================================

VERIFICATION_URL = "https://sedse.pages.dev"

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="verify with discord", url=VERIFICATION_URL, style=discord.ButtonStyle.link
        ))

class JJSDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="sedse jjs script", description="click here for the sedse jjs script", value="sedse_jjs"),
            discord.SelectOption(label="jjs piano", description="click here for info on jjs piano", value="jjs_piano"),
            discord.SelectOption(label="jjs piano open source", description="click here for info on the open source version", value="jjs_piano_os")
        ]
        super().__init__(placeholder="choose a script...", min_values=1, max_values=1, options=options, custom_id="persistent_jjs_dropdown")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "sedse_jjs":
            response_text = "here's the sedse jjs script:\n`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/SedseXD/sedsejjs/refs/heads/main/sedse's%20scripts\"))()`"
        elif self.values[0] == "jjs_piano":
            response_text = "here's the info and link for jjs piano:\n `loadstring(game:HttpGet('https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua'))()`"
        elif self.values[0] == "jjs_piano_os":
            response_text = "here's the github link and info for jjs piano open source: https://raw.githubusercontent.com/SedseXD/piano/refs/heads/main/pianoscript.lua"
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
            return await interaction.response.send_message("only admins can mess with this.", ephemeral=True)
        if interaction.channel.id not in bot.honeypot_channels:
            bot.honeypot_channels.append(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("honeypot is up and running in here.", ephemeral=True)
        else:
            await interaction.response.send_message("honeypot is already on in this channel, chill.", ephemeral=True)

    @discord.ui.button(label="disable honeypot", style=discord.ButtonStyle.red, custom_id="hp_disable_btn")
    async def disable_honeypot(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("only admins can mess with this.", ephemeral=True)
        if interaction.channel.id in bot.honeypot_channels:
            bot.honeypot_channels.remove(interaction.channel.id)
            save_honeypots(bot.honeypot_channels)
            await interaction.response.send_message("honeypot is off for this channel now.", ephemeral=True)
        else:
            await interaction.response.send_message("honeypot isn't even on here.", ephemeral=True)

class ReasonModal(discord.ui.Modal, title='why tho?'):
    reason_input = discord.ui.TextInput(
        label='reason',
        style=discord.TextStyle.paragraph,
        placeholder='why are you doing this? spill it.',
        required=True,
        max_length=500
    )
    def __init__(self, view):
        super().__init__()
        self.view = view
    async def on_submit(self, interaction: discord.Interaction):
        self.view.reason = self.reason_input.value
        self.view.stop()
        await interaction.response.send_message("got it, moving on...", ephemeral=True)

class ReasonView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300) 
        self.ctx = ctx
        self.reason = None
    @discord.ui.button(label="give reason", style=discord.ButtonStyle.primary)
    async def provide_reason(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("not your button, back off.", ephemeral=True)
        await interaction.response.send_modal(ReasonModal(self))
    async def on_timeout(self):
        if not self.reason:
            try:
                await self.ctx.author.timeout(discord.utils.utcnow() + timedelta(minutes=10), reason="didn't drop a reason in 5 mins.")
                await self.ctx.channel.send(f"{self.ctx.author.mention} got muted for 10 mins 'cause they didn't give a reason in time.")
            except discord.Forbidden:
                await self.ctx.channel.send(f"{self.ctx.author.mention} didn't give a reason, but i don't have perms to mute them.")

class OwnerBanConfirmView(discord.ui.View):
    def __init__(self, target: discord.Member, reason: str, mod: discord.Member):
        super().__init__(timeout=None)
        self.target = target
        self.reason = reason
        self.mod = mod
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == interaction.guild.owner or await bot.is_owner(interaction.user):
            return True
        await interaction.response.send_message("only sedse can respond and confirm the ban.", ephemeral=True)
        return False
    @discord.ui.button(label="allow ban", style=discord.ButtonStyle.danger)
    async def allow_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.target.ban(reason=f"approved by sedse. mod: {self.mod.display_name}. reason: {self.reason}")
            await interaction.message.edit(content=f"ban greenlit by {interaction.user.mention} for {self.target.mention}.", view=None)
            await send_log(interaction.guild, "user banned", f"**user:** {self.target.mention}\n**mod:** {self.mod.mention} (approved by sedse)\n**reason:** {self.reason}", discord.Color.red())
        except discord.Forbidden:
            await interaction.response.send_message("i don't have perms to ban this user.", ephemeral=True)
        self.stop()
    @discord.ui.button(label="just mute", style=discord.ButtonStyle.secondary)
    async def just_mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(content=f"ban shot down by {interaction.user.mention}. {self.target.mention} is just gonna stay muted.", view=None)
        self.stop()

# --- MODVIEW UI CLASSES ---

class UnbanModal(discord.ui.Modal, title='unban user'):
    user_id = discord.ui.TextInput(label='user id', placeholder='drop their discord id here', required=True)
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            user = await bot.fetch_user(int(self.user_id.value))
            cmd = bot.get_command('unban')
            if await cmd.can_run(self.ctx):
                await self.ctx.invoke(cmd, user=user)
                await interaction.followup.send(f"unbanned {user.name}.", ephemeral=True)
        except commands.CheckFailure:
            await interaction.followup.send("you lack perms.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"failed: {e}", ephemeral=True)

class PermsModal(discord.ui.Modal, title='edit perms'):
    cmd_name = discord.ui.TextInput(label='command name', placeholder='e.g. kick, ban, all', required=True)
    target_id = discord.ui.TextInput(label='target id', placeholder='user or role id', required=True)
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            target_obj = self.ctx.guild.get_member(int(self.target_id.value)) or self.ctx.guild.get_role(int(self.target_id.value))
            if not target_obj: return await interaction.followup.send("couldn't find that user or role.", ephemeral=True)
            cmd = bot.get_command('perm')
            if await cmd.can_run(self.ctx):
                await self.ctx.invoke(cmd, command_name=self.cmd_name.value, target=target_obj)
                await interaction.followup.send(f"updated perms for {self.cmd_name.value}.", ephemeral=True)
        except commands.CheckFailure:
            await interaction.followup.send("you lack perms.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"failed: {e}", ephemeral=True)

class ModActionModal(discord.ui.Modal):
    def __init__(self, action, target, ctx):
        super().__init__(title=f"{action} target"[:45])
        self.action = action
        self.target = target
        self.ctx = ctx

        if self.action in ["mute", "forcemute"]:
            self.duration = discord.ui.TextInput(label="duration", placeholder="e.g. 10m, 1h, 1d", default="1h", required=True, max_length=20)
            self.add_item(self.duration)

        self.reason = discord.ui.TextInput(label="reason", placeholder="spill the reason", default="no reason", required=False, max_length=300)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cmd_map = {"warn": "warn", "mute": "timeout", "kick": "kick", "ban": "ban", "softban": "softban", "forcemute": "forcemute"}
        try:
            cmd = bot.get_command(cmd_map[self.action])
            if await cmd.can_run(self.ctx):
                kw = {"member": self.target, "reason": self.reason.value}
                if self.action in ["mute", "forcemute"]: kw["duration_str"] = self.duration.value
                await self.ctx.invoke(cmd, **kw)
                await interaction.followup.send(f"dropped the hammer on {self.target.mention} with {self.action}.", ephemeral=True)
        except DynamicRateLimitError as e:
            await interaction.followup.send(e.message, ephemeral=True)
        except commands.CheckFailure:
            await interaction.followup.send("you lack perms for this.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"something broke: {e}", ephemeral=True)

class ModView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.category = None
        self.action = None
        self.target = None

        self.category_select = discord.ui.Select(
            placeholder="pick a category...",
            options=[
                discord.SelectOption(label="punish", description="smite someone"),
                discord.SelectOption(label="pardon", description="forgive someone"),
                discord.SelectOption(label="whitelist", description="manage protections"),
                discord.SelectOption(label="server & perms", description="locks, perms, honeypots")
            ],
            row=0
        )
        self.category_select.callback = self.category_cb
        self.add_item(self.category_select)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("this menu ain't for you.", ephemeral=True)
            return False
        return True

    async def category_cb(self, interaction: discord.Interaction):
        self.category = self.category_select.values[0]
        self.action = None
        self.target = None
        self.rebuild_ui()
        await interaction.response.edit_message(view=self)

    def rebuild_ui(self):
        self.clear_items()
        self.add_item(self.category_select)
        if not self.category: return

        opts = []
        if self.category == "punish": opts = ["warn", "mute", "kick", "ban", "softban", "forcemute", "annihilate"]
        elif self.category == "pardon": opts = ["unmute", "forceunmute", "clear warnings", "unban"]
        elif self.category == "whitelist": opts = ["add whitelist", "remove whitelist", "add priority", "remove priority"]
        elif self.category == "server & perms": opts = ["lock channel", "unlock channel", "uwulock user", "uwulock server", "uwu unlock server", "toggle honeypot", "edit perms"]

        self.action_select = discord.ui.Select(
            placeholder="pick an action...",
            options=[discord.SelectOption(label=opt) for opt in opts],
            row=1
        )
        self.action_select.callback = self.action_cb
        self.add_item(self.action_select)

        if self.action:
            needs_user = self.action in ["warn", "mute", "kick", "ban", "softban", "forcemute", "annihilate", "unmute", "forceunmute", "clear warnings", "add whitelist", "remove whitelist", "add priority", "remove priority", "uwulock user"]
            needs_channel = self.action in ["lock channel", "unlock channel", "toggle honeypot"]
            needs_exec = self.action in ["unban", "uwulock server", "uwu unlock server", "edit perms"]

            if needs_user:
                class DynamicUserSelect(discord.ui.UserSelect):
                    def __init__(inner_self, **kwargs): super().__init__(**kwargs)
                    async def callback(inner_self, interaction: discord.Interaction):
                        self.target = inner_self.values[0]
                        await self.handle_action(interaction)
                self.add_item(DynamicUserSelect(placeholder="select target user...", row=2))

            elif needs_channel:
                class DynamicChannelSelect(discord.ui.ChannelSelect):
                    def __init__(inner_self, **kwargs): super().__init__(**kwargs)
                    async def callback(inner_self, interaction: discord.Interaction):
                        self.target = inner_self.values[0]
                        await self.handle_action(interaction)
                self.add_item(DynamicChannelSelect(placeholder="select target channel...", channel_types=[discord.ChannelType.text], row=2))

            elif needs_exec:
                btn = discord.ui.Button(label="execute action", style=discord.ButtonStyle.grey, row=2)
                async def btn_cb(interaction: discord.Interaction):
                    await self.handle_action(interaction)
                btn.callback = btn_cb
                self.add_item(btn)

    async def action_cb(self, interaction: discord.Interaction):
        self.action = self.action_select.values[0]
        self.rebuild_ui()
        await interaction.response.edit_message(view=self)

    async def handle_action(self, interaction: discord.Interaction):
        needs_modal = self.action in ["warn", "mute", "kick", "ban", "softban", "forcemute"]
        if needs_modal:
            await interaction.response.send_modal(ModActionModal(self.action, self.target, self.ctx))
        elif self.action == "unban":
            await interaction.response.send_modal(UnbanModal(self.ctx))
        elif self.action == "edit perms":
            await interaction.response.send_modal(PermsModal(self.ctx))
        else:
            await interaction.response.defer()
            await self.execute_direct(interaction)

    async def execute_direct(self, interaction: discord.Interaction):
        act, ctx, t = self.action, self.ctx, self.target
        try:
            if act == "clear warnings":
                warnings = load_json(WARNINGS_FILE, dict)
                uid = str(t.id)
                if uid in warnings:
                    del warnings[uid]
                    save_json(WARNINGS_FILE, warnings)
                    await interaction.followup.send(f"wiped warnings for {t.mention}.", ephemeral=True)
                else:
                    await interaction.followup.send(f"{t.mention} is already clean.", ephemeral=True)
                return

            if act == "toggle honeypot":
                if t.id in bot.honeypot_channels:
                    bot.honeypot_channels.remove(t.id)
                    save_honeypots(bot.honeypot_channels)
                    await interaction.followup.send(f"killed honeypot in {t.mention}.", ephemeral=True)
                else:
                    bot.honeypot_channels.append(t.id)
                    save_honeypots(bot.honeypot_channels)
                    await interaction.followup.send(f"dropped honeypot in {t.mention}.", ephemeral=True)
                return

            cmd_map = {"annihilate": "annihilate", "unmute": "untimeout", "forceunmute": "forceunmute", "add whitelist": "whitelist", "remove whitelist": "unwhitelist", "lock channel": "lock", "unlock channel": "unlock"}
            if act in cmd_map:
                cmd = bot.get_command(cmd_map[act])
                if await cmd.can_run(ctx):
                    kw = {"channel": t} if act in ["lock channel", "unlock channel"] else {"member": t}
                    await ctx.invoke(cmd, **kw)
                    await interaction.followup.send(f"ran {act}.", ephemeral=True)
                return

            if act == "add priority":
                cmd = bot.get_command("priority").get_command("whitelist")
                if await cmd.can_run(ctx): await ctx.invoke(cmd, member=t)
                await interaction.followup.send("priority whitelisted.", ephemeral=True)
            elif act == "remove priority":
                cmd = bot.get_command("priority").get_command("unwhitelist")
                if await cmd.can_run(ctx): await ctx.invoke(cmd, member=t)
                await interaction.followup.send("removed priority whitelist.", ephemeral=True)
            elif act == "uwulock user":
                cmd = bot.get_command("uwulock")
                if await cmd.can_run(ctx): await ctx.invoke(cmd, arg1="lock", arg2=str(t.id))
                await interaction.followup.send("uwulocked them.", ephemeral=True)
            elif act == "uwulock server":
                cmd = bot.get_command("uwulock")
                if await cmd.can_run(ctx): await ctx.invoke(cmd, arg1="lock", arg2="everyone")
                await interaction.followup.send("uwulocked the whole server.", ephemeral=True)
            elif act == "uwu unlock server":
                cmd = bot.get_command("uwulock")
                if await cmd.can_run(ctx): await ctx.invoke(cmd, arg1="unlock", arg2="everyone")
                await interaction.followup.send("freed the server from uwu.", ephemeral=True)

        except DynamicRateLimitError as e: await interaction.followup.send(e.message, ephemeral=True)
        except commands.CheckFailure: await interaction.followup.send("you lack perms for this.", ephemeral=True)
        except Exception as e: await interaction.followup.send(f"broken: {e}", ephemeral=True)

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
        try:
            await self.tree.sync()
        except Exception as e:
            print(f"sync failed: {e}")

bot = MyBot()

# ==========================================
# 3. HELPERS & SYSTEMS
# ==========================================

UWU_EMOJIS = ["(ᵘʷᵘ)", "(ᴜ‿ᴜ✿)", "~(˘▾˘~)", "UwU", "(˘³˘)", "owo", "( ｡ᵘ ᵕ ᵘ ｡)", "(◦ᵕ ˘ ᵕ◦)", "(⑅˘꒳˘)", "^w^", "(。U ω U。)"]

def uwuify(text):
    text = text.replace('r', 'w').replace('l', 'w').replace('R', 'W').replace('L', 'W')
    text = re.sub(r'n([aeiou])', r'ny\1', text)
    text = re.sub(r'N([aeiou])', r'Ny\1', text)
    text = re.sub(r'N([AEIOU])', r'NY\1', text)
    words = text.split()
    result = []
    for word in words:
        if not (word.startswith("<@") or word.startswith("<#") or word.startswith("<:")):
            match = re.search(r'[a-zA-Z0-9]', word)
            if match:
                first_char = match.group()
                stutter = f"{first_char}-" * random.randint(1, 3)
                word = word[:match.start()] + stutter + word[match.start():]
        result.append(word)
        if random.random() < 0.8: result.append(random.choice(UWU_EMOJIS))
    return " ".join(result)

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

async def is_mod_owner(ctx):
    if ctx is None: return False
    if ctx.guild and ctx.author == ctx.guild.owner: return True
    if await ctx.bot.is_owner(ctx.author): return True
    return False

def check_perms(cmd_name, **default_perms):
    async def predicate(ctx):
        if ctx.guild and (ctx.author == ctx.guild.owner or ctx.author.guild_permissions.administrator):
            return True
        if default_perms:
            if all(getattr(ctx.author.guild_permissions, k, False) == v for k, v in default_perms.items()):
                return True
        perms_data = load_json(PERMS_FILE, dict)
        guild_perms = perms_data.get(str(ctx.guild.id), {})
        for check_cmd in [cmd_name, "all"]:
            cmd_perms = guild_perms.get(check_cmd, {"roles": [], "users": []})
            if ctx.author.id in cmd_perms["users"] or any(role.id in cmd_perms["roles"] for role in ctx.author.roles):
                return True
        raise commands.MissingPermissions([f"custom role/user perm or {list(default_perms.keys())}"])
    return commands.check(predicate)

async def check_and_increment_quota(ctx, command_name):
    if await is_mod_owner(ctx): return True
    quotas = load_json(QUOTAS_FILE, dict)
    user_id = str(ctx.author.id)
    today = discord.utils.utcnow().strftime("%Y-%m-%d")
    if user_id not in quotas or quotas[user_id].get("date") != today:
        quotas[user_id] = {"date": today, "kick": 0, "timeout": 0, "warn": 0}
    if quotas[user_id].get(command_name, 0) >= 10: return False
    quotas[user_id][command_name] = quotas[user_id].get(command_name, 0) + 1
    save_json(QUOTAS_FILE, quotas)
    return True

def is_whitelisted(guild_id, user_id):
    wl_data = load_json(WHITELIST_FILE, dict)
    return str(user_id) in wl_data.get(str(guild_id), [])

def is_priority_whitelisted(guild_id, user_id):
    pwl_data = load_json(PRIORITY_WHITELIST_FILE, dict)
    return str(user_id) in pwl_data.get(str(guild_id), [])

@bot.check
async def global_dynamic_cooldown(ctx):
    if await is_mod_owner(ctx): return True
    now = discord.utils.utcnow().timestamp()
    user_id = str(ctx.author.id)
    if user_id not in user_cooldowns:
        user_cooldowns[user_id] = {'last_used': 0, 'spam_hits': 0, 'penalty_until': 0}
    cd_data = user_cooldowns[user_id]
    if now < cd_data['penalty_until']:
        raise DynamicRateLimitError(f"chill on the commands. try again in {int(cd_data['penalty_until'] - now)} secs.")
    if now - cd_data['last_used'] < 5:
        cd_data['spam_hits'] += 1
        if cd_data['spam_hits'] >= 3:
            cd_data['penalty_until'] = now + 60
            cd_data['spam_hits'] = 0
            raise DynamicRateLimitError("you're spamming too hard. take a 60 second timeout.")
        raise DynamicRateLimitError(f"hold up, command on cooldown. wait {int(5 - (now - cd_data['last_used']))} secs.")
    cd_data['spam_hits'] = 0
    cd_data['last_used'] = now
    return True

# ==========================================
# 4. EVENTS
# ==========================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, DynamicRateLimitError):
        await ctx.send(error.message, delete_after=5)
    elif hasattr(error, "original") and isinstance(error.original, DynamicRateLimitError):
        await ctx.send(error.original.message, delete_after=5)
    elif isinstance(error, (commands.MissingPermissions, commands.CheckFailure)):
        await ctx.send("you don't have perms for this.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"you forgot something: {error.param}")
    elif not isinstance(error, commands.CommandNotFound):
        print(f"error: {error}")

@bot.event
async def on_message(message):
    if message.author.bot: 
        return

    # --- MINI AUTO MOD ---
    slur_pattern = r'\bnigg[ae]r?h?s?\b'
    
    if re.search(slur_pattern, message.content.lower()):
        is_immune = False
        if message.guild:
            if message.author == message.guild.owner or await bot.is_owner(message.author):
                is_immune = True
            elif is_whitelisted(message.guild.id, message.author.id) or is_priority_whitelisted(message.guild.id, message.author.id):
                is_immune = True
        
        if not is_immune:
            if message.author.guild_permissions.administrator or message.author.guild_permissions.moderate_members:
                user_id = str(message.author.id)
                now = discord.utils.utcnow().timestamp()
                
                if user_id in mod_slur_warnings and now - mod_slur_warnings[user_id] < 300:
                    try:
                        await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1), reason="Repeated slur use as staff")
                        await message.channel.send(f"told you once already. {message.author.mention} is muted for an hour.")
                        await send_log(message.guild, "Mod Auto-Mute", f"**Mod:** {message.author.mention}\n**Reason:** Repeated slur use", discord.Color.red())
                        del mod_slur_warnings[user_id]
                    except discord.Forbidden:
                        await message.channel.send("tried to mute the mod but i don't have perms.")
                else:
                    mod_slur_warnings[user_id] = now
                    await message.channel.send(f"language buddy, {message.author.mention} you're getting muted next time you say it.")
            
            else:
                try:
                    await message.delete()
                    await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1), reason="Slur use (Auto-Mod)")
                    await message.channel.send(f"{message.author.mention} got muted for an hour for that. chill.")
                    await send_log(message.guild, "Auto-Mod Mute", f"**User:** {message.author.mention}\n**Reason:** Slur usage", discord.Color.orange())
                except discord.Forbidden:
                    await message.channel.send(f"tried to mute {message.author.mention} but i don't have permissions.")
            return 

    # --- HONEYPOT ---
    if message.channel.id in bot.honeypot_channels:
        if message.author != message.guild.owner and not message.author.guild_permissions.administrator:
            try:
                await message.guild.ban(message.author, reason="honeypot", delete_message_seconds=604800)
                await message.guild.unban(message.author, reason="security unban")
                alert = await message.channel.send(f"busted. {message.author} fell for the honeypot.")
                await alert.delete(delay=10) 
            except discord.Forbidden: pass
            return 

    # --- AFK ---
    afk_data = load_json(AFK_FILE, dict)
    author_id = str(message.author.id)
    if author_id in afk_data:
        del afk_data[author_id]
        save_json(AFK_FILE, afk_data)
        welcome_msg = await message.channel.send(f"wb {message.author.mention}, took off your afk status.")
        await welcome_msg.delete(delay=5)
    
    if message.mentions:
        for mentioned_user in message.mentions:
            mid = str(mentioned_user.id)
            if mid in afk_data:
                await message.channel.send(f"{mentioned_user.display_name} is afk right now: {afk_data[mid]['message']}")

    # --- UWU LOCK ---
    is_uwu_cmd = message.content.lower().startswith(("!sedse uwu", "!uwu", "!sedse lock", "!sedse unlock"))
    uwu_data = load_json(UWULOCK_FILE, dict)
    if not is_uwu_cmd and (uwu_data.get("everyone") or str(message.author.id) in uwu_data):
        uwu_text = uwuify(message.content) if message.content.strip() else random.choice(UWU_EMOJIS)
        if len(uwu_text) > 2000: uwu_text = uwu_text[:1997] + "..."
        try:
            webhooks = await message.channel.webhooks()
            webhook = discord.utils.get(webhooks, name="sedse impersonator") or await message.channel.create_webhook(name="sedse impersonator")
            await webhook.send(content=uwu_text, username=message.author.display_name, avatar_url=message.author.display_avatar.url if message.author.display_avatar else None)
            await message.delete()
        except Exception as e: print(f"uwu error: {e}")
        return

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"bot logged in as {bot.user}")

# ==========================================
# 5. COMMANDS
# ==========================================

@bot.command()
@check_perms("modview", moderate_members=True)
async def modview(ctx):
    embed = discord.Embed(
        title="mod control panel",
        description="select what you want to manage from the menus below.",
        color=0x2b2d31 
    )
    await ctx.send(embed=embed, view=ModView(ctx))

@bot.group(invoke_without_command=True)
async def priority(ctx):
    await ctx.send("you need a subcommand. try '!sedse priority whitelist [user]'.")

@priority.command()
async def whitelist(ctx, member: discord.Member = None):
    pwl_data = load_json(PRIORITY_WHITELIST_FILE, dict)
    gid = str(ctx.guild.id)

    # If no member is mentioned, display the list
    if member is None:
        users = pwl_data.get(gid, [])
        if not users:
            return await ctx.send("the priority whitelist is currently empty.")
        
        mentions = [f"<@{uid}>" for uid in users]
        embed = discord.Embed(title="priority whitelisted users", description="\n".join(mentions), color=discord.Color.gold())
        return await ctx.send(embed=embed)

    # If a member is mentioned, add them to the whitelist
    if not await is_mod_owner(ctx): return await ctx.send("only sedse can mess with the priority whitelist, back off.")
    if gid not in pwl_data: pwl_data[gid] = []
    if str(member.id) not in pwl_data[gid]:
        pwl_data[gid].append(str(member.id))
        save_json(PRIORITY_WHITELIST_FILE, pwl_data)
        await ctx.send(f"put {member.mention} on the priority whitelist. they can now touch other whitelisted users.")
    else: 
        await ctx.send(f"{member.mention} is already on the priority whitelist.")

@priority.command()
async def unwhitelist(ctx, member: discord.Member):
    if not await is_mod_owner(ctx): return await ctx.send("only sedse can touch this, go away.")
    pwl_data = load_json(PRIORITY_WHITELIST_FILE, dict)
    gid = str(ctx.guild.id)
    if gid in pwl_data and str(member.id) in pwl_data[gid]:
        pwl_data[gid].remove(str(member.id))
        save_json(PRIORITY_WHITELIST_FILE, pwl_data)
        await ctx.send(f"took {member.mention} off the priority whitelist. they lost their privileges.")
    else: 
        await ctx.send(f"{member.mention} isn't even on the priority whitelist.")

@bot.command()
async def whitelist(ctx, member: discord.Member = None):
    wl_data = load_json(WHITELIST_FILE, dict)
    gid = str(ctx.guild.id)
    
    # If no member is mentioned, display the list
    if member is None:
        users = wl_data.get(gid, [])
        if not users:
            return await ctx.send("the whitelist is currently empty.")
            
        mentions = [f"<@{uid}>" for uid in users]
        embed = discord.Embed(title="whitelisted users", description="\n".join(mentions), color=discord.Color.green())
        return await ctx.send(embed=embed)

    # If a member is mentioned, add them to the whitelist
    if not await is_mod_owner(ctx): return await ctx.send("only sedse can mess with the whitelist, back off.")
    if gid not in wl_data: wl_data[gid] = []
    if str(member.id) not in wl_data[gid]:
        wl_data[gid].append(str(member.id))
        save_json(WHITELIST_FILE, wl_data)
        await ctx.send(f"put {member.mention} on the whitelist. they're completely safe now.")
    else: await ctx.send(f"{member.mention} is already on the whitelist.")

@bot.command()
async def unwhitelist(ctx, member: discord.Member):
    if not await is_mod_owner(ctx): return await ctx.send("only sedse can touch this, go away.")
    wl_data = load_json(WHITELIST_FILE, dict)
    gid = str(ctx.guild.id)
    if gid in wl_data and str(member.id) in wl_data[gid]:
        wl_data[gid].remove(str(member.id))
        save_json(WHITELIST_FILE, wl_data)
        await ctx.send(f"took {member.mention} off the whitelist. fair game again.")
    else: await ctx.send(f"{member.mention} isn't even on the whitelist.")

@bot.command(aliases=["uwu"]) 
@check_perms("uwulock", manage_messages=True)
async def uwulock(ctx, arg1: str, arg2: str = None):
    if arg1.lower() == "unlock" and arg2:
        target = arg2
        uwu_data = load_json(UWULOCK_FILE, dict)
        if target.lower() == "everyone":
            if not await is_mod_owner(ctx): return await ctx.send("only sedse can unlock everyone, nice try.")
            if uwu_data.pop("everyone", None):
                save_json(UWULOCK_FILE, uwu_data)
                return await ctx.send("the whole server uwu curse is gone.")
            return await ctx.send("the server isn't globally uwu locked right now.")
        try:
            member = await commands.MemberConverter().convert(ctx, target)
            if str(member.id) in uwu_data:
                del uwu_data[str(member.id)]
                save_json(UWULOCK_FILE, uwu_data)
                return await ctx.send(f"{member.mention} is free from the uwu curse.")
            return await ctx.send(f"{member.mention} isn't uwu locked right now.")
        except: return await ctx.send("can't find that user.")
    member_str = arg2 if arg1.lower() == "lock" and arg2 else arg1
    uwu_data = load_json(UWULOCK_FILE, dict)
    if member_str.lower() == "everyone":
        if not await is_mod_owner(ctx): return await ctx.send("only sedse can do the everyone lock, nice try.")
        if not uwu_data.get("everyone"):
            uwu_data["everyone"] = True
            save_json(UWULOCK_FILE, uwu_data)
            return await ctx.send("the whole server is uwu locked now.")
        return await ctx.send("the whole server is already uwu locked.")
    try:
        member = await commands.MemberConverter().convert(ctx, member_str)
        user_id = str(member.id)
        if user_id not in uwu_data:
            uwu_data[user_id] = True
            save_json(UWULOCK_FILE, uwu_data)
            await ctx.send(f"{member.mention} is uwu locked now.")
        else: await ctx.send(f"{member.mention} is already uwu locked.")
    except: await ctx.send("can't find that user.")

@bot.command()
@check_perms("uwulock", manage_messages=True)
async def uwuunlock(ctx, target: str):
    uwu_data = load_json(UWULOCK_FILE, dict)
    if target.lower() == "everyone":
        if not await is_mod_owner(ctx): return await ctx.send("only sedse can unlock everyone, nice try.")
        if uwu_data.pop("everyone", None):
            save_json(UWULOCK_FILE, uwu_data)
            return await ctx.send("the whole server uwu curse is gone.")
        return await ctx.send("the server isn't globally uwu locked right now.")
    try:
        member = await commands.MemberConverter().convert(ctx, target)
        user_id = str(member.id)
        if user_id in uwu_data:
            del uwu_data[user_id]
            save_json(UWULOCK_FILE, uwu_data)
            await ctx.send(f"{member.mention} is free from the uwu curse.")
        else: await ctx.send(f"{member.mention} isn't uwu locked right now.")
    except: await ctx.send("can't find that user.")

@bot.command()
@commands.is_owner()
async def forcemute(ctx, member: discord.Member, duration_str: str = "1h", *, reason="sedse override"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    duration = parse_duration(duration_str) or timedelta(hours=1)
    exempt = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    roles_to_remove = [r for r in member.roles if r.name != "@everyone" and not r.is_default() and not r.managed and r.id not in exempt]
    role_ids = [r.id for r in roles_to_remove]
    muted_data = load_json(MUTED_ADMINS_FILE, dict)
    muted_data[str(member.id)] = {"roles": role_ids}
    save_json(MUTED_ADMINS_FILE, muted_data)
    try:
        if roles_to_remove: await member.remove_roles(*roles_to_remove, reason=f"force mute by {ctx.author}")
        await member.timeout(discord.utils.utcnow() + duration, reason=reason)
        await ctx.send(f"ripped {len(roles_to_remove)} roles off and force-muted {member.mention} for {duration_str}.")
        await send_log(ctx.guild, "admin force muted", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {reason}", discord.Color.red())
    except discord.Forbidden: await ctx.send("can't mute them. check my role height.")

@bot.command()
@commands.is_owner()
async def forceunmute(ctx, member: discord.Member):
    muted_data = load_json(MUTED_ADMINS_FILE, dict)
    uid = str(member.id)
    if uid in muted_data:
        roles_to_add = [ctx.guild.get_role(rid) for rid in muted_data[uid]["roles"] if ctx.guild.get_role(rid)]
        try:
            await member.timeout(None, reason="force unmute")
            if roles_to_add: await member.add_roles(*roles_to_add)
            del muted_data[uid]
            save_json(MUTED_ADMINS_FILE, muted_data)
            await ctx.send(f"gave back {len(roles_to_add)} roles and unmuted {member.mention}.")
        except discord.Forbidden as e: await ctx.send(f"can't restore roles: {e}")
    else: await ctx.send("they aren't in the force-mute database.")

@bot.command()
@commands.has_permissions(administrator=True)
async def perm(ctx, command_name: str, target: Union[discord.Role, discord.Member]):
    command_name = command_name.lower()
    valid = [c.name for c in bot.commands] + ["all"]
    if command_name not in valid: return await ctx.send("that command doesn't even exist.")
    perms_data = load_json(PERMS_FILE, dict)
    gid = str(ctx.guild.id)
    if gid not in perms_data: perms_data[gid] = {}
    if command_name not in perms_data[gid]: perms_data[gid][command_name] = {"roles": [], "users": []}
    cmd_perms = perms_data[gid][command_name]
    if isinstance(target, discord.Role):
        if target.id in cmd_perms["roles"]: cmd_perms["roles"].remove(target.id); action = "revoked"
        else: cmd_perms["roles"].append(target.id); action = "granted"
        t_name = f"role {target.mention}"
    else:
        if target.id in cmd_perms["users"]: cmd_perms["users"].remove(target.id); action = "revoked"
        else: cmd_perms["users"].append(target.id); action = "granted"
        t_name = f"user {target.mention}"
    save_json(PERMS_FILE, perms_data)
    await ctx.send(f"perms for '{command_name}' {action} for {t_name}.")

@bot.command()
@check_perms("honeypot_setup", administrator=True)
async def honeypot_setup(ctx):
    embed = discord.Embed(title="honeypot setup", description="click below to mess with the honeypot.", color=0xFF0000)
    await ctx.send(embed=embed, view=HoneypotView())

@bot.command()
@check_perms("verify_setup", administrator=True)
async def verify_setup(ctx):
    embed = discord.Embed(title="server verification", description="click below to verify.", color=0x5865F2)
    await ctx.send(embed=embed, view=VerifyView())

@bot.command()
async def menu(ctx):
    await ctx.send("pick a script from down here:", view=JJSView())

@bot.command()
@check_perms("verify", manage_roles=True)
async def verify(ctx, member: discord.Member):
    roles = [ctx.guild.get_role(ROLE_SCRIPT_USER_ID), ctx.guild.get_role(ROLE_VERIFIED_ID)]
    roles = [r for r in roles if r]
    if not roles: return await ctx.send("couldn't find the roles.")
    try:
        await member.add_roles(*roles)
        await ctx.send(f"verified {member.mention}.")
    except discord.Forbidden: await ctx.send("check my role height.")

@bot.command()
@check_perms("impersonate", manage_webhooks=True)
async def impersonate(ctx, member: discord.Member, channel: discord.TextChannel, *, message: str):
    webhooks = await channel.webhooks()
    webhook = discord.utils.get(webhooks, name="sedse impersonator") or await channel.create_webhook(name="sedse impersonator")
    try:
        await webhook.send(content=message, username=member.display_name, avatar_url=member.display_avatar.url if member.display_avatar else None)
        try: await ctx.message.delete()
        except: pass
        confirmation = await ctx.send(f"impersonated {member.display_name} in {channel.mention}.")
        await confirmation.delete(delay=3)
    except Exception as e: await ctx.send(f"failed: {e}")

@bot.command()
async def afk(ctx, *, message="afk"):
    afk_data = load_json(AFK_FILE, dict)
    afk_data[str(ctx.author.id)] = {"message": message}
    save_json(AFK_FILE, afk_data)
    await ctx.send(f"{ctx.author.mention}, you're now afk: {message}")

@bot.command()
@check_perms("kick", kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="no reason"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    if not await check_and_increment_quota(ctx, "kick"): return await ctx.send(f"{ctx.author.mention}, you hit your daily limit of 10 kicks.")
    await member.kick(reason=reason)
    await ctx.send(f"kicked {member.mention}. reason: {reason}")
    await send_log(ctx.guild, "user kicked", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {reason}", discord.Color.orange())

@bot.command()
@check_perms("ban", ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="no reason"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    is_owner = await is_mod_owner(ctx)
    if (not reason or reason.strip() == "no reason") and not is_owner:
        view = ReasonView(ctx)
        msg = await ctx.send(f"{ctx.author.mention} {ctx.author.mention} yo, you need to give a reason. click the button within 5 mins or you're getting muted.", view=view)
        await view.wait()
        if not view.reason: return 
        reason = view.reason
        try: await msg.delete()
        except: pass
    if is_owner:
        await member.ban(reason=reason)
        await ctx.send(f"banned {member.mention}. reason: {reason}")
        await send_log(ctx.guild, "user banned", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {reason}", discord.Color.red())
        return
    try:
        await member.timeout(discord.utils.utcnow() + timedelta(days=27, hours=23), reason=f"pending sedse review: {reason}")
        await ctx.send(f"{member.mention} is muted pending sedse's approval for the ban.")
    except discord.Forbidden: await ctx.send(f"can't mute {member.mention}, but awaiting sedse's approval anyway.")
    owner = ctx.guild.owner
    confirm_view = OwnerBanConfirmView(member, reason, ctx.author)
    await ctx.send(f"{owner.mention} a ban request was made by {ctx.author.mention} for {member.mention}.\n**reason:** {reason}", view=confirm_view)

@bot.command(aliases=["mute"])
@check_perms("timeout", moderate_members=True)
async def timeout(ctx, member: discord.Member, duration_str: str = None, *, reason="no reason"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    is_owner = await is_mod_owner(ctx)
    duration = parse_duration(duration_str) or timedelta(days=27, hours=23)
    actual_reason = reason
    if (not actual_reason or actual_reason.strip() == "no reason") and not is_owner:
        view = ReasonView(ctx)
        msg = await ctx.send(f"{ctx.author.mention} {ctx.author.mention} yo, you need to give a reason. click the button within 5 mins or you're getting muted.", view=view)
        await view.wait()
        if not view.reason: return
        actual_reason = view.reason
        try: await msg.delete()
        except: pass
    if not await check_and_increment_quota(ctx, "timeout"): return await ctx.send(f"{ctx.author.mention}, you hit your daily limit of 10 mutes.")
    try:
        await member.timeout(discord.utils.utcnow() + duration, reason=actual_reason)
        await ctx.send(f"muted {member.mention}. reason: {actual_reason}")
        await send_log(ctx.guild, "user timed out", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {actual_reason}", discord.Color.gold())
    except discord.Forbidden: await ctx.send("can't mute them. use `!sedse forcemute` if they're an admin (sedse only).")

@bot.command()
@check_perms("warn", manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="no reason"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    if (not reason or reason.strip() == "no reason") and not await is_mod_owner(ctx):
        view = ReasonView(ctx)
        msg = await ctx.send(f"{ctx.author.mention} {ctx.author.mention} yo, you need to give a reason. click the button within 5 mins or you're getting muted.", view=view)
        await view.wait()
        if not view.reason: return 
        reason = view.reason
        try: await msg.delete()
        except: pass
    if not await check_and_increment_quota(ctx, "warn"): return await ctx.send(f"{ctx.author.mention}, you hit your daily limit of 10 warns.")
    warnings = load_json(WARNINGS_FILE, dict)
    uid = str(member.id)
    if uid not in warnings: warnings[uid] = []
    warnings[uid].append({"reason": reason, "mod": ctx.author.name, "date": str(discord.utils.utcnow())[:19]})
    save_json(WARNINGS_FILE, warnings)
    await ctx.send(f"warned {member.mention}. reason: {reason}")
    await send_log(ctx.guild, "user warned", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {reason}", discord.Color.yellow())

@bot.command()
@check_perms("softban", ban_members=True)
async def softban(ctx, member: discord.Member, *, reason="no reason"):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    await member.ban(reason=f"softban: {reason}", delete_message_seconds=604800)
    await ctx.guild.unban(member, reason="softban release")
    await ctx.send(f"softbanned {member.mention} (kicked and deleted their messages).")
    await send_log(ctx.guild, "user softbanned", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}\n**reason:** {reason}", discord.Color.orange())

@bot.command()
@check_perms("unban", ban_members=True)
async def unban(ctx, user: discord.User):
    await ctx.guild.unban(user, reason=f"unbanned by {ctx.author}")
    await ctx.send(f"unbanned {user.mention}.")
    await send_log(ctx.guild, "user unbanned", f"**user:** {user.mention}\n**mod:** {ctx.author.mention}", discord.Color.green())

@bot.command(aliases=["unmute"])
@check_perms("untimeout", moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"untimeout by {ctx.author}")
    await ctx.send(f"unmuted {member.mention}.")
    await send_log(ctx.guild, "user untimed out", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}", discord.Color.green())

@bot.command()
@check_perms("purge", manage_messages=True)
async def purge(ctx, amount: int):
    if amount <= 0: return await ctx.send("amount gotta be more than 0.")
    deleted = await ctx.channel.purge(limit=amount + 1)
    msgs = [msg for msg in deleted if msg.id != ctx.message.id][:100]
    purged_messages_cache[ctx.channel.id] = msgs
    await ctx.send(f"nuked {len(msgs)} messages. use '!sedse unpurge' if you messed up.", delete_after=5)

@bot.command()
@check_perms("unpurge", manage_messages=True)
async def unpurge(ctx, action: str = None):
    global active_unpurges
    if action and action.lower() == "stop":
        if active_unpurges.get(ctx.channel.id, False):
            active_unpurges[ctx.channel.id] = False
            await ctx.send("stopping the unpurge...")
        else: await ctx.send("no unpurge running here.")
        return
    msgs = purged_messages_cache.get(ctx.channel.id, [])
    if not msgs: return await ctx.send("didn't find any recently nuked messages.")
    active_unpurges[ctx.channel.id] = True
    await ctx.send(f"bringing back {len(msgs)} messages... (type '!sedse unpurge stop' to cancel)")
    webhooks = await ctx.channel.webhooks()
    webhook = discord.utils.get(webhooks, name="sedse restore") or await ctx.channel.create_webhook(name="sedse restore")
    restored = 0
    for msg in reversed(msgs):
        if not active_unpurges.get(ctx.channel.id, False):
            await ctx.send(f"stopped early. brought back {restored} messages.")
            purged_messages_cache[ctx.channel.id] = []
            return
        if msg.content or msg.embeds:
            try:
                await webhook.send(content=msg.content or None, embeds=msg.embeds, username=msg.author.display_name, avatar_url=msg.author.display_avatar.url if msg.author.display_avatar else None)
                restored += 1
                await asyncio.sleep(0.1) 
            except: pass
    active_unpurges[ctx.channel.id] = False
    purged_messages_cache[ctx.channel.id] = []
    await ctx.send(f"brought back {restored} messages.")

@bot.command()
@check_perms("warnings", manage_messages=True)
async def warnings(ctx, member: discord.Member):
    data = load_json(WARNINGS_FILE, dict)
    user_warns = data.get(str(member.id), [])
    if not user_warns: return await ctx.send(f"{member.display_name} is clean, no warnings.")
    embed = discord.Embed(title=f"warnings for {member.display_name}", color=discord.Color.gold())
    for i, w in enumerate(user_warns, 1):
        embed.add_field(name=f"warn {i} - by {w['mod']}", value=f"**reason:** {w['reason']}\n**date:** {w['date']}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@check_perms("lock", manage_channels=True)
async def lock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send(f"locked down {channel.mention}.")

@bot.command()
@check_perms("unlock", manage_channels=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    await channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send(f"unlocked {channel.mention}.")

@bot.command()
@check_perms("nick", manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, name: str):
    await member.edit(nick=name)
    await ctx.send(f"changed {member.mention}'s nickname to **{name}**.")

@bot.command()
@check_perms("log_channel", administrator=True)
async def log_channel(ctx, channel: discord.TextChannel):
    settings = load_json(SETTINGS_FILE, dict)
    if str(ctx.guild.id) not in settings: settings[str(ctx.guild.id)] = {}
    settings[str(ctx.guild.id)]["log_channel"] = channel.id
    save_json(SETTINGS_FILE, settings)
    await ctx.send(f"mod logs are gonna go to {channel.mention} now.")

@bot.command(aliases=["conflip"])
async def coinflip(ctx):
    outcome = random.choice(["heads", "tails"])
    await ctx.send(f"coin flipped: **{outcome}**")

@bot.command()
@check_perms("annihilate", administrator=True)
async def annihilate(ctx, member: discord.Member):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    exempt = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    roles_to_remove = [r for r in member.roles if r.id not in exempt and r.name != "@everyone"]
    if not roles_to_remove: return await ctx.send(f"{member.mention} doesn't have any roles i can take.")
    try:
        await member.remove_roles(*roles_to_remove, reason="annihilation")
        await ctx.send(f"annihilated {member.mention}. took away {len(roles_to_remove)} roles.")
        await send_log(ctx.guild, "user annihilated", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}", discord.Color.dark_red())
    except discord.Forbidden: await ctx.send("don't have perms.")

@bot.command()
@check_perms("hakai", administrator=True)
async def hakai(ctx, member: discord.Member):
    if is_priority_whitelisted(ctx.guild.id, member.id): return await ctx.send(f"{member.mention} is on the priority whitelist, can't touch them.")
    if is_whitelisted(ctx.guild.id, member.id) and not is_priority_whitelisted(ctx.guild.id, ctx.author.id): return await ctx.send(f"{member.mention} is on the whitelist, can't touch them.")
    exempt = [ROLE_SCRIPT_USER_ID, ROLE_VERIFIED_ID]
    roles_to_remove = [r for r in member.roles if r.id not in exempt and r.name != "@everyone"]
    if not roles_to_remove: return await ctx.send(f"{member.mention} doesn't have any roles i can take.")
    try:
        await member.remove_roles(*roles_to_remove, reason="hakai")
        await ctx.send(f"hakai'd {member.mention}. wiped {len(roles_to_remove)} roles from existence.")
        await send_log(ctx.guild, "user hakai'd", f"**user:** {member.mention}\n**mod:** {ctx.author.mention}", discord.Color.dark_purple())
    except discord.Forbidden: await ctx.send("don't have perms.")

@bot.command()
async def badapple(ctx, action: str = "start"):
    global active_badapples
    if action.lower() in ["end", "stop"]:
        if active_badapples.get(ctx.channel.id):
            active_badapples[ctx.channel.id] = False
            await ctx.send("stopping bad apple...")
        else: await ctx.send("bad apple isn't playing here.")
        return
    if action.lower() == "start":
        if active_badapples.get(ctx.channel.id): return await ctx.send("bad apple is already playing. type '!sedse badapple end' to stop it.")
        frames_file = "bad_apple.json"
        if not os.path.exists(frames_file):
            frames = ["#####\n#...#\n#.#.#\n#...#\n#####", ".....\n.###.\n.#.#.\n.###.\n.....", "[missing bad_apple.json]"]
            await ctx.send("bad_apple.json missing. using placeholder.")
        else:
            try:
                with open(frames_file, "r", encoding="utf-8") as f: frames = json.load(f)
            except Exception as e: return await ctx.send(f"couldn't load frames: {e}")
        active_badapples[ctx.channel.id] = True
        msg = await ctx.send("```\nloading bad apple...\n```")
        for frame in frames:
            if not active_badapples.get(ctx.channel.id):
                try: await msg.edit(content="```\nbad apple stopped.\n```")
                except: pass
                break
            try:
                await msg.edit(content=f"```\n{frame[:1980]}\n```")
                await asyncio.sleep(1.5) 
            except discord.errors.HTTPException as e:
                if e.status == 429: await asyncio.sleep(5)
                else: break 
        active_badapples[ctx.channel.id] = False

@bot.command()
@check_perms("hamzbid", manage_webhooks=True)
async def hamzbid(ctx):
    target_id = 1425810901490991104
    target_messages = []
    async for msg in ctx.channel.history(limit=200):
        if msg.author.id == target_id and msg.content.strip():
            target_messages.append(msg)
            if len(target_messages) == 10: break
    if not target_messages: return await ctx.send("couldn't find any recent messages.")
    target_messages.reverse()
    combined = " ".join([m.content for m in target_messages])
    if len(combined) > 2000: combined = combined[:1997] + "..."
    user = target_messages[0].author
    webhooks = await ctx.channel.webhooks()
    webhook = discord.utils.get(webhooks, name="sedse impersonator") or await ctx.channel.create_webhook(name="sedse impersonator")
    try:
        await webhook.send(content=combined, username=user.display_name, avatar_url=user.display_avatar.url if user.display_avatar else None)
        try: await ctx.message.delete()
        except: pass
    except Exception as e: await ctx.send(f"failed: {e}")

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member = None):
    if user2 is None: user2 = ctx.author
    random.seed(user1.id + user2.id)
    pct = random.randint(0, 100)
    random.seed()
    if pct == 100: s = "just get married already."
    elif pct > 75: s = "perfect match."
    elif pct > 50: s = "some potential here."
    elif pct > 25: s = "stay friends."
    else: s = "absolutely not."
    embed = discord.Embed(title="love calculator", description=f"**{user1.display_name}** & **{user2.display_name}**\n\ncompatibility: **{pct}%**\n*{s}*", color=discord.Color.pink())
    await ctx.send(embed=embed)

@bot.command()
async def iq(ctx, member: discord.Member = None):
    member = member or ctx.author
    random.seed(member.id)
    score = random.randint(10, 200)
    random.seed()
    if score < 50: c = "actual room temp iq."
    elif score < 90: c = "not looking too bright."
    elif score < 130: c = "pretty average."
    else: c = "alright albert einstein."
    embed = discord.Embed(title="iq test", description=f"**{member.display_name}**'s iq is **{score}**.\n*{c}*", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
async def ratio(ctx, member: discord.Member = None):
    pieces = ["l", "ratio", "skill issue", "touch grass", "cope", "seethe", "mald", "didn't ask", "you fell off", "get real", "no maidens", "bozo"]
    text = " + ".join(random.sample(pieces, random.randint(4, 7)))
    await ctx.send(f"{member.mention} {text}" if member else text)

@bot.command()
async def doxx(ctx, member: discord.Member = None):
    member = member or ctx.author
    ip = f"{random.randint(11,250)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
    mac = ":".join(["%02x" % random.randint(0, 255) for _ in range(6)]).upper()
    lat, lon = round(random.uniform(-90, 90), 4), round(random.uniform(-180, 180), 4)
    embed = discord.Embed(title="target acquired", color=0x00FF00)
    embed.add_field(name="target", value=member.mention, inline=False)
    embed.add_field(name="ipv4", value=f"`{ip}`", inline=True)
    embed.add_field(name="mac", value=f"`{mac}`", inline=True)
    embed.add_field(name="coords", value=f"`{lat}, {lon}`", inline=False)
    embed.add_field(name="isp", value="`spectrum / at&t`", inline=True)
    embed.set_footer(text="info is 100% accurate (real)")
    await ctx.send(embed=embed)

@bot.command()
async def zalgo(ctx, *, text: str):
    marks = [chr(i) for i in range(0x0300, 0x036F)]
    res = "".join([char + "".join(random.choices(marks, k=random.randint(3, 8))) for char in text])
    await ctx.send(res[:2000])

@bot.command()
async def rizz(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("you gotta ping someone to rizz them up.")
        
    fallback_lines = [
        "Are you a keyboard? Because you're just my type.",
        "Are you a parking ticket? Because you've got FINE written all over you.",
        "If you were a vegetable, you'd be a cute-cumber.",
        "Do you have a map? I keep getting lost in your eyes.",
        "Are you French? Because Eiffel for you.",
        "Is your name Google? Because you have everything I've been searching for."
    ]
    
    pickup_line = random.choice(fallback_lines)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Rizz API alternative endpoint
            async with session.get("https://rizzapi.vercel.app/random", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    if "text" in data:
                        pickup_line = data["text"]
    except Exception as e:
        print(f"pickup line api failed: {e}")
        
    await ctx.send(f"{member.mention} {pickup_line}")

@bot.command()
async def umarizz(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("you gotta ping someone to umarizz them up.")
        
    try:
        with open(UMARIZZ_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        lines = data.get("umamusume_pickup_lines", [])
        if not lines:
            raise ValueError("No pickup lines found in the file.")
            
        # Pick a random line
        pickup_line = random.choice(lines)["line"]
    except Exception as e:
        print(f"umarizz error: {e}")
        # Ultimate fallback just in case the file gets deleted/corrupted
        pickup_line = "Are you a Trainer? Because my heart starts racing the moment you're around."
        
    await ctx.send(f"{member.mention} {pickup_line}")

# ==========================================
# MUSIC SYSTEM SETUP
# ==========================================

import yt_dlp
import imageio_ffmpeg
import aiohttp
import re
import random
import discord

music_queues = {}
current_song = {}
loop_mode = {} # 0: Off, 1: Loop Song, 2: Loop Queue

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'scsearch',
    'source_address': '0.0.0.0',
    # NEW: This reads your YouTube login cookies, completely destroying the "Sign in" block!
    'cookiefile': 'cookies.txt',
    'extractor_args': {
        'youtube': ['player_client=ios,web_safari'] 
    }
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

def play_next(ctx):
    """Function to play the next song and handle looping."""
    guild_id = ctx.guild.id
    
    # Check loop mode and re-insert the last song if needed
    last_song = current_song.get(guild_id)
    l_mode = loop_mode.get(guild_id, 0)
    
    if last_song:
        if l_mode == 1:
            # Loop Song: Insert back to the front
            music_queues.setdefault(guild_id, []).insert(0, last_song)
        elif l_mode == 2:
            # Loop Queue: Append to the end
            music_queues.setdefault(guild_id, []).append(last_song)
            
    current_song[guild_id] = None

    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        song = music_queues[guild_id].pop(0)
        current_song[guild_id] = song
        
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        source = discord.FFmpegPCMAudio(song['url'], executable=ffmpeg_path, **FFMPEG_OPTIONS)
        
        # Open-source bots use VolumeTransformer to allow dynamic volume changes
        volume_adjusted = discord.PCMVolumeTransformer(source, volume=1.0)
        song['source'] = volume_adjusted 
        
        if ctx.voice_client:
            ctx.voice_client.play(volume_adjusted, after=lambda e: play_next(ctx))
            if l_mode != 1: # Don't spam the chat if a single song is on repeat
                bot.loop.create_task(ctx.send(f"🎵 Now playing: **{song['title']}**"))
    else:
        if ctx.voice_client and ctx.voice_client.is_connected():
            bot.loop.create_task(ctx.send("Queue is empty. Add more songs to keep the party going!"))

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"Joined {channel.mention}!")
    else:
        await ctx.send("You need to be in a voice channel first!")

@bot.command()
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        return await ctx.send("You need to be in a voice channel first!")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()

    msg = await ctx.send(f"🔍 Searching for `{query}`...")
    
    # Spotify workaround
    if "spotify.com" in query:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(query) as resp:
                    text = await resp.text()
                    match = re.search(r'<title>(.*?)</title>', text)
                    if match:
                        query = match.group(1).split(" | ")[0]
        except Exception:
            pass 

    is_url = query.startswith('http')
    search_query = query if is_url else f"scsearch:{query}"
    
    try:
        data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
    except Exception:
        return await msg.edit(content=f"❌ Blocked by provider or invalid link. Try searching the song by name instead!")
    
    if 'entries' in data and len(data['entries']) > 0:
        data = data['entries'][0]
    elif 'entries' in data:
        return await msg.edit(content="Couldn't find any results for that search.")
        
    song = {
        'title': data.get('title'),
        'url': data.get('url'),
        'webpage_url': data.get('webpage_url', data.get('url'))
    }
    
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = []
        
    music_queues[guild_id].append(song)
    
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await msg.edit(content="Song found! Starting playback.")
        play_next(ctx)
    else:
        await msg.edit(content=f"Added to queue: **{song['title']}** (Position: {len(music_queues[guild_id])})")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        # Skipping is as simple as stopping the current audio, which triggers the 'after' callback -> play_next()
        ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped.")
    else:
        await ctx.send("Nothing is playing right now.")

@bot.command()
async def loop(ctx):
    guild_id = ctx.guild.id
    current_mode = loop_mode.get(guild_id, 0)
    
    # Cycle through: 0 (Off) -> 1 (Song) -> 2 (Queue)
    new_mode = (current_mode + 1) % 3
    loop_mode[guild_id] = new_mode
    
    if new_mode == 0:
        await ctx.send("🔁 Looping is now **OFF**.")
    elif new_mode == 1:
        await ctx.send("🔂 Looping **CURRENT SONG**.")
    elif new_mode == 2:
        await ctx.send("🔁 Looping **ENTIRE QUEUE**.")

@bot.command()
async def shuffle(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queues and len(music_queues[guild_id]) > 1:
        random.shuffle(music_queues[guild_id])
        await ctx.send("🔀 Queue has been shuffled!")
    else:
        await ctx.send("Not enough songs in the queue to shuffle.")

@bot.command(aliases=["nowplaying"])
async def np(ctx):
    guild_id = ctx.guild.id
    song = current_song.get(guild_id)
    if song:
        embed = discord.Embed(title="Now Playing 🎵", description=f"**[{song['title']}]({song['webpage_url']})**", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        await ctx.send("Nothing is currently playing.")

@bot.command()
async def volume(ctx, vol: int):
    if 1 <= vol <= 100:
        guild_id = ctx.guild.id
        song = current_song.get(guild_id)
        if ctx.voice_client and ctx.voice_client.is_playing() and song and 'source' in song:
            song['source'].volume = vol / 100
            await ctx.send(f"🔊 Volume set to **{vol}%**")
        else:
            await ctx.send("Nothing is playing to change the volume of.")
    else:
        await ctx.send("Please choose a volume between 1 and 100.")

@bot.command()
async def clear(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queues:
        music_queues[guild_id].clear()
        await ctx.send("🗑️ Cleared the queue.")
    else:
        await ctx.send("The queue is already empty.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        guild_id = ctx.guild.id
        if guild_id in music_queues:
            music_queues[guild_id].clear()
        if guild_id in current_song:
            current_song[guild_id] = None
        loop_mode[guild_id] = 0
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("Stopped the music, cleared the queue, and left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def queue(ctx):
    guild_id = ctx.guild.id
    if guild_id in music_queues and len(music_queues[guild_id]) > 0:
        q = music_queues[guild_id]
        queue_list = "\n".join([f"**{idx+1}.** {song['title']}" for idx, song in enumerate(q[:10])])
        if len(q) > 10:
            queue_list += f"\n*...and {len(q)-10} more.*"
        
        embed = discord.Embed(title="Current Music Queue", description=queue_list, color=discord.Color.blurple())
        await ctx.send(embed=embed)
    else:
        await ctx.send("The queue is currently empty.")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Music paused.")
    else:
        await ctx.send("Nothing is playing right now.")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Music resumed.")
    else:
        await ctx.send("Music isn't paused or nothing is in the player.")

@bot.command()
async def remove(ctx, *, identifier: str):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or len(music_queues[guild_id]) == 0:
        return await ctx.send("The queue is empty.")
        
    q = music_queues[guild_id]
    
    if identifier.isdigit():
        idx = int(identifier) - 1
        if 0 <= idx < len(q):
            removed = q.pop(idx)
            return await ctx.send(f"Removed **{removed['title']}** from the queue.")
        else:
            return await ctx.send("Invalid position number in queue.")
    
    for idx, song in enumerate(q):
        if identifier.lower() in song['title'].lower():
            removed = q.pop(idx)
            return await ctx.send(f"Removed **{removed['title']}** from the queue.")
            
    await ctx.send("Couldn't find that song in the queue.")
# ==========================================
# 6. RUN
# ==========================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    try: bot.run(TOKEN, log_handler=None) 
    except Exception as e: print(f"critical error: {e}")
else: print("critical error: no discord_token found!")
