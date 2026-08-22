
import os
import asyncio
import discord
import time
import re

from bson.objectid import ObjectId
from config import config
from discord.ext import commands
from dotenv import load_dotenv
from pyauxy import hprint
from services.homura import database
from services.homura.MediaLoader import PLAY_YDL, media_loader, extract_info

prefix = config.PREFIX

load_dotenv()
git_avatar = os.getenv('GIT_AVA')

player_locks = {}

def get_lock(guild_id):
    if guild_id not in player_locks:
        player_locks[guild_id] = asyncio.Lock()

    return player_locks[guild_id]

async def audio_player(ctx:commands.Context, search):
        guild_id = ctx.guild.id

        # Check if user on a voice channel
        if not ctx.author.voice:
            await ctx.send(f'Please use when you inside a voice channel.')
            return

        voice_channel = ctx.author.voice.channel
        audio_db = database.audioQueue_db[str(guild_id)]
        empty_queue = True

        if ctx.voice_client is None:
            audio_db.delete_many({})
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client
            if vc is None or not vc.is_connected():
                vc = await voice_channel.connect()

        if audio_db.estimated_document_count():
            empty_queue = False

        wait_msg = await ctx.send('Checking the request...')

        # Gatekeeper
        media = await media_loader(search)

        if media == 4041:
            await wait_msg.edit("Couldn't find a playable version of that Spotify track.")
            return
        if media == 4042:
            await wait_msg.edit('No results found.')
            return

        audio_db.insert_one({
            'title': media['title'],
            'artist': media['channel'],
            'source': media['source'],
            'source_url': media['url'],
            'requester': ctx.author.id,
            'created_at': int(time.time())
        })

        # Media player
        if not vc.is_playing() or vc.is_paused():
            await wait_msg.delete()
            await play_next(ctx)
        if not empty_queue:
            await wait_msg.edit(f'Queue: {media["title"]} by {media["channel"]} successfully added.')

async def play_next(ctx:commands.Context, err=None):

    # Lock the media player and wait until end

    guild_id = ctx.guild.id
    lock = get_lock(guild_id)

    async with lock:
        channel = ctx.voice_client

        # Trio security checker
        if channel is None:
            await ctx.send("I'm not in a voice channel. I can't play the audio.")
            return

        if not channel.is_connected():
            return

        if channel.is_playing() or channel.is_paused():
            return

        if err:
            await ctx.send(f'Cannot play the audio. Unexpected error happened, please contact administrator for help.')
            return
        
        hprint('Preparing the audio', id=guild_id)
        audio_db = database.audioQueue_db[str(guild_id)]
        loop = asyncio.get_running_loop()

        audio = audio_db.find_one({}, sort=[('created_at', 1)])

        if not audio:
            await ctx.send('Audio stopped, queue is empty.')
            hprint('No audio found', id=guild_id)
            return

        hprint(f'Attempting to streaming {audio['source_url']}', id=guild_id)

        info = await extract_info(PLAY_YDL, audio['source_url'], 2)


        stream_url = info['url']

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-ar 48000 -ac 2 -af "aresample=async=1"',
            executable=config.FFMPEG_PATH
        )

        def after(error):
            if error:
                print(error)

            audio_db.delete_one({"_id": audio["_id"]})

            asyncio.run_coroutine_threadsafe(
                play_next(ctx, err=1),
                loop
            )

        await ctx.send(f'Playing {audio['title']} by {audio['artist']}')
        channel.play(source, after=after)

async def clear_queue(ctx:commands.Context, amount:str='1', args:str=None):
    audio_db = database.audioQueue_db[str(ctx.guild.id)]

    if not audio_db.find_one({}):
        hprint('No documents found', ctx.guild.id)
        return

    if amount != "-n":
        pattern = r"^\d+$"

        if not bool(re.fullmatch(pattern, amount)):
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** Invalid number"
                )
            return

        audio_skip = int(amount)

        if audio_skip < 1:
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** The number cannot be below 1"
                )

    else:
        audio_skip = 1

    stop_current = False if amount == "-n" or args == "-n" else True

    rm_queue = list(
        audio_db.find(
            {},
            sort=[("created_at", 1)],
            limit=audio_skip if stop_current else audio_skip + 1
        )
    )

    if amount != "-n":
        pattern = r"^\d+$"

        if not bool(re.fullmatch(pattern, amount)):
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** Invalid number"
                )
            return

        audio_skip = int(amount)

        if audio_skip < 1:
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** The number cannot be below 1"
                )

    else:
        audio_skip = 1

    stop_current = False if amount == "-n" or args == "-n" else True

    rm_queue = list(
        audio_db.find(
            {},
            sort=[("created_at", 1)],
            limit=audio_skip if stop_current else audio_skip + 1
        )
    )

    if not stop_current:
        rm_queue.pop(0)

    audio_db.delete_many({
        "_id": {
            "$in": [doc["_id"] for doc in rm_queue]
        }
    })

    if ctx.voice_client:
        if stop_current and ctx.voice_client.is_playing():            
            ctx.voice_client.stop()

    await ctx.send(f'Skipping {audio_skip} song.')

