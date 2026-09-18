import io
import sqlite3
import aiohttp
import urllib.parse
import asyncio
import random
import logging
import discord
from discord.ext import commands

from config import DISCORD_TOKEN

# --- LOGGING SETTINGS ---
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("EmojiBot")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Dictionary to keep track of active sessions (Discord ID -> Bot Username)
aktif_oturumlar = {}

# Database setup and migration
def init_db():
    logger.info("Checking/creating database...")
    conn = sqlite3.connect("favoriler.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            discord_id INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            username TEXT,
            emoji_text TEXT,
            image_url TEXT,
            PRIMARY KEY (username, emoji_text)
        )
    """)
    
    # Check if username column exists in old databases, update if missing
    try:
        cursor.execute("SELECT username FROM favorites LIMIT 1")
    except sqlite3.OperationalError:
        logger.warning("Old database structure detected, adding 'username' column...")
        cursor.execute("DROP TABLE IF EXISTS favorites")
        cursor.execute("""
            CREATE TABLE favorites (
                username TEXT,
                emoji_text TEXT,
                image_url TEXT,
                PRIMARY KEY (username, emoji_text)
            )
        """)

    conn.commit()
    conn.close()
    logger.info("Database is ready.")

init_db()


# --- REGISTRATION MODAL ---
class KayitModal(discord.ui.Modal, title="Create Bot Account"):
    username_input = discord.ui.TextInput(
        label="Username",
        placeholder="E.g: john123",
        min_length=3,
        max_length=20
    )
    password_input = discord.ui.TextInput(
        label="Password",
        placeholder="Enter your secret password",
        style=discord.TextStyle.short,
        min_length=4
    )

    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value
        password = self.password_input.value

        conn = sqlite3.connect("favoriler.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, discord_id) VALUES (?, ?, ?)",
                (username, password, interaction.user.id)
            )
            conn.commit()
            logger.info(f"New account created: {username} (Discord: {interaction.user})")
            await interaction.response.send_message(
                f"✅ Successfully created account **{username}**! You can now log in using the `!login` command.",
                ephemeral=True
            )
        except sqlite3.IntegrityError:
            await interaction.response.send_message(
                "❌ This username is already taken. Please choose another one.",
                ephemeral=True
            )
        finally:
            conn.close()


# --- LOGIN MODAL ---
class GirisModal(discord.ui.Modal, title="Log In to Bot Account"):
    username_input = discord.ui.TextInput(
        label="Username",
        placeholder="Enter your username",
        min_length=3,
        max_length=20
    )
    password_input = discord.ui.TextInput(
        label="Password",
        placeholder="Enter your password",
        style=discord.TextStyle.short,
        min_length=4
    )

    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value
        password = self.password_input.value

        conn = sqlite3.connect("favoriler.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == password:
            aktif_oturumlar[interaction.user.id] = username
            logger.info(f"User logged in: {username} (Discord: {interaction.user})")
            await interaction.response.send_message(
                f"🔓 Successfully logged in to account **{username}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Incorrect username or password!",
                ephemeral=True
            )


# --- ACCOUNT ACTION VIEW ---
class HesapAksiyonView(discord.ui.View):
    def __init__(self, action_type: str):
        super().__init__(timeout=60)
        self.action_type = action_type

    @discord.ui.button(label="Open Form & Proceed", style=discord.ButtonStyle.green)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.action_type == "kayit":
            await interaction.response.send_modal(KayitModal())
        elif self.action_type == "giris":
            await interaction.response.send_modal(GirisModal())


# Add to favorites button view
class EmojiView(discord.ui.View):
    def __init__(self, username: str, emoji_text: str, image_url: str):
        super().__init__(timeout=180)
        self.username = username
        self.emoji_text = emoji_text
        self.image_url = image_url

    @discord.ui.button(label="⭐ Add to Favorites", style=discord.ButtonStyle.blurple)
    async def favori_ekle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        aktif_user = aktif_oturumlar.get(interaction.user.id)
        if not aktif_user:
            await interaction.followup.send(
                "⚠️ You must log in using the `!login` command before performing this action!", 
                ephemeral=True
            )
            return

        conn = sqlite3.connect("favoriler.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO favorites (username, emoji_text, image_url) VALUES (?, ?, ?)",
                (aktif_user, self.emoji_text, self.image_url)
            )
            conn.commit()
            logger.info(f"Added to favorites for account: {aktif_user} -> {self.emoji_text}")
            await interaction.followup.send(
                f"✅ Successfully added to `{aktif_user}`'s favorites! (`{emoji_text}`)", ephemeral=True
            )
        except sqlite3.IntegrityError:
            await interaction.followup.send(
                "⚠️ This design is already in this account's favorites!", ephemeral=True
            )
        finally:
            conn.close()


@bot.event
async def on_ready():
    logger.info(f"Bot successfully logged in as: {bot.user.name} (ID: {bot.user.id})")


@bot.command(name="help")
async def help_command(ctx):
    logger.info(f"{ctx.author} viewed the help menu.")
    embed = discord.Embed(
        title="🎨 Emoji Kitchen - Help Menu",
        description="A Discord bot that fuses emojis or text into unique AI designs and features a secure account system.",
        color=0xFFA500,
    )
    embed.add_field(
        name="🔐 Account Commands",
        value="`!register` - Opens a secure modal to create a bot account\n`!login` - Opens a secure modal to log in\n`!logout` - Logs out of your current account",
        inline=False,
    )
    embed.add_field(
        name="✨ `!emoji-fuse <emoji1> <emoji2> ...`",
        value="Fuses the specified emojis together.",
        inline=False,
    )
    embed.add_field(
        name="🔀 `!emoji-sentence <text>`",
        value="Matches words in a sentence to emojis and generates a visual design.",
        inline=False,
    )
    embed.add_field(
        name="⭐ `!favorites`",
        value="Lists your active account's saved favorite designs.",
        inline=False,
    )
    await ctx.send(embed=embed)


# --- ACCOUNT COMMANDS ---

@bot.command(name="register")
async def kayit(ctx):
    view = HesapAksiyonView("kayit")
    await ctx.send("🔐 Click the button below to open the secure panel and enter your registration details:", view=view, ephemeral=True)


@bot.command(name="login")
async def giris(ctx):
    view = HesapAksiyonView("giris")
    await ctx.send("🔓 Click the button below to open the secure panel and enter your login details:", view=view, ephemeral=True)


@bot.command(name="logout")
async def cikis(ctx):
    if ctx.author.id in aktif_oturumlar:
        eski_user = aktif_oturumlar.pop(ctx.author.id)
        logger.info(f"User logged out: {eski_user}")
        await ctx.send(f"🔒 Logged out from account **{eski_user}**.")
    else:
        await ctx.send("⚠️ You do not have an active account logged in.")


# Emoji to English translation dictionary
EMOJI_TO_ENGLISH = {
    "🍕": "pizza slice", "🍍": "pineapple", "🌶️": "hot pepper", "🔥": "fire flame",
    "💧": "water droplet", "❤️": "red heart", "💖": "sparkling heart", "🚗": "sports car",
    "⚡": "lightning bolt", "🍔": "hamburger", "☕": "coffee cup", "🐱": "cute cat",
    "🐶": "cute dog", "💰": "money bag", "💻": "laptop computer", "🎵": "musical note",
    "🎮": "video game controller", "⭐": "golden star", "✨": "sparkles", "😢": "crying face",
    "😊": "smiling face", "🤖": "robot", "🚀": "space rocket", "🧀": "cheese wedge", 
    "🍯": "honey pot", "🤝": "shaking hands", "👥": "people", "➕": "plus sign", 
    "📈": "chart increasing", "👍": "thumbs up", "🍬": "candy", "🍧": "shaved ice",
    "💀": "skull", "👺": "tengu mask", "🐨": "koala", "😭": "crying face"
}


# Shared image generation function
async def generate_and_send_emoji(ctx, emojis_list):
    if len(emojis_list) < 2:
        await ctx.send("⚠️ At least 2 emojis are required.")
        return

    aktif_user = aktif_oturumlar.get(ctx.author.id, "Guest")
    emoji_text = " + ".join(emojis_list)
    logger.info(f"Image generation started. Account: {aktif_user}, Emojis: {emoji_text}")
    loading_msg = await ctx.send(f"🎨 Fusing `{emoji_text}`, preparing new design...")

    english_terms = [EMOJI_TO_ENGLISH.get(e, "emoji object") for e in emojis_list]
    combined_terms_str = " and ".join(english_terms)

    image_prompt = (
        f"A single brand-new emoji design that creatively fuses the concepts"
        f" and visual elements of these items together: {combined_terms_str}."
        " Flat vector illustration, glossy 3D emoji/sticker style like Apple"
        " or Google emojis, bold clean shapes, simple background,"
        " centered composition, no text."
    )

    try:
        encoded_prompt = urllib.parse.quote(image_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        max_retries = 3
        image_bytes = None
        timeout = aiohttp.ClientTimeout(total=25)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for attempt in range(max_retries):
                try:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            logger.info(f"Image downloaded successfully (Attempt: {attempt + 1})")
                            break
                        elif attempt == max_retries - 1:
                            raise ValueError(f"Service returned status {resp.status}.")
                except asyncio.TimeoutError:
                    if attempt == max_retries - 1:
                        logger.warning("Image generation timed out.")
                        raise ValueError("Server did not respond (Timeout).")

        image_file = discord.File(
            io.BytesIO(image_bytes), filename="custom_emoji.png"
        )

        embed = discord.Embed(
            title=f"🎨 New Design: {emoji_text}", color=0xFF73FA
        )
        embed.set_image(url="attachment://custom_emoji.png")
        embed.set_footer(text=f"Account: {aktif_user}")

        await loading_msg.delete()
        
        view = EmojiView(aktif_user, emoji_text, url)
        await ctx.send(file=image_file, embed=embed, view=view)
        logger.info(f"Image sent successfully: {emoji_text}")

    except Exception as e:
        logger.error(f"Error while generating image: {e}")
        await loading_msg.edit(content=f"❌ An error occurred while drawing the image: {e}")


@bot.command(name="emoji-fuse")
async def emoji_uret(ctx, *emojis: str):
    logger.info(f"!emoji-fuse command executed. Author: {ctx.author}, Input: {emojis}")
    if len(emojis) < 2:
        await ctx.send("⚠️ You must enter at least 2 emojis. Example: `!emoji-fuse 🍕 🍍 🌶️`")
        return
    await generate_and_sent_emoji(ctx, list(emojis))


@bot.command(name="emoji-sentence")
async def emoji_cumle(ctx, *, metin: str):
    logger.info(f"!emoji-sentence command executed. Author: {ctx.author}, Text: {metin}")
    kelimeler = metin.split()
    
    sozluk = {
        "fire": "🔥", "water": "💧", "heart": "❤️", "love": "💖", "car": "🚗",
        "speed": "⚡", "food": "🍔", "coffee": "☕", "cat": "🐱", "dog": "🐶",
        "money": "💰", "computer": "💻", "music": "🎵", "game": "🎮", "star": "⭐",
        "beautiful": "✨", "sad": "😢", "happy": "😊", "robot": "🤖", "space": "🚀",
        "friend": "🤝", "friends": "👥", "with": "➕", "very": "📈", "good": "👍", 
        "candy": "🍬", "sweet": "🍧"
    }
    
    yedek_emojiler = ["🔥", "⭐", "💎", "🚀", "💡", "🎨", "⚡", "🌟", "🍕", "🍀"]
    
    secilen_emojiler = []
    for kelime in kelimeler:
        k = kelime.lower()
        k = k.strip(".,?!'")
        if k in sozluk:
            secilen_emojiler.append(sozluk[k])
        else:
            secilen_emojiler.append(random.choice(yedek_emojiler))
            
    while len(secilen_emojiler) < 2:
        secilen_emojiler.append(random.choice(yedek_emojiler))
        
    secilen_emojiler = secilen_emojiler[:5]
    
    await ctx.send(f"🔀 Emojis matched based on words in **\"{metin}\"**: `{' '.join(secilen_emojiler)}`")
    await generate_and_sent_emoji(ctx, secilen_emojiler)


@bot.command(name="favorites")
async def favorilerim(ctx):
    aktif_user = aktif_oturumlar.get(ctx.author.id)
    if not aktif_user:
        await ctx.send("⚠️ You must log in using the `!login` command to view your favorites!")
        return

    logger.info(f"!favorites command executed. Account: {aktif_user}")
    conn = sqlite3.connect("favoriler.db")
    cursor = conn.cursor()
    cursor.execute("SELECT emoji_text, image_url FROM favorites WHERE username = ?", (aktif_user,))
    favs = cursor.fetchall()
    conn.close()

    if not favs:
        await ctx.send(f"⭐ No saved favorite designs found for account **{aktif_user}**.")
        return

    embed = discord.Embed(
        title=f"⭐ {aktif_user} - Favorite Designs",
        color=0xFFD700
    )
    
    for emoji_text, img_url in favs[-5:]:
        embed.add_field(name=f"🎨 {emoji_text}", value=f"[Image Link]({img_url})", inline=False)
        
    await ctx.send(embed=embed)


bot.run(DISCORD_TOKEN)
