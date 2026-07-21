
import json
import random
import traceback
import discord
from discord.ext import commands

DATA_PATH = 'data/'

def get_gif(category):
    with open(DATA_PATH + 'gifs.json', 'r') as file:
        gifs = json.load(file)

    return random.choice(gifs[category])

def get_message(category):
    with open(DATA_PATH + 'gifs_message.json', 'r') as file:
        msgs = json.load(file)

    return random.choice(msgs[category])

async def send_gif(ctx, member, action, msgt=True):
    try:
        gif = get_gif(action)
        if msgt is True:
            msg = get_message(action).format(
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