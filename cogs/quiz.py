# quiz.py
import discord
from discord.ext import commands

import json
import random
import asyncio
import numpy as np

import os
from dotenv import load_dotenv
load_dotenv()
PROFILE_THUMBNAIL = os.getenv('PROFILE_THUMBNAIL')


class Quiz(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.in_progress = []
        with open('data/vocabulary.json', 'r', encoding='utf-8') as f:
            self.vocabulary = json.load(f)
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            self.levels = json.load(f)

    def load_player(self, player_id):
        """
        Loads player data from data/users.json. Creates a new profile for the
        player if one does not exist.

        Arguments:
            player_id: Integer representation of discord user
        Returns:
            Python representation of the player's profile from users.json
        """
        def create_profile(player_id):
            """
            Returns a new profile for player_id.

            Arguments:
                player_id: Integer representation of discord user
            Returns:
                new profile representation for player_id
            """
            lvl_1_kana = list(self.levels['1'].keys())
            return {
                "num_correct": 0,
                "times_played": 0,
                "level": 1,
                "discovered": len(lvl_1_kana),
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

        with open('data/users.json', 'r', encoding='utf-8') as f:
            all_users = json.load(f)

        try:
            player_data = all_users[str(player_id)]
        except KeyError:
            player_data = create_profile(player_id)
        return player_data

    @commands.command(aliases=['q'], help='Asks what a Japanese character is in romaji.')
    async def quiz(self, ctx):
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

            try:
                romaji = self.vocabulary[jp_char]['romaji']
                return jp_char, romaji
            except:
                raise RuntimeError('Failed to locate Q&A pair')

        async def q_and_a():
            """
            Print question and parse player answer.

            Returns:
                Boolean of whether player answers correctly
            """
            await ctx.send(f'What is the following character in romaji? \n {jp_char}')

            def check(msg):
                return ctx.author == msg.author and ctx.channel == msg.channel
            try:
                msg = await self.client.wait_for("message", timeout=5, check=check)
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

            Arguments:
                correct: bool of whether player answers correctly
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
            found_unmastered = False
            for jp_char in self.levels[str(level)]:
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
                new_kana = self.levels[str(level)].keys()
                player_data['familiarities']["0"] += new_kana
                player_data['discovered_vocab'] += len(self.levels[str(level)])
                await ctx.send(f':partying_face: Congratulations! You are now Level {level}!')

        if ctx.author.id in self.in_progress:
            await ctx.send('Please wait until starting a new quiz.')
            return

        self.in_progress.append(ctx.author.id)
        player_data = self.load_player(ctx.author.id)

        bin_weights = np.array([18, 16, 15, 14, 13, 6, 6, 5, 4, 3])
        bin_weights = bin_weights / np.sum(bin_weights)
        jp_char, romaji = gen_question_data(player_data, bin_weights)

        correct = await q_and_a()
        await response_update(correct)
        await check_level_up()

        player_data["times_played"] += 1

        # write player data to json
        with open('data/users.json', 'r', encoding='utf-8') as f:
            all_users = json.load(f)
            all_users[str(ctx.author.id)] = player_data
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(all_users, f, ensure_ascii=False, indent=4)
        self.in_progress.remove(ctx.author.id)

    @commands.command(aliases=['pr'])
    async def profile(self, ctx):
        player_data = self.load_player(ctx.author.id)

        color = discord.Color.dark_magenta().value
        level = player_data['level']
        num_correct = player_data['num_correct']
        vocab_discovered = player_data['discovered_vocab']
        times_played = player_data['times_played']
        total_vocab = self.levels['total_vocab']

        profile = discord.Embed(
            color=color
        )

        profile.set_author(name=ctx.author.display_name,
                           icon_url=ctx.author.avatar_url)
        profile.set_thumbnail(url=PROFILE_THUMBNAIL)
        profile.add_field(name='Level', value=level, inline=False)
        profile.add_field(
            name='Correct Answers', value=num_correct, inline=False)
        profile.add_field(
            name='Times Played', value=times_played, inline=False)
        profile.add_field(
            name='Vocabulary Discovered', value=f'{vocab_discovered}/{total_vocab}', inline=False)
        await ctx.send(embed=profile)

    @commands.command()
    @commands.is_owner()
    async def updatevocabcount(self, ctx):
        """ Json Manipulation"""
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        total_lvls = levels['total_lvls']
        sum = 0
        for i in range(1, total_lvls + 1):
            sum += len(levels[str(i)])
        levels['total_vocab'] = sum
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, ensure_ascii=False, indent=4)
        await ctx.send(f'Update successful! There are {sum} vocabulary words.')

    @commands.command()
    @commands.is_owner()
    async def createvocabjson(self, ctx):
        """ Json Manipulation"""
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        total_lvls = levels['total_lvls']
        vocab = {}
        for i in range(1, total_lvls + 1):
            level_items = levels[str(i)].items()
            for kana, romaji in level_items:
                vocab[kana] = {
                    "level": i,
                    "romaji": romaji,
                    "definition": None,
                    "pronunciation": None
                }
        with open('data/vocabulary.json', 'w', encoding='utf-8') as f:
            json.dump(vocab, f, ensure_ascii=False, indent=4)
        await ctx.send(f'Creation successful!')

    @commands.command()
    @commands.is_owner()
    async def levelstodict(self, ctx):
        """ Json Manipulation"""
        with open('data/levels.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        total_lvls = levels['total_lvls']
        for i in range(1, total_lvls + 1):
            level_keys = list(levels[str(i)].keys())
            levels[str(i)] = level_keys
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, ensure_ascii=False, indent=4)
        await ctx.send(f'Command successful!')


def setup(client):
    client.add_cog(Quiz(client))
