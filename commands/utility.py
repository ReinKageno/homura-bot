from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        guild_id = ctx.guild.id
        await ctx.send(
            f"Pong!\n"
            f"**Guild:** {guild_id}"
            )

async def setup(bot):
    await bot.add_cog(Utility(bot))