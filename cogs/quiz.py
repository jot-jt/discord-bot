# quiz.py
import discord
from discord.ext import commands

import json
import random
import asyncio


class Quiz(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(help='Prints a random hiragana character.')
    async def hiragana(self, ctx):
        with open('data/kana.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            hiragana = data['hiragana']
        response = random.choice(list(hiragana.keys()))
        await ctx.send(response)

    @commands.command(help='Asks what the hiragana character is in romaji.')
    async def question(self, ctx):
        with open('data/kana.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            hiragana = data['hiragana']
        char, romaji = random.choice(list(hiragana.items()))

        await ctx.send(f'What is the following character in romaji? {char}')

        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            msg = await self.client.wait_for("message", timeout=10, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f'Time\'s up! The answer is {romaji}')
        else:
            if msg.content == romaji:
                await ctx.send(f'Correct!')
            else:
                await ctx.send(f'Incorrect! The answer is {romaji}')


def setup(client):
    client.add_cog(Quiz(client))
