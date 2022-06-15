# misc.py
import discord
from discord.ext import commands

import random


class Misc(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(help='Say hello to Candle!')
    async def greet(self, ctx):
        hello_responses = [
            'Hello!',
            'Ahoy!',
            'Hola!',
        ]
        response = random.choice(hello_responses)
        await ctx.send(response)

    @commands.command(name='8ball', help='Ask a question, and it will be answered')
    async def _8ball(self, ctx, *, _):
        ball_responses = [
            'Yes.',
            'I suppose so.',
            'Probably not.',
            'No.',
            'Ask again later.'
        ]
        response = random.choice(ball_responses)
        await ctx.send(response)

    @_8ball.error
    async def _8ball_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a yes/no qeustion.")


def setup(client):
    client.add_cog(Misc(client))
