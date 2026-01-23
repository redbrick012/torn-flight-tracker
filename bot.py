import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

from sheets import get_sheet_values

# =====================
# ENV
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
CHANNEL_ID = int(os.environ["FLIGHT_CHANNEL_ID"])

STATE_FILE = "flight_state.json"

# =====================
# STATE
# =====================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()
posted_message_id = state.get("posted_message_id")

# =====================
# DISCORD
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =====================
# FLAGS
# =====================
COUNTRY_EMOJIS = {
    "Torn": "<:city:1458205750617833596>",
    "Mexico": "<:mx:1458203844474572801>",
    "Cayman Islands": "<:ky:1458203876544221459>",
    "Canada": "<:ca:1458204026813415517>",
    "Hawaii": "<:ushi:1458203802342522981>",
    "United Kingdom": "<:gb:1458203934647910441>",
    "Argentina": "<:ar:1458204051970986170>",
    "Switzerland": "<:ch:1458203997964861590>",
    "Japan": "<:jp:1458203900594094270>",
    "China": "<:cn:1458203968059474042>",
    "UAE": "<:ae:1458203747749728610>",
    "South Africa": "<:za:1458204114524569640>",
}

def country_emoji(country: str) -> str:
    return COUNTRY_EMOJIS.get(country, "🌍")

# =====================
# EMBED BUILDER
# =====================
def build_embed(rows):
    embed = discord.Embed(
        title="✈️ Smugglers Flight Paths",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    sorted_rows = sorted(
        rows[2:],
        key=lambda r: r[0].lower() if len(r) > 0 and r[0] else ""
    )

    for row in sorted_rows:
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        outb = outb or "-"
        inbound = inbound or "-"
        returning = returning or "-"
        purch = purch or "-"
        icc = icc or ""

        flag = country_emoji(dest)

        embed.add_field(
            name=f"{flag}{icc} {dest}",
            value=(
                f"🛫 Out: **{outb}** "
                f"🛬 In: **{inbound}** "
                f"↩ Return: **{returning}**\n"
                f"📦 Item: **{purch}**"
            ),
            inline=False
        )

    embed.set_footer(text="Auto-updates every 5 minutes")
    return embed

# =====================
# UPDATE LOGIC
# =====================
async def update_flight_message(force_new=False):
    global posted_message_id, state

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return "❌ Channel not found"

    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows:
        return "❌ No sheet data"

    embed = build_embed(rows)

    if posted_message_id and not force_new:
        try:
            msg = await channel.fetch_message(posted_message_id)
            await msg.edit(embed=embed)
            return "✅ Updated existing message"
        except discord.NotFound:
            posted_message_id = None

    msg = await channel.send(embed=embed)
    posted_message_id = msg.id
    state["posted_message_id"] = msg.id
    save_state(state)

    return "🆕 Posted new message"

# =====================
# LOOP
# =====================
@tasks.loop(minutes=5)
async def flight_task():
    await update_flight_message()

# =====================
# SLASH COMMANDS
# =====================
@bot.tree.command(name="refresh", description="Force refresh the flight embed")
async def refresh(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    result = await update_flight_message()
    await interaction.followup.send(result, ephemeral=True)

@bot.tree.command(name="forcepost", description="Post a brand new message")
async def forcepost(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    result = await update_flight_message(force_new=True)
    await interaction.followup.send(result, ephemeral=True)

@bot.tree.command(name="status", description="Show bot message status")
async def status(interaction: discord.Interaction):
    msg = (
        f"📌 Message ID: `{posted_message_id}`"
        if posted_message_id
        else "⚠️ No message stored"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.tree.sync()
    if not flight_task.is_running():
        flight_task.start()

# =====================
# RUN
# =====================
bot.run(DISCORD_TOKEN)
