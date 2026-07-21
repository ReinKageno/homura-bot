
import os
import argparse
import discord
import logging
import logging.handlers
import pyauxy
import traceback
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


parser = argparse.ArgumentParser(description='Run TC Big Sister discord bot')
parser.add_argument('--debug', action='store_true', help='Run in debug mode')
args = parser.parse_args()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DUMMY_GUILD = discord.Object(os.getenv('DUMMY_GUILD_ID'))

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

if hasattr(logging, 'HTTP'):
    logging.getLogger('discord.http').setLevel(logging.WARNING)

handler = logging.handlers.RotatingFileHandler(
     filename='discord.log',
     encoding='utf8',
     maxBytes=32 * 1024 * 1024,
     backupCount=5,
)

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Homura(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        await self.load_extension('commands.utility')
        await self.load_extension('commands.fun')

        try:
            if getattr(args, 'debug', False):
                print(f'{pyauxy.strc("Syncing with guid ", "yellow")}{DUMMY_GUILD.id}')
                self.tree.copy_global_to(guild=DUMMY_GUILD)
                await self.tree.sync(guild=DUMMY_GUILD)
            else:
                print('Syncing to global discord APIs')
                self.tree.clear_commands(guild=DUMMY_GUILD)
                await self.tree.sync()
            
        except:
            traceback.print_exc()

    async def on_ready(self):
        if getattr(args, 'debug', False):
            pyauxy.printc('Bot is running in DEBUG mode.', 'yellow')

        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        if message.author.bot:
            return
        
        await self.process_commands(message)

bot = Homura()

bot.run(BOT_TOKEN, log_handler=None)