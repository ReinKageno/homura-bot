
import discord
from services.homura import database
from discord import app_commands
from discord.ext import commands
from services.homura.permission import is_permission_manager

from pyauxy import hprint

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='perms_set', description='Set up permission to current channel.')
    @is_permission_manager()
    async def perms_set(
        self,
        interaction:discord.Interaction,
        target:discord.Role|discord.Member,
        command:str,
        access:bool
    ):
        db = database.permission_db[str(interaction.guild_id)]

        channel_id = int(interaction.channel_id)
        target_id = str(target.id)
        target_type = 'roles' if target is discord.Role else 'users'

        result = db.update_one(
            {'channel_id': channel_id},
            {
                "$set": {
                    f"commands.{command}.{target_type}.{target_id}": access
                }
            },
            upsert=True,
        )
        await interaction.response.send_message(
            f'Permission {'enabled' if access else "disabled"} '
            f'for `{command}` for {target.mention}.'
        )

    @app_commands.command(name='perms_get', description='Show permission information')
    @is_permission_manager()
    async def perms_get(
        self,
        interaction:discord.Interaction
    ):
        db = database.permission_db[str(interaction.guild.id)]
        channel_id = int(interaction.channel_id)

        channel_db = db.find_one({'channel_id': channel_id})

        if not channel_db:
            await interaction.response.send_message('No permissions have been configured for this channel.')
            return

        grouped = {
            'users': {},
            'roles': {}
        }

        for command, targets in channel_db['commands'].items():
            for user_id, access in targets.get('users', {}).items():
                grouped['users'].setdefault(user_id, []).append(
                    (command, access)
                )

            for role_id, access in targets.get('roles', {}).items():
                grouped['roles'].setdefault(role_id, []).append(
                    (command, access)
                )

        lines = []

        for user_id, permissions in grouped['users'].items():
            user = interaction.guild.get_member(int(user_id))

            if user:
                name = user.mention
            else:
                name = f'Unknown User ({user_id})'

            lines.append(f'**{name}:**')

            for command, access in permissions:
                status = 'Enabled' if access else 'Disabled'
                lines.append(f'- {status} | `{command}`')

            lines.append('')

        for role_id, permissions in grouped['roles'].items():
            role = interaction.guild.get_role(int(role_id))

            if role:
                name = role.mention
            else:
                name = f'Unknown Role ({role_id})'

            lines.append(f'**{name}:**')

            for command, access in permissions:
                status = 'Enabled' if access else 'Disabled'
                lines.append(f'- {status} | `{command}`')

            lines.append('')

        perms = "\n".join(lines)

        await interaction.response.send_message(perms)

async def setup(bot):
    await bot.add_cog(Security(bot))