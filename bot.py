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

# =====================
# EMBED BUILDER
# =====================
def build_embed(rows):
    embed = discord.Embed(
        title="✈️ Torn City Flight Tracker",
        color=discord.Color.blue(),
        timestamp=datetime.now(timezone.utc)
    )

    #embed.set_thumbnail(url=bot.user.display_avatar.url)

    lines = [
        "```",
        "🌍 Destination  | 🛫 Out | Landed | 🛬 In ",
        "────────────────────────────────────────"
    ]

    for row in rows[2:]:  # skip headers
        if len(row) < 4:
            continue

        dest, outb, inbound, returning = row[:4]

        lines.append(
            f"{dest:<16} | "
            f"{outb:^6} | "
            f"{inbound:^6} | "
            f"{returning:^6}"
        )

    lines.append("```")

    embed.add_field(
        name="Current Flights",
        value="\n".join(lines),
        inline=False
    )

    embed.set_footer(text="Auto-updates every 5 minutes")
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
