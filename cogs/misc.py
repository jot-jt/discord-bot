# misc.py
import discord
from discord.ext import commands

import random
import json

import os
from dotenv import load_dotenv
load_dotenv()
PROFILE_THUMBNAIL = os.getenv('PROFILE_THUMBNAIL')


class Misc(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(help='Say hello!')
    async def greet(self, ctx):
        hello_responses = [
            'Hello!',
            'Ahoy!',
            'Hola!',
            'Bonjour!',
            'こんにちは！',
            '你好！',
            '안녕하세요!',
            'Hallo!',
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
            await ctx.send("Please provide a yes/no question.")

    @commands.command(name='io', help='List some web browser games.')
    async def io(self, ctx):
        with open('data/io.json', 'r', encoding='utf-8') as f:
            websites = json.load(f)

        color = discord.Color.dark_magenta().value
        embed = discord.Embed(
            color=color,
            title=f'Multiplayer .io Games'
        )
        user = ctx.author
        embed.set_author(name=user.display_name,
                         icon_url=user.avatar_url)
        embed.set_thumbnail(url=PROFILE_THUMBNAIL)

        general = ''
        for website in websites['general']:
            general += f'\n{website}'

        drawing = ''
        for website in websites['drawing']:
            drawing += f'\n{website}'

        embed.add_field(
            name=':partying_face:', value=general, inline=False)
        embed.add_field(
            name=':pencil:', value=drawing, inline=False)
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Misc(client))
