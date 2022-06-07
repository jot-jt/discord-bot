import discord
from discord.ext import commands

import asyncio


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['latency'], help='Show bot latency')
    async def ping(self, ctx):
        await ctx.send(f'Returned in {round(self.client.latency * 1000)} ms')

    @commands.command()
    async def clear(self, ctx, amount: int):
        MAX_PURGE = 20

        if amount <= MAX_PURGE:
            await ctx.channel.purge(limit=amount+1)
        else:
            await ctx.send(
                f'Provided number must be <= {MAX_PURGE}.')
            await asyncio.sleep(3)
            await ctx.channel.purge(limit=2)

    @commands.command(help=f'Change the status of the bot')
    async def changestatus(self, ctx, new_status):
        if new_status == 'idle':
            await self.client.change_presence(status=discord.Status.idle)
            await ctx.send(f'Changed my status to idle!')
        elif new_status == 'dnd':
            await self.client.change_presence(status=discord.Status.dnd)
            await ctx.send(f'Changed my status to do not disturb!')
        elif new_status == 'online':
            await self.client.change_presence(status=discord.Status.online)
            await ctx.send(f'Changed my status to online!')
        elif new_status in ['invisible', 'invis', 'offline']:
            await self.client.change_presence(status=discord.Status.offline)
            await ctx.send(f'Changed my status to offline!')
        else:
            await ctx.send(f'Please use follow the command with one of `online`, `idle`, `dnd`, `invis`.')


def setup(client):
    client.add_cog(General(client))
