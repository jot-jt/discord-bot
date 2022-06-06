import discord
from discord.ext import commands

import asyncio
import random


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.client.user} is online!')

    @commands.command(aliases=['latency'], help='Show bot latency.')
    async def ping(self, ctx):
        await ctx.send(f'Returned in {round(self.client.latency * 1000)} ms')

    @commands.command()
    async def clear(ctx, amount: int):
        MAX_PURGE = 20

        if amount <= MAX_PURGE:
            await ctx.channel.purge(limit=amount+1)
        else:
            await ctx.send(
                f'Provided number must be <= {MAX_PURGE}.')
            await asyncio.sleep(3)
            await ctx.channel.purge(limit=2)

    @commands.command(help='Say hello to Candle!')
    async def greet(ctx):
        hello_responses = [
            'Hello!',
            'Ahoy!',
            'Hola!',
        ]
        response = random.choice(hello_responses)
        await ctx.send(response)

    @commands.command(name='8ball', help='Ask a question, and it will be answered.')
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


def setup(client):
    client.add_cog(General(client))
