
import asyncio
import discord
import time
import re
import yt_dlp
from discord.ext import commands
from pyauxy import hpril
from services.homura import database

QUEUE_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'extract_flat': True,
    'quiet': True,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    }
})

PLAY_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    }
})

player_locks = {}

def get_lock(guild_id):
    if guild_id not in player_locks:
        player_locks[guild_id] = asyncio.Lock()

    return player_locks[guild_id]

async def music_player(ctx:commands.Context, query):
        if not ctx.author.voice:
            await ctx.send(f'Please use when you inside a voice channel.')
            return
        
        voice = ctx.author.voice.channel
        guild_id = ctx.guild.id
        music_db = database.musicQueue_db[str(guild_id)]
        queue_null = True

        if ctx.voice_client is None:
            music_db.delete_many({})

            vc = await voice.connect()
        else:
            vc = ctx.voice_client

        if music_db.count_documents({}) != 0:
            queue_null = False

        info = await asyncio.to_thread(
            QUEUE_YDL.extract_info,
            query,
            download=False
        )

        music_db.insert_one({
            'title': info["title"],
            'artist': info["channel"],
            'webpage_url': query,
            'requester': ctx.author.id,
            'created_at': int(time.time())
        })

        if not vc.is_playing() or vc.is_paused():
            if not queue_null:
                await ctx.send(f'Queue: {info["title"]} by {info["channel"]} successfully added.')
            await play_next(ctx)
        else:
            await ctx.send(f'Queue: {info["title"]} by {info["channel"]} successfully added.')

async def play_next(ctx:commands.Context):
    guild_id = ctx.guild.id
    lock = get_lock(guild_id)
    hpril('Attempting to play the audio', id=guild_id)

    async with lock:
        channel = ctx.voice_client
        if channel.is_playing() or channel.is_paused():
            return
        
        hpril('Preparing the audio', id=guild_id)
        music_db = database.musicQueue_db[str(guild_id)]
        loop = asyncio.get_running_loop()

        if ctx.voice_client is None:
            await ctx.send("I'm not in a voice channel. Can't play the audio.")
            return
        else:
            channel = ctx.voice_client

        song = music_db.find_one({}, sort=[('created_at', 1)])

        if not song:
            await ctx.send('Music stopped, queue is empty.')
            hpril('No audio found', id=guild_id)
            return

        info = await asyncio.to_thread(
            PLAY_YDL.extract_info,
            song['webpage_url'],
            download=False
        )

        stream_url = info['url']

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            options='-ar 48000 -ac 2 -af "aresample=async=1"'
        )

        def after(error):
            if error:
                print(error)

            music_db.delete_one({"_id": song["_id"]})

            asyncio.run_coroutine_threadsafe(
                play_next(ctx),
                loop
            )

        await ctx.send(f'Playing {song['title']}')
        channel.play(source, after=after)

async def clear(ctx:commands.Context, skip=1, stop=False):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    if skip is str:
        skip = int(skip)

    if skip == 1 and not stop:
        await clear_queue(ctx)
        return

    if skip > 1:
        rm_queue = list(
            music_db.find({}, sort=[("created_at", 1)], limit=skip)
        )

        music_db.delete_many({
            "_id": {
                "$in": [doc["_id"] for doc in rm_queue]
            }
        })

    if stop and ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send(f'Skipping {skip} song.')

async def remove_queue(ctx:commands.Context, query):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    isnum = bool(re.fullmatch(r'\d+', query))

    if isnum:
        query = int(query)

        if query == 0:
            await ctx.send('Queue is not changed, nothing to remove.')
            return

        if query < 0:
            ""

        db_cursor = music_db.find(
            {},
            sort=[('created_at', 1)],
            skip=query - 1,
            limit=1,
        )

        db_doc = next(db_cursor, None)

        if db_doc is None:
            await ctx.send("That queue position doesn't exit.")
            return

        music_db.delete_one({'_id': db_doc['_id']})
        await ctx.send(f"Queue: {db_doc['name']} at line {query} has been removed.")
        return
    
    arg = " ".join(query)

    if  arg.startswith(("http://", "https://")):
        music_db.delete_one({'url': arg})
    else:
        song = music_db.find_one({
            'name': {
                '$regex': query,
                '$options': 'i'
            }
        })

        if not song:
            song = music_db.find_one({
                'title': {
                    '$regex': query,
                    '$options': 'i'
                }
            })

    if song:
        music_db.delete_one({'_id': song['_id']})
        await ctx.send(f"{song['title']} successfully removed.")
    else:
        await ctx.send(f"I can't find {query} in queue. Remove something doesn't exist is not possible.")
        return

async def clear_queue(ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    music_db.delete_many({})
    await ctx.send('The queue successfully cleared.')

async def show_queue(bot, ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]
    text = []

    music_list = list(
        music_db.find(
            {},
            {
                'title': 1,
                'artist': 1,
                'requester': 1,
                '_id': 0
            }
        ).sort('created_at', 1)
    )

    text.extend([
        '**Now Playing** \n────────────\n','```\n',
        f'{music_list[0]['title']} by {music_list[0]['artist']}\n',
        f'Requested by {await bot.fetch_user(music_list[0]['requester'])}\n\n',
        '```'
    ])

    music_list.pop(0)
    if music_list:
        text.append('\n **Queue**\n──────\n')

    i = 0

    for music in music_list:
        i += 1
        text.extend([
            '```\n',
            f'[{i}].{music['title']} by {music['artist']}\n',
            f'? Requested by {await bot.fetch_user(music['requester'])}\n',
            '```'
        ])

    msg = "".join(text)

    await ctx.send(msg)

async def music_stop(ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    music_db.delete_many({})

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Disconnected.')
    else:
        await ctx.send("I'm not in a voice channel.")