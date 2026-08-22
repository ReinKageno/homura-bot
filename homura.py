
import os
import argparse
import discord
import logging
import logging.handlers
import pyauxy
from config import config
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description='Run TC Big Sister discord bot')
parser.add_argument('--debug', action='store_true', help='Run in debug mode')
parser.add_argument('--debug-gateway', action='store_true', help='Debug for Discord gateway')
args = parser.parse_args()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DUMMY_GUILD = discord.Object(os.getenv('DUMMY_GUILD_ID'))

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

if getattr(args, 'debug-gateway', False):
    logging.getLogger('discord.gateway').setLevel(logging.DEBUG)
else:
    logging.getLogger('discord.gateway').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
     filename='discord.log',
     encoding='utf-8',
     maxBytes=10 * 1024 * 1024,
     backupCount=5,
)

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Homura(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=config.PREFIX, intents=intents)
        self.remove_command('help')

    async def setup_hook(self):
        await self.load_extension('commands.utility')
        await self.load_extension('commands.fun')
        await self.load_extension('commands.security')
        await self.load_extension('services.voice')

        if getattr(args, 'debug', False):
            print(f'{pyauxy.strc("Syncing with guid ", "yellow")}{DUMMY_GUILD.id}')
            self.tree.copy_global_to(guild=DUMMY_GUILD)
            await self.tree.sync(guild=DUMMY_GUILD)
        else:
            print('Syncing to global discord APIs')
            self.tree.clear_commands(guild=DUMMY_GUILD)
            await self.tree.sync()

    async def on_ready(self):
        if getattr(args, 'debug', False):
            pyauxy.printc('Bot is running in DEBUG mode.', 'yellow')

        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        if message.author.bot or message.author == bot.user:
            return
        
        await self.process_commands(message)

    async def on_error(event, *args, **kwargs):
        if event == 'on_message':
            print(f"An error occurred in on_message. Message details: {args[0]}")
        else:
            raise


bot = Homura()

bot.run(BOT_TOKEN, log_handler=None)