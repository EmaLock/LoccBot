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
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print("An error occured:", e.args[0])

def get_mention(user : discord.User):
    # returns the mention of a user
    if user == None:
        mention = 'a user who is not here'
    else:
        mention = user.mention
    return mention

def has_mentions(message : discord.Message):
    # returns True if the message has a mention
    if len(message.mentions) == 0:
        return False
    return True

def get_first_mention_id(message : discord.Message):
    # returns the userID of the first mention in a message
    return message.mentions[0].id

def get_first_mention_mention(message : discord.Message):
    # returns a string to mention the first user mentioned in a message
    return message.mentions[0].mention

def get_author_id(message : discord.Message):
    # returns the userID of the message's author
    return message.author.id

def get_author_mention(message : discord.Message):
    # returns a string to mention the message's author
    return message.author.mention

def get_row_where_locked_id(locked_id : int):
    # returns the rows matching a locked_id
    return database_query('SELECT locked_id, keyholder_id, CAST(julianday(\'now\') - julianday(since_date) as INTEGER) AS since_date FROM lock WHERE locked_id = ?', [locked_id])

def get_row_where_keyholder_id(keyholder_id : int):
    return database_query('SELECT locked_id, keyholder_id, CAST(julianday(\'now\') - julianday(since_date) as INTEGER) AS since_date FROM lock WHERE keyholder_id = ?', [keyholder_id])

def get_row_where_locked_id_and_keyholder_id(locked_id : int, keyholder_id : int):
    return database_query('SELECT locked_id, keyholder_id, CAST(julianday(\'now\') - julianday(since_date) as INTEGER) AS since_date FROM lock WHERE locked_id = ? AND keyholder_id = ?', [locked_id, keyholder_id])

def insert_new_session(locked_id : int, keyholder_id : int):
    database_query('INSERT INTO lock (locked_id, keyholder_id, since_date) VALUES (?,?, julianday(\'now\'))', [locked_id, keyholder_id])

def delete_session_with_locked_id(locked_id : int):
    database_query('DELETE FROM lock WHERE locked_id = ?', [locked_id])

def delete_session_with_locked_id_and_keyholder_id(locked_id: int, keyholder_id: int):
    database_query('DELETE FROM lock WHERE  locked_id = ? AND keyholder_id = ?', [locked_id, keyholder_id])


@bot.command(pass_context=True)
async def lockme(context):
    message = context.message
    locked_mention = get_author_mention(message)
    locked_id = get_author_id(message)
    # needs a mention! Names [mention] as the author's keyholder
    if has_mentions(message):
        keyholder_id = get_first_mention_id(message)
        # check if locked_id is already locked
        locked_id_result = get_row_where_locked_id(locked_id)
        # check if locked_id is already in a session with keyholder_id
        keyholder_id_result = get_row_where_keyholder_id(keyholder_id)
        keyholder_mention = get_first_mention_mention(message)
        # if the locked is not in a session
        if locked_id_result == []:
            # if the wished keyholder is not in a session with the locked
            if keyholder_id_result == []:
                insert_new_session(locked_id, keyholder_id)
                await bot.say('Congratulations {locked}! You are now held by {keyholder}!'.format(locked=locked_mention, keyholder=keyholder_mention))
            else:
                await bot.say('{locked}: you are already locked by {keyholder}!'.format(locked=locked_mention, keyholder=keyholder_mention))

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
    message = context.message
    locked_id = get_author_id(message)
    locked_mention = get_author_mention(message)
    locked_id_result = get_row_where_locked_id(locked_id)
    # if the locked is not in a session
    if locked_id_result == []:
        await bot.say('{locked}: you are not locked (yet!)'.format(locked=locked_mention))
    # if the locked is in a session
    else:
        keyholder_id = locked_id_result[0]['locked_id']
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = get_mention(keyholder_user)
        delete_session_with_locked_id(locked_id)
        await bot.say('{locked} is no longer held by {keyholder}'.format(locked=locked_mention, keyholder=keyholder_mention))

