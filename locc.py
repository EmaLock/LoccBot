# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import random
import sqlite3
import sys

import discord
import key
from discord.ext import commands

TOKEN = key.TOKEN

description = '''Manages chastity'''
bot = commands.Bot(command_prefix='!', description=description)

def database_query(query : str, parameters):
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print('An error occured:', e.args[0])

@bot.command(pass_context=True)
async def lockme(context):
    if context.message.mentions.__len__() > 0:
        keyholder_id = context.message.mentions[0].id
        locked_id = context.message.author.id
        # check if locked_id is already locked
        locked_id_result = database_query('SELECT locked_id FROM lock WHERE locked_id = ?', [locked_id])
        # check if locked_id is already in a session with keyholder_id
        keyholder_id_result = database_query('SELECT keyholder_id FROM lock WHERE locked_id = ? AND keyholder_id = ?', [ locked_id, keyholder_id])
        if locked_id_result == []:
            if keyholder_id_result == []:
                database_query('INSERT INTO lock (locked_id, keyholder_id) VALUES (?,?)', [locked_id, keyholder_id])
                await bot.say('Congratulations ' + context.message.author.mention + '! You are now held by ' + context.message.mentions[0].mention + '!')
        else:
            await bot.say(context.message.author.mention + ': you are already locked!')
    else:
        await bot.say(context.message.author.mention + ': you have to mention someone to be your keyholder!')

@bot.command(pass_context=True)
async def unlockme(context):
    server = context.message.server
    locked_id = context.message.author.id
    locked_mention = context.message.author.mention
    locked_id_result = database_query('SELECT locked_id, keyholder_id FROM lock WHERE locked_id = ?', [locked_id])
    if locked_id_result == []:
        await bot.say(locked_mention + ': you are not locked (yet!)')
    else:
        keyholder_id = locked_id_result[0][1]
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = keyholder_user.mention
        database_query('DELETE FROM lock WHERE locked_id = ?', [locked_id])
        await bot.say(locked_mention + ' is no longer held by ' + keyholder_mention)

@bot.command(pass_context=True)
async def keyholder(context):
    server = context.message.server
    locked_id = None
    locked_mention = None
    # if someone is mentioned, get the current keyholder of the mentioned person
    if context.message.mentions.__len__() > 0:
        locked_id = context.message.mentions[0].id
        locked_mention = context.message.mentions[0].mention
    # else, get the current keyholder of the author
    else:
        locked_id = context.message.author.id
        locked_mention = context.message.author.mention
    keyholder_id_result = database_query('SELECT keyholder_id FROM lock WHERE locked_id = ?', [locked_id])
    if keyholder_id_result == []:
        await bot.say(locked_mention + ' is not held (yet!)')
    else:
        keyholder_id = keyholder_id_result[0][0]
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = keyholder_user.mention
        await bot.say(locked_mention + ' is held by ' + keyholder_mention)

@bot.command()
async def h():
    await bot.say('''Available commands:
    - `!lockme [mention]`: name [mention] as your keyholder
    - `!unlockme`: removes you from being held
    - `!keyholder`: shows your current keyholder
    - `!keyholder[meniton]`: shows [mention]'s current keyholder''')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='!h'))
    # Try to connect to database
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            # for testing purposes only
            if 'test' in sys.argv:
                cursor.execute('DROP TABLE lock')
            cursor.execute('CREATE TABLE IF NOT EXISTS lock (keyholder_id INTEGER, locked_id INTEGER, since_date INTEGER)')
    except sqlite3.Error as e:
        print('An error occured:', e.args[0])

bot.run(TOKEN)
