# quiz.py
import discord
import discord_ui
from discord.ext import commands

import json
import random
import asyncio
import numpy as np
import background.database as database

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
        self.db = database.Database()

    @commands.command(aliases=['q'])
    async def quiz(self, ctx):
        """
        Asks what a vocabulary word is in romaji.
        """
        def gen_question_data(user_id: int, bin_weights: np.array):
            """
            Loads a Q&A pair from levels.json based on player level
            and word familiarity of that specific set.

            Arguments:
                user_id: Discord id of player
                bin_weights: Normalized numpy array of size 10 that represents
                    the probability distribution of each familiarity level
            Returns:
                A pair in the form of (vocab_id, question_word, answer)
            """
            found = False
            rng = np.random.default_rng()
            bin_priority = rng.choice(
                np.arange(10), size=10, replace=False, p=bin_weights)
            i = 0
            while not found and i < 10:
                bin_index = int(bin_priority[i])
                bin = self.db.player_vocab(user_id, bin_index)
                bin_sz = len(bin)
                if bin_sz > 0:
                    vocab_id = random.choice(bin)[0]
                    jp_char, romaji = self.db.as_defn_pair(vocab_id)
                    found = True
                else:
                    i += 1

            return vocab_id, jp_char, romaji

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
                url=self.db.pronunciation(vocab_id),
                label='See Pronunciation'
            )

            try:
                msg = await self.client.wait_for("message", timeout=5, check=check)
            except asyncio.TimeoutError:
                await self.ui.components.send(
                    channel=ctx.channel,
                    content=f':hourglass: Time\'s up! The answer is `{romaji}`',
                    components=[pronounce_btn])
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

        if ctx.author.id in self.in_progress:
            await ctx.send('Please wait until starting a new quiz.')
            return

        self.in_progress.append(ctx.author.id)

        if not self.db.user_exists(ctx.author.id):
            self.db.create_user(ctx.author.id)

        bin_weights = np.array([20, 13, 13, 13, 12, 7, 6, 6, 5, 4])
        bin_weights = bin_weights / np.sum(bin_weights)
        vocab_id, jp_char, romaji = gen_question_data(
            ctx.author.id, bin_weights)

        correct = await q_and_a()
        self.db.response_update(ctx.author.id, vocab_id, correct)
        new_level, level_up = self.db.check_level_up(ctx.author.id)
        if level_up:
            await ctx.send(f':partying_face: Congratulations! You are now Level {new_level}!')
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

    @commands.command(aliases=['pr'])
    async def profile(self, ctx):
        """
        Display statistics for your active set.
        """
        color = discord.Color.dark_magenta().value
        level = self.db.total_level(ctx.author.id)
        num_correct = self.db.total_times_correct(ctx.author.id)
        vocab_discovered = self.db.total_vocab(ctx.author.id)
        times_played = self.db.total_times_played(ctx.author.id)

        profile = discord.Embed(
            color=color,
            title=f'Your Profile!'
        )

        profile.set_author(name=ctx.author.display_name,
                           icon_url=ctx.author.avatar_url)
        profile.set_thumbnail(url=PROFILE_THUMBNAIL)
        profile.add_field(name='Total Level', value=level, inline=False)
        profile.add_field(
            name='Correct Answers', value=num_correct, inline=False)
        profile.add_field(
            name='Times Played', value=times_played, inline=False)
        profile.add_field(
            name='Vocabulary Discovered', value=f'{vocab_discovered}', inline=False)
        await ctx.send(embed=profile)

    @commands.command(aliases=['dict'])
    async def dictionary(self, ctx):
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

        learn_entries, learn_count = generate_string(set_data, 0, 4)
        review_entries, review_count = generate_string(set_data, 5, 8)
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
        player_data = self.db.user_sets(ctx.author.id)
        active_set_id = self.db.active_set_id(ctx.author.id)
        desc = ''
        for set in player_data:
            desc += f'\n ({set[0]}) **{set[1]}** ⋅ Level {set[2]}/{set[3]}'
            if set[0] == active_set_id:
                desc += " __**|active|**__"
        color = discord.Color.dark_magenta().value
        embed = discord.Embed(
            color=color,
            title='Your Vocabulary Sets',
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
                for key, _ in data[str(i)].items():
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
