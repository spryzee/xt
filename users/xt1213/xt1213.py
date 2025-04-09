import discord
import asyncio
import logging
from colorama import Fore, Style

# Enable logging
logging.basicConfig(level=logging.INFO)

# List of account tokens
TOKENS = []

# Define a function to run a selfbot instance
async def run_selfbot(token):
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(Fore.GREEN + f"Logged in as {client.user} ({client.user.id})" + Style.RESET_ALL)

    @client.event
    async def on_message(message):
        if message.author.id != client.user.id:
            return  # Ignore messages from others

        if message.content.startswith("!ping"):
            await message.channel.send("Pong!")

    try:
        await client.start(token, bot=False)
    except discord.errors.LoginFailure:
        print(Fore.RED + f"Invalid token: {token[:10]}..." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)

# Run all accounts concurrently
async def main():
    tasks = [run_selfbot(token) for token in TOKENS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
