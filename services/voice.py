
import asyncio
import discord
from discord.ext import commands
from pyauxy import hpril

class VoiceEventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.disconnected_tasks = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before, after):
        voice = member.guild.voice_client

        if voice is None:
            return

        channel = voice.channel

        humans = [m for m in channel.members if not m.bot]

        if humans:
            task = self.disconnected_tasks.pop(member.guild.id, None)
            if task:
                task.cancel()
                hpril(f'Voice channel disconnect task canceled', id=member.guild.id)
            return

        if member.guild.id in self.disconnected_tasks:
            return

        hpril(f'Attempting to disconnect from voice channel', id=member.guild.id)

        self.disconnected_tasks[member.guild.id] = asyncio.create_task(
            self.disconnect_after_timeout(member.guild)
        )

    async def disconnect_after_timeout(self, guild:discord.Guild):
        try:
            await asyncio.sleep(300) # 5 minutes

            voice = guild.voice_client

            if voice is None:
                return

            channel = voice.channel

            humans = [
                m for m in channel.members
                if not m.bot
            ]

            if not humans:
                await voice.disconnect()
                self.disconnected_tasks.pop(guild.id, None)
                hpril(f'Disconnected from voice channel', id=guild.id)

        except asyncio.CancelledError:
            return

async def setup(bot):
    await bot.add_cog(VoiceEventHandler(bot))