# https://github.com/Rapptz/discord.py/blob/async/examples/reply.py
import random
import sqlite3

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
        print(locked_id_result)
        # check if locked_id is already in a session with keyholder_id
        keyholder_id_result = database_query('SELECT keyholder_id FROM lock WHERE locked_id = ? AND keyholder_id = ?', [ locked_id, keyholder_id])
        print(keyholder_id_result)
        if locked_id_result == []:
            if keyholder_id_result == []:
                database_query('INSERT INTO lock (locked_id, keyholder_id) VALUES (?,?)', [locked_id, keyholder_id])
                await bot.say('Congratulations ' + context.message.author.mention + '! ' + context.message.mentions[0].mention + ' is now your keyholder!')
        else:
            await bot.say(context.message.author.mention + ': you are already locked!')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    # Try to connect to database
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            # for testing purposes only
            cursor.execute('DROP TABLE lock')
            cursor.execute('CREATE TABLE IF NOT EXISTS lock (keyholder_id INTEGER, locked_id INTEGER, since_date INTEGER)')
    except sqlite3.Error as e:
        print('An error occured:', e.args[0])

bot.run(TOKEN)
