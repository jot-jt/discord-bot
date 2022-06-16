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
        self.in_progress = []

    @commands.command(aliases=['q'], help='Asks what a Japanese character is in romaji.')
    async def quiz(self, ctx):
        def load_player(player_id):
            """
            Loads player data from data/users.json

            Arguments:
                player_id: Integer representation of discord user
            Returns:
                all_users: Representation of entire users.json file
                player_id: Representation of specific user in users.json
            """
            player_id = str(player_id)

            with open('data/users.json', 'r', encoding='utf-8') as f:
                all_users = json.load(f)

            try:
                player_data = all_users[player_id]
            except KeyError:  # create new profile
                with open('data/levels.json', 'r', encoding='utf-8') as f:
                    kana = json.load(f)
                lvl_1_kana = list(kana['1'].keys())
                all_users[str(ctx.author.id)] = {
                    "num_correct": 0,
                    "times_played": 0,
                    "level": 1,
                    "familiarities": {
                        "0": lvl_1_kana,
                        "1": [],
                        "2": [],
                        "3": [],
                        "4": [],
                        "5": [],
                        "6": [],
                        "7": [],
                        "8": [],
                        "9": []
                    }
                }
                player_data = all_users[player_id]
            return all_users, player_data

        def gen_question_data(player_data, bin_weights):
            """
            Loads a Q&A pair from levels.json based on player level
            and word familiarity.

            Arguments:
                player_data: Dictionary that represents a json entry
                    in data/users.json
                bin_weights: Normalized numpy array of size 10 that represents
                    the probability distribution of each familiarity level
            Returns:
                A pair in the form of (question_word, answer)
            Raises:
                RuntimeError if no valid pair is found
            """
            found = False
            rng = np.random.default_rng()
            bin_priority = rng.choice(
                np.arange(10), size=10, replace=False, p=bin_weights)
            i = 0
            while not found and i < 10:
                bin_index = bin_priority[i]
                bin = player_data['familiarities'][str(bin_index)]
                bin_sz = len(bin)
                if bin_sz > 0:
                    jp_char = random.choice(bin)
                    found = True
                else:
                    i += 1

            with open('data/levels.json', 'r', encoding='utf-8') as f:
                kana = json.load(f)
            player_level = player_data["level"]
            for i in range(1, player_level+1):
                romaji = kana[str(i)].get(jp_char)
                if romaji != None:
                    return jp_char, romaji  # should always return

            raise RuntimeError('Failed to locate Q&A pair')

        async def q_and_a():
            """
            Print question and parse player answer.

            Returns:
                Boolean of whether player answer correctly
            """
            await ctx.send(f'What is the following character in romaji? \n {jp_char}')

            def check(msg):
                return ctx.author == msg.author and ctx.channel == msg.channel
            try:
                msg = await self.client.wait_for("message", timeout=10, check=check)
            except asyncio.TimeoutError:
                await ctx.send(f':hourglass: Time\'s up! The answer is `{romaji}`')
                player_data["familiarities"]["0"].append(jp_char)
            else:
                if msg.content.casefold() == romaji.casefold():
                    await ctx.send(f':white_check_mark: Correct!')
                    player_data["num_correct"] += 1
                    return True
                else:
                    await ctx.send(f':x: Incorrect! The answer is `{romaji}`')
            return False

        async def response_update(correct):
            """
            Update data based on player response.
            """
            familiarity_lvl = 0
            for i in range(10):
                if jp_char in player_data["familiarities"][str(i)]:
                    player_data["familiarities"][str(i)].remove(jp_char)
                    familiarity_lvl = i

            if correct:  # update familiarity lvl
                familiarity_lvl = min(familiarity_lvl + 1, 9)  # check ceiling
            else:
                familiarity_lvl = max(familiarity_lvl - 1, 0)  # check floor

            if jp_char not in player_data["familiarities"][str(familiarity_lvl)]:
                player_data["familiarities"][str(
                    familiarity_lvl)].append(jp_char)

        async def check_level_up():
            """
            Check if player can level up based on if all words in current level
            are mastered.
            """
            level = player_data["level"]
            with open('data/levels.json', 'r', encoding='utf-8') as f:
                kana = json.load(f)
            found_unmastered = False
            for jp_char in kana[str(level)]:
                found = False
                for i in range(5, 10):
                    if jp_char in player_data['familiarities'][str(i)]:
                        found = True
                        break
                if not found:
                    found_unmastered = True

            if not found_unmastered:
                level += 1
                player_data["level"] = level
                new_kana = kana[str(level)].keys()
                player_data['familiarities']["0"] += new_kana
                await ctx.send(f':partying_face: Congratulations! You are now Level {level}!')

        if ctx.author.id in self.in_progress:
            await ctx.send('Please wait until starting a new quiz.')
            return

        self.in_progress.append(ctx.author.id)
        all_users, player_data = load_player(ctx.author.id)

        bin_weights = np.array([20, 18, 18, 15, 10, 6, 5, 4, 3, 1])
        bin_weights = bin_weights / np.sum(bin_weights)
        jp_char, romaji = gen_question_data(player_data, bin_weights)

        correct = await q_and_a()
        await response_update(correct)
        await check_level_up()

        player_data["times_played"] += 1

        # write player data to json
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(all_users, f, ensure_ascii=False, indent=4)
        self.in_progress.remove(ctx.author.id)


def setup(client):
    client.add_cog(Quiz(client))
