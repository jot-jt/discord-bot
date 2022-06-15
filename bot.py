# bot.py
import discord
import json
from discord.ext import commands

import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_PREFIX = os.getenv('BOT_PREFIX')
STATUS = os.getenv('BOT_STATUS_DESC')


def get_prefix(client, message):
    with open('data/prefixes.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]


client = commands.Bot(command_prefix=get_prefix)


@client.event
async def on_guild_join(guild):
    with open('data/prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = DEFAULT_PREFIX
    with open('data/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.event
async def on_guild_remove(guild):
    with open('data/prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))
    with open('data/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.command(help='Change bot prefix for this server')
async def changeprefix(ctx, prefix):
    with open('data/prefixes.json', 'r') as f:
        prefixes = json.load(f)
    prefixes[str(ctx.guild.id)] = prefix
    with open('data/prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)
    await ctx.send(f'The prefix has been changed to `{prefix}`!')


@changeprefix.error
async def changeprefix_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please specify a new bot prefix.")


@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')


@client.event
async def on_member_remove(member):
    print(f'{member} has been removed from a server.')


@client.command(help='(DEV) Load a cog')
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Loaded {extension}!')


@client.command(help='(DEV) Unload a cog')
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f'Poof! Unloaded {extension}.')


@client.command(help='(DEV) Reload a cog')
@commands.is_owner()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'Reloaded {extension}!')


@client.command(aliases=['exit', 'stop'], help='(DEV) Stop the bot')
@commands.is_owner()
async def shutdown(ctx):
    await ctx.send('Turning off, goodbye!')
    await client.change_presence(status=discord.Status.offline)
    await ctx.bot.logout()


@client.event
async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.dnd, activity=discord.Game(f'{STATUS}'))
    print(f'{client.user} is online!')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')  # splice removes '.py'

client.run(TOKEN)
