import discord
from discord.ext import commands

import asyncio


class General(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['latency'], help='Show bot latency')
    async def ping(self, ctx):
        await ctx.send(f'Returned in {round(self.client.latency * 1000)} ms')

    @commands.command(help="Clear message history")
    async def clear(self, ctx, num_msgs: int):
        MAX_NUM = 20

        if num_msgs <= MAX_NUM:
            await ctx.channel.purge(limit=num_msgs+1)
        else:
            await ctx.send(f'Provided number must be <= {MAX_NUM}.')

    @clear.error
    async def clear_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify the number of messages to delete.")

    @commands.command(help='Change the status of the bot')
    @commands.has_permissions(administrator=True)
    async def changestatus(self, ctx, new_status):
        if new_status == 'idle':
            await self.client.change_presence(status=discord.Status.idle)
            await ctx.send('Changed my status to idle!')
        elif new_status == 'dnd':
            await self.client.change_presence(status=discord.Status.dnd)
            await ctx.send('Changed my status to do not disturb!')
        elif new_status == 'online':
            await self.client.change_presence(status=discord.Status.online)
            await ctx.send('Changed my status to online!')
        elif new_status in ['invisible', 'invis', 'offline']:
            await self.client.change_presence(status=discord.Status.offline)
            await ctx.send('Changed my status to offline!')
        else:
            await ctx.send('Please use follow the command with one of `online`, `idle`, `dnd`, `invis`.')

    @changestatus.error
    async def changestatus_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please use follow the command with one of `online`, `idle`, `dnd`, `invis`.')


def setup(client):
    client.add_cog(General(client))
