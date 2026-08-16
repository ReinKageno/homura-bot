
import os
import asyncio
import discord
import time
import re
import yt_dlp
from bson.objectid import ObjectId
from discord.ext import commands
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs 
from pyauxy import hprint
from services.homura import database
from spotdl import Spotdl
from config import config

prefix = config.PREFIX

load_dotenv()
git_avatar = os.getenv('GIT_AVA')

dlp_quiet = True

dlp_quiet = True

QUEUE_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'extract_flat': True,
    'quiet': dlp_quiet,
    'quiet': dlp_quiet,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    }
})

PLAY_YDL = yt_dlp.YoutubeDL({
    'fragment_retries': 10,
    'retry_on_http_error': True,
    'fragment_retries': 10,
    'retry_on_http_error': True,
    'format': 'bestaudio',
    'quiet': dlp_quiet,
    'quiet': dlp_quiet,
    'noplaylist': True,
    'nocheckcertificate': True,
    'js_runtimes': {
        'deno': {
            'path':'../tools/deno/deno'
        }
    },
    'extractor_args': {
        'youtube':[
            'player_js_version=actual',
            'player_client=default,web_safari'
        ]
    }
})

ydl_opts = {
    'rm_cachedir': True
}

spotdl = Spotdl(
    client_id="f8a606e5583643beaa27ce62c48e3fc1",
    client_secret="f6f4c8f73f0649939286cf417c811607"
)

player_locks = {}

URL_RE = re.compile(r"^https?://", re.IGNORECASE)

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

SPOTIFY_HOSTS = {
    "spotify.com",
    "www.spotify.com",
    "open.spotify.com",
}

def ydl_clear_cache():
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        hprint('Clearing yt-dlp filesystem cache...')

def get_lock(guild_id):
    if guild_id not in player_locks:
        player_locks[guild_id] = asyncio.Lock()

    return player_locks[guild_id]

async def music_player(ctx:commands.Context, search):
        guild_id = ctx.guild.id

        # Check if user on a voice channel      

        # Check if user on a voice channel      
        if not ctx.author.voice:
            await ctx.send(f'Please use when you inside a voice channel.')
            return

        voice_channel = ctx.author.voice.channel

        voice_channel = ctx.author.voice.channel
        
        music_db = database.musicQueue_db[str(guild_id)]
        empty_queue = True
        query = None

        if ctx.voice_client is None:
            music_db.delete_many({})

            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

            if vc is None or not vc.is_connected():
                vc = await voice_channel.connect()

        if music_db.estimated_document_count():
            empty_queue = False

        wait_msg = await ctx.send('Checking the request...')

        # Gatekeeper
        url_info = await detect_url(search)
        if url_info:
            source = url_info['source']
            url = url_info['url']
            spotify = url_info['spot']

            if source == 'youtube':
                query = url
            elif source == 'spotify':
                hprint(f'[spotify] Searching for {search} audio', id=guild_id)
                query_spotify = await find_youtube_audio(spotify)

                if not query_spotify:
                    await wait_msg.edit("Couldn't find a playable version of that Spotify track.")
                    return

                _title = query_spotify['title']
                _artist = query_spotify['channel']

                try:
                    url =  query_spotify['original_url']
                except Exception:
                    try:
                        url = query_spotify['webpage_url']
                    except Exception:
                        url = query_spotify['url']
        else:
            source = 'youtube'
            hprint(f"[youtube] Searching for {search} audio", id=guild_id)
            query = f'ytsearch:{search}'

        if source != 'spotify':
            # Youtube finder
            info = await asyncio.to_thread(
                QUEUE_YDL.extract_info,
                query,
                download=False
            )

            if 'entries' in info:
                info = next(iter(info['entries']), None)

            if info is None:
                await wait_msg.edit('No results found.')
                return

            # URL filtering for youtube
            _title = info["title"]
            _artist = info["channel"]
            try:
                url =  info['original_url']
            except Exception:
                try:
                    url = info['webpage_url']
                except Exception:
                    url = info['url']

        music_db.insert_one({
            'title': _title,
            'artist': _artist,
            'source': source,
            'source_url': url,
            'requester': ctx.author.id,
            'created_at': int(time.time())
        })

        # Media player
        if not vc.is_playing() or vc.is_paused():
            await wait_msg.delete()
            await play_next(ctx)
        if not empty_queue:
            await wait_msg.edit(f'Queue: {info["title"]} by {info["channel"]} successfully added.')

