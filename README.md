# 🎨 Emoji Kitchen & Design Bot

An advanced Discord bot that fuses emojis using AI to create brand new 3D sticker designs, matches sentences into emojis, and includes a secure password-protected account and favorites system.

---

## 🚀 Features

* **🔐 Secure Account System (Modals):** Create an account and log in securely via hidden pop-up forms (`!register` and `!login`) without exposing your password in chat.
* **✨ Emoji Fusing (`!emoji-fuse`):** Harmonizes multiple emojis logically and generates a unique design using AI.
* **🔀 Sentence Matching (`!emoji-sentence`):** Automatically converts words from your sentence into emojis and visualizes them.
* **⭐ Personal Favorites:** Each user's account is independent; users can only save and list favorite designs for their currently logged-in account.
* **🛡️ SQLite Database:** User accounts and favorite designs are safely stored in a local SQLite database.

---

## 🛠️ Installation & Setup

### 1. Requirements
Python (3.10 or higher) must be installed on your computer. Open your terminal or command prompt and install the required libraries:
pip install discord.py aiohttp

2. Configuration (config.py)
Create a file named config.py inside your project folder and add your Discord Bot Token:
DISCORD_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"

3. Running the Bot
Navigate to your project folder in the terminal and run the bot:
python bot.py

📖 Command List

!help	- Lists the help menu and available commands.

!register -	Opens a modal form to create a new bot account securely.

!login - Opens a modal form to log into your bot account.

!logout -	Logs out of your active account.

!emoji-fuse <emoji1> <emoji2> -	Fuses selected emojis to generate an AI image.

!emoji-sentence <text> - Converts words in a sentence into emojis and generates a design.

!favorites - Lists the favorite designs saved to your active account.
