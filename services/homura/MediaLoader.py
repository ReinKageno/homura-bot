
import os

import asyncio
from dotenv import load_dotenv
import re
import yt_dlp
from urllib.parse import parse_qs, urlparse
from spotdl import Spotdl

from config import config
from pyauxy import hprint

load_dotenv()

YT_USERNAME = os.getenv('YT_USERNAME')
YT_PASSWORD = os.getenv('YT_PASSWORD')

dlp_quiet = True

QUEUE_YDL = yt_dlp.YoutubeDL({
    'format': 'bestaudio',
    'extract_flat': True,
    'quiet': dlp_quiet,
    'noplaylist': True,
    'js_runtimes': {
        'deno': {
            'path':config.DENO_PATH
        }
    }
})

PLAY_YDL = yt_dlp.YoutubeDL({
    'fragment_retries': 10,
    'retry_on_http_error': True,
    'format': 'bestaudio',
    'quiet': dlp_quiet,
    'noplaylist': True,
    'force_ipv4': True,
    'js_runtimes': {
        'deno': {
            'path':config.DENO_PATH
        }
    }
})

ydl_opts = {
    'rm_cache_dir': True
}

spotdl = Spotdl(
    client_id="f8a606e5583643beaa27ce62c48e3fc1",
    client_secret="f6f4c8f73f0649939286cf417c811607"
)

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

async def extract_info(ydl, query, retries=1):
    for attempt in range(retries + 1):
        try:
            return await asyncio.to_thread(
                ydl.extract_info,
                query,
                download=False
            )
        except yt_dlp.utils.DownloadError as e:
            hprint(
                f"[yt-dlp] attempt {attempt + 1}/{retries + 1}: {e}"
            )

            if attempt >= retries:
                return None

            await asyncio.sleep(1)

async def find_youtube_audio(audio):
    queries = [
        f"{audio['artist']} - {audio['title']}",
        f"{audio['artist']} {audio['title']} official audio",
        f"{audio['artist']} {audio['title']} audio",
    ]

    for query in queries:
        info = await extract_info(QUEUE_YDL, f"ytsearch:{query}")

        if not info or not info.get("entries"):
            continue

        result = next(iter(info["entries"]), None)

        if result: return result

    return None

async def resolver_spotify(url:str):
    audios = await asyncio.to_thread(
        spotdl.search,
        [url]
    )

    if not audios:
        return None

    audio = audios[0]

    return {
        'title': audio.name,
        'artist': ", ".join(audio.artists),
        'spotify_url': audio.url,
        'duration': audio.duration,
        'isrc': audio.isrc
    }

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
                'url':spot_info,
                'source':'spotify'
            }

    except Exception:
        pass

    return None

async def media_loader(search):
        url_info = await detect_url(search)

        if url_info:
            source = url_info['source']

            if source == 'youtube':
                url_query = url_info['url']

                info = await extract_info(QUEUE_YDL, url_query)

            elif source == 'spotify':
                
                hprint(f"spotify> Searching for '{search}' audio")
                info = await find_youtube_audio(url_info['url'])

                if not info:
                    return 4041
        else:
            source = 'youtube'
            hprint(f"youtube> Searching for '{search}' audio")
            info = await extract_info(QUEUE_YDL, f'ytsearch:{search}')

        if not info:
            return 4042

        if "entries" in info:
            result = next(iter(info["entries"]), None)
        else:
            result = info

        if result is None:
            return 4042

        result['source'] = source
        return result