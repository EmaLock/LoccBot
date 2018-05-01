import sqlite3
import sys

import discord
import key
from discord.ext import commands

TOKEN = key.TOKEN

description = '''Manages chastity'''
bot = commands.Bot(command_prefix='!', description=description)
bot.remove_command('help')

def database_query(query : str, parameters):
    # sends a query to the database. It should be parametered with interrogation marks in place of the arguments, and the arguments should be in a list
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print("An error occured:", e.args[0])

@bot.command(pass_context=True)
async def lockme(context):
    locked_mention = context.message.author.mention
    locked_id = context.message.author.id
    # needs a mention! Names [mention] as the author's keyholder
    if context.message.mentions.__len__() > 0:
        keyholder_id = context.message.mentions[0].id
        # check if locked_id is already locked
        locked_id_result = database_query('SELECT locked_id FROM lock WHERE locked_id = ?', [locked_id])
        # check if locked_id is already in a session with keyholder_id
        keyholder_id_result = database_query('SELECT keyholder_id FROM lock WHERE locked_id = ? AND keyholder_id = ?', [locked_id, keyholder_id])
        # if the locked is not in a session
        if locked_id_result == []:
            # if the wished keyholder is not in a session with the locked
            if keyholder_id_result == []:
                keyholder_mention = context.message.mentions[0].mention
                database_query('INSERT INTO lock (locked_id, keyholder_id, since_date) VALUES (?,?, julianday(\'now\'))', [locked_id, keyholder_id])
                await bot.say('Congratulations {locked}! You are now held by {keyholder}!'.format(locked=locked_mention, keyholder=keyholder_mention))
        # if the locked is already locked
        else:
            await bot.say('{locked}: you are already locked!'.format(locked=locked_mention))
    # if nobody has been mentioned
    else:
        await bot.say('{locked}: you have to mention someone to be your keyholder!'.format(locked=locked_mention))

@bot.command(pass_context=True)
async def unlockme(context):
    #unlocks the author from their keyholder
    server = context.message.server
    locked_id = context.message.author.id
    locked_mention = context.message.author.mention
    locked_id_result = database_query('SELECT locked_id, keyholder_id FROM lock WHERE locked_id = ?', [locked_id])
    # if the locked is not in a session
    if locked_id_result == []:
        await bot.say('{locked}: you are not locked (yet!)'.format(locked=locked_mention))
    # if the locked is in a session
    else:
        keyholder_id = locked_id_result[0][1]
        keyholder_user = server.get_member(str(keyholder_id))
        # if the keyholder is not connected to the server
        if keyholder_user == None:
            keyholder_mention = 'a user who is not here'
        # if the keyholder is connected to the server
        else:
            keyholder_mention = keyholder_user.mention
        database_query('DELETE FROM lock WHERE locked_id = ?', [locked_id])
        await bot.say('{locked} is no longer held by {keyholder}'.format(locked=locked_mention, keyholder=keyholder_mention))

@bot.command(pass_context=True)
async def unlock(context):
    #needs a mention! Lets a keyholder free [mention]
    if context.message.mentions.__len__() > 0:
        locked_id = context.message.mentions[0].id
        locked_mention = context.message.mentions[0].mention
        keyholder_id = context.message.author.id
        keyholder_mention = context.message.author.mention
        lock_result = database_query('SELECT locked_id, keyholder_id FROM lock WHERE locked_id = ? AND keyholder_id = ?', [locked_id, keyholder_id])
        # if the keyholder is NOT holding [mention]
        if lock_result == []:
            await bot.say('{keyholder}: you are not holding {locked}'.format(keyholder=keyholder_mention, locked=locked_mention))
        # if the keyholder is holding [mention]
        else:
            database_query('DELETE FROM lock WHERE  locked_id = ? AND keyholder_id = ?', [locked_id, keyholder_id])
            await bot.say('{keyholder} is no longer holding {locked}'.format(keyholder=keyholder_mention, locked=locked_mention))

@bot.command(pass_context=True)
async def keyholder(context):
    #shows who is currently holding the author or the [mention]
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
    keyholder_id_result = database_query('SELECT keyholder_id, CAST(julianday(\'now\') - julianday(since_date) as INTEGER) FROM lock WHERE locked_id = ?', [locked_id])
    # if no results are returned, the author or [mention] is not help
    if keyholder_id_result == []:
        await bot.say('{locked} is not held (yet!)'.format(locked=locked_mention))
    # if there is a result, get the keyholder and mention them!
    else:
        keyholder_id = keyholder_id_result[0][0]
        keyholder_user = server.get_member(str(keyholder_id))
        # if the keyholder is not in the server
        if keyholder_user == None:
            keyholder_mention = 'a user who is not here'
        # if the keyholder is in the server
        else:
            keyholder_mention = keyholder_user.mention
        since_date = keyholder_id_result[0][1]
        await bot.say('{locked} has been held by {keyholder} for {days} day(s)'.format(locked=locked_mention, keyholder=keyholder_mention, days=str(since_date)))

@bot.command(pass_context=True)
async def subs(context):
    #lists the subs of the author or [mention]
    server = context.message.server
    keyholder_id = None
    keyholder_mention = None
    # if someone is mentioned, get the current subs of the mentioned person
    if context.message.mentions.__len__() > 0:
        keyholder_id = context.message.mentions[0].id
        keyholder_mention = context.message.mentions[0].mention
    # else, get the current subs of the author
    else:
        keyholder_id = context.message.author.id
        keyholder_mention = context.message.author.mention
    locked_id_result = database_query('SELECT locked_id, CAST(julianday(\'now\') - julianday(since_date) as INTEGER) FROM lock WHERE keyholder_id = ?', [keyholder_id])
    # if there is no results, the author or [mention] is not holding someone
    if locked_id_result == []:
        await bot.say('{keyholder} is holding no one (yet!)'.format(keyholder=keyholder_mention))
    # if there are results, the author or [mention] is holding someone, mention them!
    else:
        locked_mentions = ''
        for locked in locked_id_result:
            locked_id = locked[0]
            locked_user = server.get_member(str(locked_id))
            print(locked_user)
            # if the locked is not on the server
            if locked_user == None:
                locked_mention = 'someone who is not on the server'
            else:
                locked_mention = locked_user.mention
            since_date = locked[1]
            locked_mentions += ' {locked} ({days} day(s))'.format(locked=locked_mention, days=str(since_date))
        await bot.say('{keyholder} is holding:{locked_mentions}'.format(keyholder=keyholder_mention, locked_mentions=locked_mentions))

@bot.command()
async def help():
    # list the commands
    await bot.say('''Available commands:
    - `!lockme [mention]`: name [mention] as your keyholder
    - `!unlockme`: removes you from being held
    - `!unlock [mention]`: frees [mention] from your holding
    - `!keyholder`: shows your current keyholder
    - `!keyholder[meniton]`: shows [mention]'s current keyholder
    - `!subs`: lists your subs
    - `!subs [mention]`: lists [mention]'s subs''')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name='!help'))
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