async def play_next(ctx:commands.Context):

    # Lock the media player and wait until end

    guild_id = ctx.guild.id
    lock = get_lock(guild_id)
    hprint('Attempting to play an audio', id=guild_id)
    hprint('Attempting to play an audio', id=guild_id)

    async with lock:
        channel = ctx.voice_client

        # Trio security checker
        # Trio security checker
        if channel is None:
            await ctx.send("I'm not in a voice channel. Can't play the audio.")
            await ctx.send("I'm not in a voice channel. Can't play the audio.")
            return

        if not channel.is_connected():
            return

        if channel.is_playing() or channel.is_paused():
            return
        
        hprint('Preparing the audio', id=guild_id)
        music_db = database.musicQueue_db[str(guild_id)]
        loop = asyncio.get_running_loop()

        song = music_db.find_one({}, sort=[('created_at', 1)])

        if not song:
            await ctx.send('Music stopped, queue is empty.')
            hprint('No audio found', id=guild_id)
            return

        hprint(f'Attempting to streaming {song['source_url']}', id=guild_id)

        info = await asyncio.to_thread(
            PLAY_YDL.extract_info,
            song['source_url'],
            download=False
        )

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

            music_db.delete_one({"_id": song["_id"]})

            asyncio.run_coroutine_threadsafe(
                play_next(ctx),
                loop
            )

        await ctx.send(f'Playing {song['title']} by {song['artist']}')
        channel.play(source, after=after)

async def resolver_spotify(url:str):
    songs = await asyncio.to_thread(
        spotdl.search,
        [url]
    )

    if not songs:
        return None

    song = songs[0]

    return {
        'title': song.name,
        'artist': ", ".join(song.artists),
        'spotify_url': song.url,
        'duration': song.duration,
        'isrc': song.isrc
    }

async def find_youtube_audio(song):
    queries = [
        f"{song['artist']} - {song['title']}",
        f"{song['artist']} {song['title']} official audio",
        f"{song['artist']} {song['title']} audio",
    ]

    for query in queries:
        info = await asyncio.to_thread(
            QUEUE_YDL.extract_info,
            f"ytsearch:{query}",
            download=False
        )

        if not info or not info.get("entries"):
            continue

        result = next(iter(info["entries"]), None)

        if result: return result

    return None

