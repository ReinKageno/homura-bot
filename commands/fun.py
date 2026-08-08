
import discord
from discord.ext import commands
from services import gifs
from services.homura import mplayer
from services.homura.permission import has_permission
from services.homura.permission import has_prefix_permission

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Audio/Music command field

    @commands.command(help='Play audio on a voice channel. You must inside a voice channel to use this command.')
    @has_prefix_permission()
    async def playm(self, ctx, *, search):
        await mplayer.music_player(ctx, search)

    @commands.command(help='Remove specifict audio from queue. Supported by title or link, also works by order by telling a specific number.')
    @has_prefix_permission()
    async def revokem(self, ctx, *, query):
        await mplayer.remove_queue(ctx, query)

    @commands.command(help='Clear the queue, keep playing the current audio.')
    @has_prefix_permission()
    async def clearm(self, ctx, *, num=1):
        await mplayer.clear_queue(ctx, num, clear=True)

    @commands.command(help='Skip the current audio, can skip more than single audios (will skip from the older queue).')
    @has_prefix_permission()
    async def skipm(self, ctx, *, num=1):
        await mplayer.clear_queue(ctx, num, clear=False)

    @commands.command(help='Show the details of current queue.')
    @has_prefix_permission()
    async def queue(self, ctx):
        await mplayer.show_queue(self.bot, ctx)

    @commands.command(help='Stop the audio and leave the voice channel.')
    @has_prefix_permission()
    async def stopm(self, ctx):
        await mplayer.music_stop(ctx)

    # GIFs command field

    @commands.hybrid_command(
            name='cry', description="Just cry",
            help='Express cry by send a gif. Only self supported.'
        )
    @has_permission()
    async def cry(self, ctx):
        await gifs.send_gif(ctx, None, 'cry')

    @commands.hybrid_command(
            name='look', description="Look at my-",
            help='Express sadness meme by send a gif. Target supported.'
        )
    @has_permission()
    async def look(self, ctx):
        await gifs.send_gif(ctx, None, 'look')

    @commands.hybrid_command(
            name='hug', description="A hug can make you feel warm",
            help='Express hug action by send a gif. Target supported.'
        )
    @has_permission()
    async def hug(self, ctx, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'hug')

    @commands.hybrid_command(
            name='pat', description="Get a pat or give to someone",
            help='Express pat action by send a gif. Target supported.'
        )
    @has_permission()
    async def pat(self, ctx, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'pat')

    @commands.hybrid_command(
            name='slap', description="Feel annoyed?",
            help='Express slap action by sending a gif. Target supported.'
        )
    @has_permission()
    async def slap(self, ctx, member:discord.Member=None):
        await gifs.send_gif(ctx, member, 'slap')

async def setup(bot):
    await bot.add_cog(Fun(bot))