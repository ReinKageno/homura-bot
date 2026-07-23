
import discord
from services import gifs
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='look', description="Look at my...")
    async def look(self, ctx:commands.Context):
        await gifs.send_gif(ctx, None, 'look', False)

    @commands.hybrid_command(name='pat', description="Get a pat or give to someone")
    async def look(self, ctx:commands.Context, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'pat')

async def setup(bot):
    await bot.add_cog(Fun(bot))