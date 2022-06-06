# bot.py
import os
import random
import logging
import asyncio
from dotenv import load_dotenv

import discord
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='c.')


@bot.event
async def on_ready():
    print(f'{bot.user} is online!')


@bot.event
async def on_member_join(member):
    print(f'{member} has joined a server.')


@bot.event
async def on_member_remove(member):
    print(f'{member} has been removed from a server.')


@bot.command(aliases=['exit'])
@commands.is_owner()
async def shutdown(ctx):
    await ctx.bot.logout()


@bot.command(help='Say hello to Candle!')
async def greet(ctx):
    hello_responses = [
        'Hello!',
        'Ahoy!',
        'Hola!',
    ]
    response = random.choice(hello_responses)
    await ctx.send(response)


@bot.command(aliases=['latency'], help='Show bot latency.')
async def ping(ctx):
    await ctx.send(f'Returned in {round(bot.latency * 1000)} ms')


@bot.command()
async def clear(ctx, amount: int):
    MAX_PURGE = 20

    if amount <= MAX_PURGE:
        await ctx.channel.purge(limit=amount+1)
    else:
        await ctx.send(
            f'Provided number must be <= {MAX_PURGE}.')
        await asyncio.sleep(3)
        await ctx.channel.purge(limit=2)


@bot.command(name='8ball', help='Ask a question, and it will be answered.')
async def _8ball(ctx, *, _):
    ball_responses = [
        'Yes.',
        'I suppose so.',
        'Probably not.',
        'No.',
        'Ask again later.'
    ]
    response = random.choice(ball_responses)
    await ctx.send(response)


@bot.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise

bot.run(TOKEN)
