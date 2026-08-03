
import json
import random
import discord
from discord.ext import commands

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
    _mention = member.mention if member else None
    solo = True if member else False

    gif = get_gif(action)
    msg = get_message(action, solo).format(
        author = _author,
        target = _mention
    )

    if gif and msg:
        embed = discord.Embed(
            description=f"{msg}"
        )

        embed.set_image(url=gif)

        await ctx.send(embed=embed)
        print(f"A gif has been sent to {ctx.message.id}")

    else:
        msg_id = ctx.message.id
        print(f'Error at {msg_id}')
        await ctx.send(
            f"An error occured, please contact the developer\n"
            f"-# id {msg_id}"
        )