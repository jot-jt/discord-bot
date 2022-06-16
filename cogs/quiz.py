# quiz.py
import discord
from discord.ext import commands

import json
import random
import asyncio
import numpy as np


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
            # create new profile
            with open('data/kana.json', 'r', encoding='utf-8') as f:
                kana = json.load(f)
            lvl_1_kana = list(kana['hiragana']['1'].keys())
            users[str(ctx.author.id)] = {
                "num_correct": 0,
                "times_played": 0,
                "level": 1,
                "familiarities": {
                    "0": lvl_1_kana,
                    "1": [],
                    "2": [],
                    "3": [],
                    "4": [],
                    "5": []
                }
            }
            player_data = users[player_id]

        # load hiragana pool from json to use for question
        level = player_data["level"]
        char_pool = []
        char_weights = []  # weight for each entry in char_pool
        bin_weights = np.array([10, 9, 6, 4, 4, 1])  # weight per frequency bin
        for i in range(6):
            char_pool += player_data['familiarities'][str(i)]
            list_sz = len(player_data['familiarities'][str(i)])
            char_weights += [bin_weights[i]] * list_sz
        char_weights = char_weights / np.sum(char_weights)
        jp_char = np.random.choice(
            char_pool, replace=False, p=char_weights)
        with open('data/kana.json', 'r', encoding='utf-8') as f:
            kana = json.load(f)
        for i in range(1, level+1):
            romaji = kana['hiragana'][str(i)].get(jp_char)
            if romaji != None:
                break

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
                player_data["num_correct"] += 1
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

        # check if player can level up based on if all words in current level are mastered
        found_unmastered = False
        for jp_char in kana['hiragana'][str(level)]:
            if jp_char not in player_data['familiarities']['5']:
                found_unmastered = True
                break

        if not found_unmastered:
            level += 1
            player_data["level"] = level
            new_kana = kana['hiragana'][str(level)].keys()
            player_data['familiarities']["0"] += new_kana
            await ctx.send(f':partying_face: Congratulations! You are now Level {level}!')

        player_data["times_played"] += 1

        # write player data to json
        with open('data/users.json', 'w', encoding='utf-8') as f:
            users = json.dump(users, f, ensure_ascii=False, indent=4)


def setup(client):
    client.add_cog(Quiz(client))
