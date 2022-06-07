import discord
from discord.ext import commands

import asyncio


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['latency'], help='Show bot latency.')
    async def ping(self, ctx):
        await ctx.send(f'Returned in {round(self.client.latency * 1000)} ms')

    @commands.command()
    async def clear(ctx, amount: int):
        MAX_PURGE = 20

        if amount <= MAX_PURGE:
            await ctx.channel.purge(limit=amount+1)
        else:
            await ctx.send(
                f'Provided number must be <= {MAX_PURGE}.')
            await asyncio.sleep(3)
            await ctx.channel.purge(limit=2)


def setup(client):
    client.add_cog(General(client))
