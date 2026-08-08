
import config
import discord
from discord import app_commands
from discord.ext import commands
from pyauxy import hprint
from services.homura import database

BOT_OWNER_ID = config.config.MASTER

def is_permission_manager():
    async def predicate(interaction: discord.Interaction) -> bool:

        if interaction.user.id == BOT_OWNER_ID:
            return True

        if isinstance(interaction.user, discord.Member):
            return interaction.user.guild_permissions.administrator

        return False

    return app_commands.check(predicate)

async def check_permission(
        guild_id: int,
        channel_id: int,
        command_name: str,
        user: discord.Member
) -> bool:
    hprint('PREFIX PERMISSION CHECK')
    db = database.permission_db[str(guild_id)]

    channel_db = db.find_one({
        'channel_id': channel_id
    })

    if not channel_db:
        hprint('Channel permission not found', id=guild_id)
        return True

    permissions = channel_db.get('commands', {}).get(command_name, {})

    if not permissions:
        hprint('No permission found', id=guild_id)
        return True

    users = permissions.get('users', {})
    user_id = str(user.id)

    if user_id in users:
        hprint(f'Permission found for {user_id}')
        return users[user_id]

    roles = permissions.get('roles', {})

    for role in user.roles:
        role_id = str(role.id)

        if role_id in roles:
            hprint(f'Permission found for {role_id}')
            return roles[role_id]

    hprint('Permission is null', id=guild_id)
    return True

def has_permission():
    async def predicate(interaction:discord.Interaction) -> bool:
        command = interaction.command

        if command is None:
            return True

        return await check_permission(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            command_name=command.name,
            user=interaction.user
        )

    return app_commands.check(predicate)

def has_prefix_permission():
    async def predicate(ctx:commands.Context) -> bool:
        if ctx.command is None:
            return True

        return await check_permission(
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            command_name=ctx.command.name,
            user=ctx.author
        )

    return commands.check(predicate)