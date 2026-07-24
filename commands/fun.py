
import discord
from services import gifs
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='look', description="Look at my-")
    async def look(self, ctx:commands.Context):
        await gifs.send_gif(ctx, None, 'look')

    @commands.hybrid_command(name='pat', description="Get a pat or give to someone")
    async def pat(self, ctx:commands.Context, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'pat')

    @commands.hybrid_command(name='hug', description="A hug can make you feel warm")
    async def hug(self, ctx:commands.Context, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'hug')

    @commands.hybrid_command(name='cry', description="Just cry")
    async def cry(self, ctx:commands.Context):
        await gifs.send_gif(ctx, None, 'cry')

async def setup(bot):
    await bot.add_cog(Fun(bot))