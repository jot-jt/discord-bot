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
        # load player data from json
        with open('data/users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)
        print(users)
        try:
            player_data = users[str(ctx.author.id)]
        except KeyError:
            users[str(ctx.author.id)] = {
                "correct_ct": 0,
                "level": 1,
                "familiarities": {
                    "0": [],
                    "1": [],
                    "2": [],
                    "3": [],
                    "4": [],
                    "5": []
                }
            }
            player_data = users[ctx.author.id]

        # load random hiragana from json
        with open('data/kana.json', 'r', encoding='utf-8') as f:
            kana = json.load(f)
        level = str(player_data["level"])
        char_pool = kana['hiragana'][level]
        jp_char, romaji = random.choice(list(char_pool.items()))

        # generate question
        await ctx.send(f'What is the following character in romaji? \n {jp_char}')

        # check player response
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        try:
            msg = await self.client.wait_for("message", timeout=10, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f':hourglass: Time\'s up! The answer is `{romaji}`')
            player_data["familiarities"]["0"].append(jp_char)
        else:
            if msg.content == romaji:
                await ctx.send(f':white_check_mark: Correct!')
                player_data["correct_ct"] += 1
                player_data["familiarities"]["1"].append(jp_char)
            else:
                await ctx.send(f':x: Incorrect! The answer is `{romaji}`')
                player_data["familiarities"]["0"].append(jp_char)

        # write player data to json
        with open('data/users.json', 'w', encoding='utf-8') as f:
            users = json.dump(users, f, indent=4)


def setup(client):
    client.add_cog(Quiz(client))
