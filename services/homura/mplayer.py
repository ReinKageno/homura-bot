
import asyncio
import discord
import time
import re
import yt_dlp
from discord.ext import commands
from services.homura import database

async def music_player(ctx:commands.Context, search):
        voice = ctx.author.voice.channel
        guild_id = str(ctx.guild.id)

        if ctx.voice_client is None:
            clear_queue(ctx)
            vc = await voice.connect()
            vcn = False
        else:
            vc = ctx.voice_client
            vcn = True
        
        ydl = yt_dlp.YoutubeDL({
            'format': 'bestaudio',
            'js_runtimes': {
                'deno': {
                    'path':'../tools/deno/deno'
                }
            }
        })

        music_db = database.musicQueue_db[guild_id]
        info = ydl.extract_info(search, download=False)

        title = info["title"]
        artist = info["channel"]
        url = info["url"]

        music_db.insert_one({
            'title': title,
            'artist': artist,
            'url': search,
            'stream_url': url,
            'name': title + artist,
            'created_at': int(time.time())
        })

        if not vc.is_playing():
            if vcn:
                await ctx.send(f'Queue: {title} by {artist} successfully added.')
            await play_next(ctx)
        else:
            await ctx.send(f'Queue: {title} by {artist} successfully added.')

async def play_next(ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]
    loop = asyncio.get_running_loop()

    if ctx.voice_client is None:
        ctx.send("I'm not in a voice channel. Can't play the audio.")
        return
    else:
        channel = ctx.voice_client

    song = music_db.find_one({}, sort=[('created_at', 1)])

    if not song:
        await ctx.send('Music stopped, queue is empty.')
        return

    music_db.delete_one({"_id": song["_id"]})

    source = discord.FFmpegPCMAudio(song["stream_url"], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')

    channel.play(
        source,
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(ctx),
            loop
        )
    )

async def clear(ctx:commands.Context, skip=1, stop=False):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    if skip is str:
        skip = int(skip)

    if skip == 0 and not stop:
        await clear_queue(ctx)
        return

    if skip > 0:
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
            ctx.send(f'Skipping {skip+1} song.')
            await play_next(ctx)

async def remove_queue(ctx:commands.Context, query):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    isnum = bool(re.fullmatch(r'\d+', query))

    if isnum:
        query = int(query)

        if query == 0:
            ctx.send('Queue is not changed, nothing to remove.')
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
        ctx.send(f"Queue: {db_doc['name']} at line {query} has been removed.")
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
        await ctx.send(f"I cannot find {query} in queue. Cannot remove something doesn't exist.")
        return

async def clear_queue(ctx:commands.Context):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    music_db.delete_many({})
    ctx.send('The queue successfully cleared.')

async def music_stop(ctx:commands.Context):
    clear_queue(ctx)

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send('Disconnected.')
    else:
        await ctx.send("I'm not in a voice channel.")