"""
Quote of the Day - Discord bot

Setup:
    pip install discord.py python-dotenv
    Create a .env file next to this script with:
        DISCORD_TOKEN=your_bot_token
        CHANNEL_ID=123456789012345678
    Run:  python quote_bot.py

In the Discord Developer Portal (Bot tab), enable "Message Content Intent".
"""

import os
import random
import datetime
from zoneinfo import ZoneInfo

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# When to post the daily quote (24h clock) and in which timezone
POST_TIME = datetime.time(hour=9, minute=0, tzinfo=ZoneInfo("Europe/Warsaw"))

# Used if the online API is unreachable
FALLBACK_QUOTES = [
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("It always seems impossible until it's done.", "Nelson Mandela"),
    ("Well begun is half done.", "Aristotle"),
    ("The journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("What we think, we become.", "Buddha"),
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


async def fetch_quote() -> tuple[str, str]:
    """Get a random quote from ZenQuotes, or fall back to the local list."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://zenquotes.io/api/random",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data[0]["q"], data[0]["a"]
    except Exception as e:
        print(f"Quote API failed ({e}); using fallback.")
        return random.choice(FALLBACK_QUOTES)


def make_embed(text: str, author: str) -> discord.Embed:
    embed = discord.Embed(
        title="✨ Quote of the Day",
        description=f"*“{text}”*",
        color=discord.Color.gold(),
    )
    embed.set_footer(text=f"— {author}")
    return embed


@tasks.loop(time=POST_TIME)
async def daily_quote():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found - check CHANNEL_ID and bot permissions.")
        return
    text, author = await fetch_quote()
    await channel.send(embed=make_embed(text, author))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if not daily_quote.is_running():
        daily_quote.start()


@bot.command(name="quote")
async def quote(ctx: commands.Context):
    """Get a random quote on demand."""
    text, author = await fetch_quote()
    await ctx.send(embed=make_embed(text, author))


if __name__ == "__main__":
    if not TOKEN or not CHANNEL_ID:
        raise SystemExit("Set DISCORD_TOKEN and CHANNEL_ID in your .env file.")
    bot.run(TOKEN)
