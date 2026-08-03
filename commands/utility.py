from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        await ctx.send(
            f"Pong!\n"
            f"**Guild:** {guild_id}"
            f"**Channel:** {channel_id}"
        )

async def setup(bot):
    await bot.add_cog(Utility(bot))