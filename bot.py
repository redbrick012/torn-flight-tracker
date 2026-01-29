import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
from sheets import get_sheet_values, write_message_id

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "travelDestinations")
CHANNEL_ID = int(os.environ["FLIGHT_CHANNEL_ID"])

# =====================
# DISCORD SETUP
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
# BUILD EMBED
# =====================
def build_embed(rows):
    embed = discord.Embed(
        title="✈️ Smugglers Flight Paths",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    sorted_rows = sorted(
        rows[2:], key=lambda r: r[0].lower() if len(r) > 0 and r[0] else ""
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

    embed.set_footer(text="Auto-updates via GitHub Actions")
    return embed

# =====================
# POST OR UPDATE MESSAGE
# =====================
async def update_flight_message(channel):
    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows:
        return "❌ No sheet data"
    
    embed = build_embed(rows)

    # Try reading existing message ID from sheet
    existing_id = rows[0][0] if rows[0] else None
    if existing_id:
        try:
            msg = await channel.fetch_message(int(existing_id))
            await msg.edit(embed=embed)
            return f"✅ Updated existing message {existing_id}"
        except discord.NotFound:
            existing_id = None

    # Post new message
    msg = await channel.send(embed=embed)
    write_message_id(SPREADSHEET_SHEET, msg.id, cell="A1")
    return f"🆕 Posted new message {msg.id}"

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found")
        return
    result = await update_flight_message(channel)
    print(result)
    await bot.close()  # stop bot after posting once

# =====================
# RUN
# =====================
bot.run(DISCORD_TOKEN)
