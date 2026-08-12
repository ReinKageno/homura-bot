
import os
import discord
from config import config
from discord.ext import commands
from dotenv import load_dotenv
from services.homura.permission import has_permission
from services.homura.permission import has_prefix_permission

from pyauxy import hprint

load_dotenv()
git_avatar = os.getenv('GIT_AVA')

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='help', description='Docs and wiki about the bot.', help='Try /help for a guide.')
    async def help(self, ctx:commands.Context, context=None):
        text = []
        lines = []

        text.append(
            f'Created by {config.CREATOR} \n\n'
        )

        commands = list(self.bot.commands)

        width = max(len(command.name) for command in commands)+10

        hybrid_names = {
            command.name
            for command in self.bot.commands
        }

        for command in self.bot.commands:
            prefix = '!|/' if getattr(command, 'app_command', None) else '!| '
            lines.append(f'{f'`{prefix}` | `{command.name}':<{width}}` {command.help} \n')

        if self.bot.tree.get_commands():
            slash_lines = []
            
            for c in self.bot.tree.get_commands():
                if c.name in hybrid_names:
                    continue
                slash_lines.append(f'{f'` /` | `{c.name}':<{width}}` {c.description} \n')

        text.extend(lines)
        text.extend(slash_lines)

        msg = "".join(text)

        embed = discord.Embed(
            title=f'Homura v{config.VERSION}',
            description=msg,
            color=0x4b37e6,
        )

        embed.set_footer(
            text='\u00a9 2026 KanadeRein',
            icon_url=f"https://avatars.githubusercontent.com/u/{git_avatar}"
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='status', description="Get bot's current status and news.", help="Get bot's current status and news.")
    async def status(self, ctx:commands.Context):
        text=[]

        latency_ms = round(self.bot.latency * 1000)

        text.append(f'**Ping:** {latency_ms}ms\n\n')
        text.append(
            f'Participate in supporting development:\n'
            f'**[Homura on Github](https://github.com/ReinKageno/homura-bot)**\n'
            f'**[Saweria to kanaede]({config.SAWERIA})**\n\n'
        )
        text.append(f'**Last changelog:**\n')

        try:
            with open('changelog.md', 'r', encoding='utf-8') as f:
                clog = f.read()
            text.extend(clog)

            msg = "".join(text)

            embed = discord.Embed(
                title="My current status",
                description=msg
            )
        except Exception:
            hprint('File: changelog.md not found')

        try:
            with open('news.md', 'r', encoding='utf-8') as f:
                news = f.read()

            embed.add_field(
                name='News',
                value=news
            )
        except Exception:
            hprint('File: news.md not found')

        embed.set_footer(
            text='\u00a9 2026 KanadeRein',
            icon_url=f"https://avatars.githubusercontent.com/u/{git_avatar}"
        )

        await ctx.send(embed=embed)

    @commands.command(help='Tell me to join a Voice Channel.')
    @has_prefix_permission()
    async def join(self, ctx:commands.Context):
        if ctx.author.voice:
            channel = ctx.author.voice.channel

            await channel.connect()
            await ctx.send(f"Joined {channel.name}")
        else:
            await ctx.send("You must be in a voice channel for me to join.")

    @commands.command(help='Graceful way to disconnect from a Voice Channel')
    @has_prefix_permission()
    async def leave(self, ctx:commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send(f"Disconnected from any voice channel.")
        else:
            await ctx.send("I am not connected to a voice channel.")

    @commands.command(help='Ping me to check.')
    @has_prefix_permission()
    async def ping(self, ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        await ctx.send(
            f"Pong!\n\n"
            f"**Guild:** {guild_id}\n"
            f"**Channel:** {channel_id}\n"
            f"**Status:** Online\n"
            f"**Go Support:** {config.SAWERIA}"
        )

async def setup(bot):
    await bot.add_cog(Utility(bot))