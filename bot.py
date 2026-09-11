# bot.py
import io
import aiohttp
import urllib.parse
import discord
from discord.ext import commands

from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
  print(f"{bot.user.name} aktif, emoji karıştırmaya hazır!")


@bot.command(name="help")
async def help_command(ctx):
  embed = discord.Embed(
      title="🎨 Emoji Karıştırıcı - Yardım",
      description="Seçtiğin emojileri birleştirip yepyeni bir emoji/sticker çizen bot!",
      color=0xFFA500,
  )
  embed.add_field(
      name="✨ `!emoji-uret <emoji1> <emoji2> <emoji3> ...`",
      value=(
          "*Örnek:* `!emoji-uret 🍕 🍍`\n"
          "*Örnek (3+ emoji):* `!emoji-uret 🍕 🍍 🌶️ 🧀`"
      ),
      inline=False,
  )
  await ctx.send(embed=embed)


@bot.command(name="emoji-uret")
async def emoji_uret(ctx, *emojis: str):
  if len(emojis) < 2:
    await ctx.send(
        "⚠️ En az 2 emoji girmelisin. Örnek: `!emoji-uret 🍕 🍍 🌶️`"
    )
    return

  emoji_text = " + ".join(emojis)

  loading_msg = await ctx.send(
      f"🎨 {emoji_text} birleştiriliyor, yeni emoji tasarlanıyor..."
  )

  emoji_list_str = ", ".join(emojis)
  image_prompt = (
      f"A single brand-new emoji design that creatively fuses the concepts"
      f" and visual elements of these emojis together: {emoji_list_str}."
      " Flat vector illustration, glossy 3D emoji/sticker style like Apple"
      " or Google emojis, bold clean shapes, simple background,"
      " centered composition, no text."
  )

  try:
    encoded_prompt = urllib.parse.quote(image_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

    async with aiohttp.ClientSession() as session:
      async with session.get(url) as resp:
        if resp.status != 200:
          raise ValueError(f"Servis {resp.status} kodu döndürdü.")
        image_bytes = await resp.read()

    image_file = discord.File(
        io.BytesIO(image_bytes), filename="hibrit_emoji.png"
    )

    embed = discord.Embed(
        title=f"🎨 Yeni Emoji: {emoji_text}", color=0xFF73FA
    )
    embed.set_image(url="attachment://hibrit_emoji.png")
    embed.set_footer(text=f"İsteyen: {ctx.author.name}")

    await loading_msg.delete()
    await ctx.send(file=image_file, embed=embed)

  except Exception as e:
    await loading_msg.edit(content=f"❌ Resim çizilirken hata çıktı: {e}")


bot.run(DISCORD_TOKEN)