@bot.command(pass_context=True)
async def unlock(context):
    #needs a mention! Lets a keyholder free [mention]
    message = context.message
    keyholder_id = get_author_id(message)
    keyholder_mention = get_author_mention(message)
    if has_mentions(message):
        locked_id = get_first_mention_id(message)
        locked_mention = get_first_mention_mention(message)
        lock_result = get_row_where_locked_id_and_keyholder_id(locked_id, keyholder_id)
        # if the keyholder is NOT holding [mention]
        if lock_result == []:
            await bot.say('{keyholder}: you are not holding {locked}'.format(keyholder=keyholder_mention, locked=locked_mention))
        # if the keyholder is holding [mention]
        else:
            delete_session_with_locked_id_and_keyholder_id(locked_id, keyholder_id)
            await bot.say('{keyholder} is no longer holding {locked}'.format(keyholder=keyholder_mention, locked=locked_mention))
    else:
        await bot.say('{keyholder}: you have to mention someone to unlock!'.format(keyholder=keyholder_mention))

@bot.command(pass_context=True)
async def keyholder(context):
    #shows who is currently holding the author or the [mention]
    server = context.message.server
    message = context.message
    # if someone is mentioned, get the current keyholder of the mentioned person
    if has_mentions(message):
        locked_id = get_first_mention_id(message)
        locked_mention = get_first_mention_mention(message)
    # else, get the current keyholder of the author
    else:
        locked_id = get_author_id(message)
        locked_mention = get_author_mention(message)
    keyholder_id_result = get_row_where_locked_id(locked_id)
    # if no results are returned, the author or [mention] is not help
    if keyholder_id_result == []:
        await bot.say('{locked} is not held (yet!)'.format(locked=locked_mention))
    # if there is a result, get the keyholder and mention them!
    else:
        keyholder_id = keyholder_id_result[0]['keyholder_id']
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = get_mention(keyholder_user)
        since_date = keyholder_id_result[0]['since_date']
        await bot.say('{locked} has been held by {keyholder} for {days} day(s)'.format(locked=locked_mention, keyholder=keyholder_mention, days=str(since_date)))

@bot.command(pass_context=True)
async def subs(context):
    #lists the subs of the author or [mention]
    server = context.message.server
    message = context.message
    # if someone is mentioned, get the current subs of the mentioned person
    if has_mentions(message):
        keyholder_id = get_first_mention_id(message)
        keyholder_mention = get_first_mention_mention(message)
    # else, get the current subs of the author
    else:
        keyholder_id = get_author_id(message)
        keyholder_mention = get_author_mention(message)
    locked_id_result = get_row_where_keyholder_id(keyholder_id)
    # if there is no results, the author or [mention] is not holding someone
    if locked_id_result == []:
        await bot.say('{keyholder} is holding no one (yet!)'.format(keyholder=keyholder_mention))
    # if there are results, the author or [mention] is holding someone, mention them!
    else:
        locked_mentions = ''
        for locked in locked_id_result:
            locked_id = locked['locked_id']
            locked_user = server.get_member(str(locked_id))
            locked_mention = get_mention(locked_user)
            since_date = locked['since_date']
            locked_mentions += ' {locked} ({days} day(s))'.format(locked=locked_mention, days=str(since_date))
        await bot.say('{keyholder} is holding:{locked_mentions}'.format(keyholder=keyholder_mention, locked_mentions=locked_mentions))

@bot.command()
async def help():
    # list the commands
    await bot.say(
'''Available commands:
    - `!lockme [mention]`: name [mention] as your keyholder
    - `!unlockme`: removes you from being held
    - `!unlock [mention]`: frees [mention] from your holding
    - `!keyholder`: shows your current keyholder
    - `!keyholder[mention]`: shows [mention]'s current keyholder
    - `!subs`: lists your subs
    - `!subs [mention]`: lists [mention]'s subs
*source: https://github.com/EmaLock/LoccBot*''')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    # for testing purposes only
    if 'test' in sys.argv:
        bot.command_prefix = '?'
    await bot.change_presence(game=discord.Game(name=bot.command_prefix + 'help'))
    # Try to connect to database
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            # for testing purposes only
            if 'test' in sys.argv:
                cursor.execute('DROP TABLE IF EXISTS lock')
            cursor.execute('CREATE TABLE IF NOT EXISTS lock (keyholder_id INTEGER, locked_id INTEGER, since_date INTEGER)')
    except sqlite3.Error as e:
        print('An error occured:', e.args[0])

bot.run(TOKEN)
