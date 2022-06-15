# quiz.py
import discord
from discord.ext import commands

import json
import random


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


def setup(client):
    client.add_cog(Quiz(client))
