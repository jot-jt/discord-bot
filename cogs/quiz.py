# quiz.py
import discord
import discord_ui
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
        self.ui = discord_ui.UI(client)
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
        def create_profile():
            """
            Returns a new profile for player_id.

            Arguments:
                player_id: Integer representation of discord user
            Returns:
                new profile representation for player_id
            """
            lvl_1_kana = self.levels['hiragana']['1']
            vocab = {}
            for jp_char in lvl_1_kana:
                vocab[jp_char] = {
                    "times_correct": 0,
                    "times_asked": 0,
                    "familiarity": 0
                }
            return {
                'active_set': 'hiragana',
                'sets': {
                    'hiragana': {
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
                        },
                        "vocab": vocab
                    }
                }
            }

        with open('data/users.json', 'r', encoding='utf-8') as f:
            all_users = json.load(f)

        try:
            player_data = all_users[str(player_id)]
        except KeyError:
            player_data = create_profile()
        return player_data

    @commands.command(aliases=['q'])
    async def quiz(self, ctx):
        """
        Asks what a vocabulary word is in romaji.
        """
        def gen_question_data(set_data, bin_weights):
            """
            Loads a Q&A pair from levels.json based on player level
            and word familiarity of that specific set.

            Arguments:
                set_data: Dictionary that represents a json entry
                    for a player's given vocabulary set in data/users.json
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
                bin = set_data['familiarities'][str(bin_index)]
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

            pronounce_btn = discord_ui.LinkButton(
                url=self.vocabulary[jp_char]['pronunciation'],
                label='See Pronunciation'
            )

            try:
                msg = await self.client.wait_for("message", timeout=5, check=check)
            except asyncio.TimeoutError:
                await self.ui.components.send(
                    channel=ctx.channel,
                    content=f':hourglass: Time\'s up! The answer is `{romaji}`',
                    components=[pronounce_btn])
                set_data["familiarities"]["0"].append(jp_char)
            else:
                if msg.content.casefold() == romaji.casefold():
                    await ctx.send(':white_check_mark: Correct!')
                    return True
                else:
                    await self.ui.components.send(
                        channel=ctx.channel,
                        content=f':x: Incorrect! The answer is `{romaji}`',
                        components=[pronounce_btn])
            return False

        async def response_update(correct):
            """
            Update data based on player response.

            Arguments:
                correct: bool of whether player answers correctly
            """
            familiarity_lvl = 0
            for i in range(10):
                if jp_char in set_data["familiarities"][str(i)]:
                    set_data["familiarities"][str(i)].remove(jp_char)
                    familiarity_lvl = i

            set_data['vocab'][jp_char]['times_asked'] += 1
            set_data["times_played"] += 1

            if correct:  # update familiarity lvl
                familiarity_lvl = min(familiarity_lvl + 1, 9)  # check ceiling
                set_data["num_correct"] += 1
                set_data['vocab'][jp_char]['times_correct'] += 1
            else:
                familiarity_lvl = max(familiarity_lvl - 1, 0)  # check floor

            set_data['vocab'][jp_char]['familiarity'] = familiarity_lvl

            if jp_char not in set_data["familiarities"][str(familiarity_lvl)]:
                set_data["familiarities"][str(
                    familiarity_lvl)].append(jp_char)

        async def check_level_up():
            """
            Check if player can level up based on if all words in current level
            are mastered.
            """
            level = set_data["level"]
            found_unmastered = False
            for jp_char in self.levels[active_set][str(level)]:
                found = False
                for i in range(5, 10):
                    if jp_char in set_data['familiarities'][str(i)]:
                        found = True
                        break
                if not found:
                    found_unmastered = True

            if not found_unmastered:
                level += 1
                set_data["level"] = level
                new_kana = self.levels[active_set][str(level)]
                set_data['familiarities']["0"] += new_kana
                for vocab_word in list(new_kana):
                    set_data['vocab'][vocab_word] = {
                        'times_correct': 0,
                        'times_asked': 0,
                        'familiarity': 0
                    }
                await ctx.send(f':partying_face: Congratulations! You are now Level {level}!')

        if ctx.author.id in self.in_progress:
            await ctx.send('Please wait until starting a new quiz.')
            return

        self.in_progress.append(ctx.author.id)
        player_data = self.load_player(ctx.author.id)
        active_set = player_data['active_set']
        set_data = player_data['sets'][active_set]

        bin_weights = np.array([25, 15, 14, 13, 12, 6, 5, 4, 3, 3])
        bin_weights = bin_weights / np.sum(bin_weights)
        jp_char, romaji = gen_question_data(set_data, bin_weights)

        correct = await q_and_a()
        await response_update(correct)
        await check_level_up()

        # write player data to json
        with open('data/users.json', 'r', encoding='utf-8') as f:
            all_users = json.load(f)
            all_users[str(ctx.author.id)]['sets'][active_set] = set_data
        with open('data/users.json', 'w', encoding='utf-8') as f:
            json.dump(all_users, f, ensure_ascii=False, indent=4)
        self.in_progress.remove(ctx.author.id)

    @commands.command()
    async def pronounce(self, ctx, vocab: str):
        """
        Returns the pronunciation of a vocabulary word.
        """
        try:
            url = self.vocabulary[vocab]['pronunciation']
            await ctx.send(url)
        except KeyError:
            await ctx.send(":cry: No pronunciation found. Only kanas are supported.")

    @pronounce.error
    async def pronounce_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a kana.")

    @commands.command()
    async def profile(self, ctx):
        """
        Display statistics for your active set.
        """
        player_data = self.load_player(ctx.author.id)
        active_set = player_data['active_set']
        set_data = player_data['sets'][active_set]

        color = discord.Color.dark_magenta().value
        level = set_data['level']
        num_correct = set_data['num_correct']
        vocab_discovered = len(set_data['vocab'])
        times_played = set_data['times_played']
        total_vocab = self.levels[active_set]['total_vocab']

        profile = discord.Embed(
            color=color,
            title=f'Your {active_set.capitalize()} Profile!'
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

    @commands.command(aliases=['dict'])
    async def bank(self, ctx):
        """
        Displays the words that you have unlocked so far.
        """
        def generate_string(set_data, start, stop):
            """
            Generates a string where each line is in form '{KANA} {ROMAJI}'
            from player_data's familiarity entries.

            Arguments:
                set_data: Python representation of users.json set
                start: starting familiarity bin
                stop: ending familiarity bin
            Returns:
                Pair of string, integer, where:
                    the string represents the content of the data or "None" if
                        empty.
                    the integer counts the number of entries.

            """
            str_entries = ""
            count = 0
            for i in range(start, stop+1):
                list = set_data['familiarities'][str(i)]
                if len(list) != 0:
                    for entry in list:
                        romaji = self.vocabulary[entry]['romaji']
                        str_entries += f'\n**{entry}** {romaji}'
                        count += 1
            if str_entries == '':
                str_entries = 'None'
            return str_entries, count

        player_data = self.load_player(ctx.author.id)
        active_set = player_data['active_set']
        set_data = player_data['sets'][active_set]

        color = discord.Color.dark_magenta().value
        dict = discord.Embed(
            color=color,
            title=f'Your {active_set.capitalize()} Vocabulary Bank!'
        )
        dict.set_author(name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url)
        dict.set_thumbnail(url=PROFILE_THUMBNAIL)

        learn_entries, learn_count = generate_string(set_data, 0, 5)
        review_entries, review_count = generate_string(set_data, 6, 8)
        master_entries, master_count = generate_string(set_data, 9, 9)
        dict.add_field(name=f'Learning - {learn_count}',
                       value=learn_entries, inline=False)
        dict.add_field(name=f'Reviewing - {review_count}',
                       value=review_entries, inline=False)
        dict.add_field(
            name=f'Mastered - {master_count}', value=master_entries, inline=False)
        await ctx.send(embed=dict)

    @commands.command()
    async def sets(self, ctx):
        """
        Displays your available and active sets.
        """
        player_data = self.load_player(ctx.author.id)
        desc = ''
        active_set = player_data['active_set']
        for set in player_data['sets']:
            desc += f'\n{set.capitalize()}'
            if set == active_set:
                desc += ' **(ACTIVE)**'
        color = discord.Color.dark_magenta().value
        embed = discord.Embed(
            color=color,
            title='Your Available Sets',
            description=desc
        )
        embed.set_author(name=ctx.author.display_name,
                         icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=PROFILE_THUMBNAIL)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def updatelvls(self, ctx):
        """(DEV) Updates levels.json from the data of levels_aux.json"""
        with open('data/levels_aux.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        for set, data in levels.items():
            total_lvls = data['total_lvls']
            count = 0
            for i in range(1, total_lvls + 1):
                lst = []
                for key, value in data[str(i)].items():
                    lst.append(key)
                count += len(data[str(i)])
                data[str(i)] = lst
            data['total_vocab'] = count

            levels[set] = data
        with open('data/levels.json', 'w', encoding='utf-8') as f:
            json.dump(levels, f, ensure_ascii=False, indent=4)
        await ctx.send(f'Update successful!')

    @commands.command()
    @commands.is_owner()
    async def updatevocab(self, ctx):
        """
        (DEV) Updates vocabulary.json from the data of levels_aux.json.
        Pronunciation is retained.
        """
        with open('data/levels_aux.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        with open('data/vocabulary.json', 'r', encoding='utf-8') as f:
            vocabulary = json.load(f)
        updated_vocab = {}
        for set, data in levels.items():
            total_lvls = data['total_lvls']
            for i in range(1, total_lvls + 1):
                for kana, romaji in data[str(i)].items():
                    try:
                        pronunciation = vocabulary[kana]['pronunciation']
                    except:
                        pronunciation = None
                    updated_vocab[kana] = {
                        "set": set,
                        "level": i,
                        "romaji": romaji,
                        "pronunciation": pronunciation
                    }
        with open('data/vocabulary.json', 'w', encoding='utf-8') as f:
            json.dump(updated_vocab, f, ensure_ascii=False, indent=4)
        await ctx.send(f'Creation successful!')


def setup(client):
    client.add_cog(Quiz(client))
