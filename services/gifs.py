
import json
import random
import discord
from discord.ext import commands
from pyauxy import hprint

DATA_PATH = 'data/'

def get_gif(category):
    import re

    with open(DATA_PATH + 'gifs.json', 'r') as file:
        gifs = json.load(file)

    url = random.choice(gifs[category])

    # tenor link resolver
    url = re.sub(r"media\d+", "media", url)
    url = url.replace(".com/m/", ".com/")

    return url

def get_message(category, alone:bool):
    category = category + '-self' if alone is True else category
    
    with open(DATA_PATH + 'gifs_message.json', 'r') as file:
        text = json.load(file)

    return random.choice(text[category])

async def send_gif(ctx:commands.Context, member, action):
    _author = ctx.author.mention
    _mention = None
    alone = True
    if member:
        _mention = member.mention
        alone = False

    gif = get_gif(action)
    msg = get_message(action, alone).format(
        author = _author,
        target = _mention
    )

    if gif and msg:
        embed = discord.Embed(
            description=f"{msg}"
        )

        embed.set_image(url=gif)

        await ctx.send(embed=embed)
    else:
        msg_id = ctx.message.id
        hprint(f'GIF Service: Error at {msg_id}')
        await ctx.send(
            f"An error occured, please contact the developer\n"
            f"-# id {msg_id}"
        )