
import json
import random
import traceback
import discord
from discord.ext import commands

DATA_PATH = 'data/'

def get_gif(category):
    import re

    with open(DATA_PATH + 'gifs.json', 'r') as file:
        gifs = json.load(file)

    url = random.choice(gifs[category])

    url = re.sub(r"media\d+", "media", url)
    url = url.replace(".com/m/", ".com/")

    return url

def get_message(category, alone:bool):
    category = category + '-self' if alone is True else category
    
    with open(DATA_PATH + 'gifs_message.json', 'r') as file:
        text = json.load(file)

    return random.choice(text[category])

async def send_gif(ctx, member, action, target=True):
    try:
        gif = get_gif(action)
        if target is True:
            solo = True if member is None else False
            msg = get_message(action, solo).format(
                author = ctx.author.mention,
                target = member.mention if member is not None else None,
            )
        
        else: msg = ""

        embed = discord.Embed(
            description=f"{msg}"
        )

        embed.set_image(url=gif)

        await ctx.send(embed=embed)

    except:
        msg_id = ctx.message.id
        print(f'Error at {msg_id}')
        traceback.print_exc()
        await ctx.send(
            f"An error occured, please contact the developer\n"
            f"-# {msg_id}"
            )