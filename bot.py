import os
import json
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

# =====================
# ENV
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
CHANNEL_ID = int(os.environ["FLIGHT_CHANNEL_ID"])
STATE_CELL = "A1"  # Where to store the Discord message ID
print("JSON length:", len(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")))

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
        rows[2:],  # skip headers
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
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return "❌ Channel not found"

    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows or len(rows) < 2:
        return "⚠️ Sheet empty"

    embed = build_embed(rows)

    posted_message_id = rows[0][0] if rows[0] else None

    if posted_message_id and not force_new:
        try:
            msg = await channel.fetch_message(int(posted_message_id))
            await msg.edit(embed=embed)
            return "🔁 Message updated"
        except (discord.NotFound, discord.Forbidden):
            posted_message_id = None

    # Post new message if missing
    msg = await channel.send(embed=embed)
    write_message_id(SPREADSHEET_SHEET, msg.id, cell=STATE_CELL)
    return "🆕 New message posted"

    # Read message ID from sheet
    posted_message_id = rows[0][0] if rows[0] else None

    if posted_message_id and not force_new:
        try:
            msg = await channel.fetch_message(int(posted_message_id))
            await msg.edit(embed=embed)
            return "✅ Updated existing message"
        except discord.NotFound:
            posted_message_id = None

    # Post new message
    msg = await channel.send(embed=embed)
    write_message_id(SPREADSHEET_SHEET, msg.id, cell=STATE_CELL)
    return "🆕 Posted new message"

# =====================
# LOOP
# =====================
@tasks.loop(minutes=5)
async def flight_task():
    try:
        result = await update_flight_message()
        print(f"[FlightTask] {result}")
    except Exception as e:
        print("❌ Flight task crashed:", e)
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
    rows = get_sheet_values(SPREADSHEET_SHEET)
    posted_message_id = rows[0][0] if rows[0] else None
    msg = f"📌 Message ID: `{posted_message_id}`" if posted_message_id else "⚠️ No message stored"
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