async def remove_queue(ctx:commands.Context, query):
    audio_db = database.audioQueue_db[str(ctx.guild.id)]

    isnum = bool(re.fullmatch(r'\d+', query))

    if isnum:
        query = int(query)

        if query == 0:
            await ctx.send(
                f'Queue: nothing is changed, nothing to remove.\n'+
                f'Try `{prefix}skipm` if you want to skip current audio.'
            )
            return

        db_cursor = audio_db.find(
            {},
            sort=[('created_at', 1)],
            skip=query,
            limit=1,
        )

        db_doc = next(db_cursor, None)

        if db_doc is None:
            await ctx.send("That queue position doesn't exit.")
            return

        audio = audio_db.find({'_id': db_doc['_id']})
        message = f"Queue: [{query}] {db_doc['title']} has been removed."
        return
    
    arg = " ".join(query)

    if  arg.startswith(("http://", "https://")):
        audio_db.delete_one({'webpage_url': arg})
    else:
        audio = audio_db.find_one({
            'title': {
                '$regex': query,
                '$options': 'i'
            }
        })
        message = f"Queue: Successfully remove {audio['title']}."

    if audio:
        current_audio = audio_db.find_one({}, sort=[('created_at', 1)])
        if audio['title'] == current_audio['title']:
            await ctx.send(
                f"Queue: Cannot remove {audio['title']} because it is still playing.\n"
                f"Try `{prefix}skipm` to skip.")
            return

        audio_db.delete_one({'_id': audio['_id']})
        await ctx.send(message)
    else:
        await ctx.send(f"Queue: I can't find {query} in queue. Remove something doesn't exist is not possible.")
        return

async def clear_whole_queue(ctx:commands.Context):
    audio_db = database.audioQueue_db[str(ctx.guild.id)]

    entity = audio_db.find_one({}, sort=[('created_at', 1)])

    audio_db.delete_many({'_id': {'$ne': ObjectId(entity['_id'])}})
    await ctx.send('The queue successfully cleared.')

async def show_queue(bot, ctx:commands.Context):
    audio_db = database.audioQueue_db[str(ctx.guild.id)]
    text = []

    audio_list = list(
        audio_db.find(
            {},
            {
                'title': 1,
                'artist': 1,
                'requester': 1,
                '_id': 0
            }
        ).sort('created_at', 1)
    )

    if not audio_list:
        await ctx.send('The queue is empty, try `!playm` to start.\n')
        return

    text.extend([
        '**Now Playing** \n──────────\n',
        f'**{audio_list[0]['title']} by {audio_list[0]['artist']}**\n',
        f'-# -requested by <@{audio_list[0]['requester']}> | [<duration>]\n'
    ])

    audio_list.pop(0)
    if audio_list:
        text.append('\n **Queue**\n──────\n')

    i = 0

    for audio in audio_list:
        i += 1
        text.extend([
            f'**[{i}] {audio['title']} by {audio['artist']}**\n',
            f'-# -requested by <@{audio['requester']}> [<duration>]\n\n'
        ])

    msg = "".join(text)

    embed = discord.Embed(
        title='Homura - Media Player',
        description=msg,
        color=0x4b37e6,
    )

    embed.set_footer(
        text='by KanadeRein',
        icon_url=f"https://avatars.githubusercontent.com/u/{git_avatar}"
    )

    await ctx.send(embed=embed)

async def audio_stop(ctx:commands.Context):
    audio_db = database.audioQueue_db[str(ctx.guild.id)]

    audio_db.delete_many({})

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Disconnected.')
    else:
        await ctx.send("I'm not in a voice channel.")