async def clear_queue(ctx:commands.Context, amount:str='1', args:str=None):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    if not music_db.find_one({}):
        hprint('No documents found', ctx.guild.id)
    if not music_db.find_one({}):
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

        music_skip = int(amount)

        if music_skip < 1:
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** The number cannot be below 1"
                )

    else:
        music_skip = 1

    stop_current = False if amount == "-n" or args == "-n" else True

    rm_queue = list(
        music_db.find(
            {},
            sort=[("created_at", 1)],
            limit=music_skip if stop_current else music_skip + 1
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

        music_skip = int(amount)

        if music_skip < 1:
            await ctx.send(
                "Queue: Cannot process the request\n"
                "**[reason]** The number cannot be below 1"
                )

    else:
        music_skip = 1

    stop_current = False if amount == "-n" or args == "-n" else True

    rm_queue = list(
        music_db.find(
            {},
            sort=[("created_at", 1)],
            limit=music_skip if stop_current else music_skip + 1
        )
    )

    if not stop_current:
        rm_queue.pop(0)

    if not stop_current:
        rm_queue.pop(0)

    music_db.delete_many({
        "_id": {
            "$in": [doc["_id"] for doc in rm_queue]
        }
    })
    music_db.delete_many({
        "_id": {
            "$in": [doc["_id"] for doc in rm_queue]
        }
    })

    if ctx.voice_client:
        if stop_current and ctx.voice_client.is_playing():            
            ctx.voice_client.stop()

    await ctx.send(f'Skipping {music_skip} song.')

async def remove_queue(ctx:commands.Context, query):
    music_db = database.musicQueue_db[str(ctx.guild.id)]

    isnum = bool(re.fullmatch(r'\d+', query))

    if isnum:
        query = int(query)

        if query == 0:
            await ctx.send(
                f'Queue: nothing is changed, nothing to remove.\n'+
                f'Try `{prefix}skipm` if you want to skip current audio.'
            )
            return

        db_cursor = music_db.find(
            {},
            sort=[('created_at', 1)],
            skip=query,
            limit=1,
        )

        db_doc = next(db_cursor, None)

        if db_doc is None:
            await ctx.send("That queue position doesn't exit.")
            return

        song = music_db.find({'_id': db_doc['_id']})
        message = f"Queue: [{query}] {db_doc['title']} has been removed."
        return
    
    arg = " ".join(query)

    if  arg.startswith(("http://", "https://")):
        music_db.delete_one({'webpage_url': arg})
    else:
        song = music_db.find_one({
            'title': {
                '$regex': query,
                '$options': 'i'
            }
        })
        message = f"Queue: Successfully remove {song['title']}."

    if song:
        current_audio = music_db.find_one({}, sort=[('created_at', 1)])
        if song['title'] == current_audio['title']:
            await ctx.send(
                f"Queue: Cannot remove {song['title']} because it is still playing.\n"
                f"Try `{prefix}skipm` to skip.")
            return

        music_db.delete_one({'_id': song['_id']})
        await ctx.send(message)
    else:
        await ctx.send(f"Queue: I can't find {query} in queue. Remove something doesn't exist is not possible.")
        return

async def clear_whole_queue(ctx:commands.Context):
    audio_db = database.musicQueue_db[str(ctx.guild.id)]

    entity = audio_db.find_one({}, sort=[('created_at', 1)])

    audio_db.delete_many({'_id': {'$ne': ObjectId(entity['_id'])}})
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

    if not music_list:
        await ctx.send('The queue is empty, try `!playm` to start.\n')
        return

    text.extend([
        '**Now Playing** \n──────────\n',
        f'**{music_list[0]['title']} by {music_list[0]['artist']}**\n',
        f'-# -requested by {await bot.fetch_user(music_list[0]['requester'])}\n'
    ])

    music_list.pop(0)
    if music_list:
        text.append('\n **Queue**\n──────\n')

    i = 0

    for music in music_list:
        i += 1
        text.extend([
            f'**[{i}] {music['title']} by {music['artist']}**\n',
            f'-# -requested by {await bot.fetch_user(music['requester'])}\n\n'
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

async def detect_url(text: str)-> bool:
    try:
        result = urlparse(text)
        host = (result.hostname or "").lower()
    
        if host in YOUTUBE_HOSTS:
            query = parse_qs(result.query)

            if 'v' in query:
                return {
                    'url':f"https://www.youtube.com/watch?v={query['v'][0]}",
                    'source':'youtube'
                }

            if host == 'youtu.be' and result.path:
                return {
                    'url':f'https://www.youtube.com/watch?v={result.path.lstrip('/')}',
                    'source':'youtube'
                }

        if host in SPOTIFY_HOSTS:
            spot_info = await resolver_spotify(text)
            return {
                'url':text,
                'source':'spotify',
                'spot':spot_info
            }

    except Exception:
        pass

    return None