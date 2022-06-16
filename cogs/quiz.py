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

    @commands.command(aliases=['q'], help='Asks what the hiragana character is in romaji.')
    async def question(self, ctx):
        # load player data from json
        with open('data/users.json', 'r', encoding='utf-8') as f:
            users = json.load(f)

        player_id = str(ctx.author.id)

        try:
            player_data = users[player_id]
        except KeyError:
            users[str(ctx.author.id)] = {
                "correct_ct": 0,
                "times_played": 0,
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
            player_data = users[player_id]

        # load random hiragana from json
        with open('data/kana.json', 'r', encoding='utf-8') as f:
            kana = json.load(f)
        level = player_data["level"]
        char_pool = []
        for i in range(1, level+1):
            char_pool += kana['hiragana'][str(i)].items()
        print(char_pool)
        jp_char, romaji = random.choice(char_pool)

        # generate question
        await ctx.send(f'What is the following character in romaji? \n {jp_char}')

        # check player response
        def check(msg):
            return ctx.author == msg.author and ctx.channel == msg.channel

        correct = False
        try:
            msg = await self.client.wait_for("message", timeout=10, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f':hourglass: Time\'s up! The answer is `{romaji}`')
            player_data["familiarities"]["0"].append(jp_char)
        else:
            if msg.content == romaji:
                await ctx.send(f':white_check_mark: Correct!')
                player_data["correct_ct"] += 1
                correct = True
            else:
                await ctx.send(f':x: Incorrect! The answer is `{romaji}`')

        # update data based on player response
        familiarity_lvl = 0
        for i in range(6):
            if jp_char in player_data["familiarities"][str(i)]:
                player_data["familiarities"][str(i)].remove(jp_char)
                familiarity_lvl = i

        if correct:  # update familiarity lvl
            familiarity_lvl = min(familiarity_lvl + 1, 5)  # check ceiling
        else:
            familiarity_lvl = max(familiarity_lvl - 1, 0)  # check floor

        if jp_char not in player_data["familiarities"][str(familiarity_lvl)]:
            player_data["familiarities"][str(familiarity_lvl)].append(jp_char)

        # check if player can level up
        # found_unmastered = False
        # for jp_char in kana['hiragana']:
        #     if jp_char != player_data['familiarities']['5']:
        #         found_unmastered = True
        #         break

        # if not found_unmastered:
        #     level += 1
        #     player_data["level"] = level
        #     await ctx.send(':partying_face: Congratulations! You are now Level {level}!')

        player_data["times_played"] += 1

        # write player data to json
        with open('data/users.json', 'w', encoding='utf-8') as f:
            users = json.dump(users, f, indent=4)


def setup(client):
    client.add_cog(Quiz(client))
