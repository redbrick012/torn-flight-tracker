import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

from sheets import get_sheet_values

# =====================
# ENV
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
SPREADSHEET_SHEET = os.environ.get("FLIGHT_SHEET", "Flights")
CHANNEL_ID = int(os.environ["FLIGHT_CHANNEL_ID"])

# =====================
# DISCORD
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

posted_message_id = None

COUNTRY_EMOJIS = {
    "Torn": "<:city:1458205750617833596>",
    "Mexico": "<:mx:1458203844474572801>",
    "Cayman Islands": "<:ky:1458203876544221459>",
    "Canada": "<:ca:1458204026813415517>",
    "Hawaii": "<:ushi:1458203802342522981>",  # US state, not country
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

    for row in rows[2:]:  # skip headers
        if len(row) < 7:
            continue

        dest, outb, inbound, returning, purch, travsug, icc = row[:7]

        # Safe numeric display
        outb = outb or "0"
        inbound = inbound or "0"
        returning = returning or "0"

        flag = country_emoji(dest)

        embed.add_field(
            name=f"{flag} {dest}",
            value=(
                f"🛫 Out: **{outb}** "
                f"🛬 In: **{inbound}** "
                f"↩ Return: **{returning}**\n"
                f"📦 Item: **{purch}**"
            ),
            inline=False
        )

    embed.set_footer(
        text="Auto-updates every 5 minutes · Business Class recommended"
    )
    return embed


# =====================
# LOOP
# =====================
@tasks.loop(minutes=5)
async def flight_task():
    global posted_message_id

    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    rows = get_sheet_values(SPREADSHEET_SHEET)
    if not rows:
        return

    embed = build_embed(rows)

    if posted_message_id:
        try:
            msg = await channel.fetch_message(posted_message_id)
            await msg.edit(embed=embed)
        except discord.NotFound:
            msg = await channel.send(embed=embed)
            posted_message_id = msg.id
    else:
        msg = await channel.send(embed=embed)
        posted_message_id = msg.id

# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Flight bot logged in as {bot.user}")
    if not flight_task.is_running():
        flight_task.start()

# =====================
# RUN
# =====================
bot.run(DISCORD_TOKEN)
