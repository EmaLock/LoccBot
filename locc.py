'''A discord bot to manage chastity'''
import datetime
import sqlite3
import sys

import discord
from discord.ext import commands
import key

TOKEN = key.TOKEN

DESCRIPITON = '''Manages chastity'''
BOT = commands.Bot(command_prefix='!', description=DESCRIPITON)
BOT.remove_command('help')

def database_query(query: str, parameters):
    '''sends a query to the database. It should be parametered with
    interrogation marks in place of the arguments, and the arguments should be
    in a list'''
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(query, parameters)
            return cursor.fetchall()
    except sqlite3.Error as error:
        print("An error occured:", error.args[0])

def get_mention(user: discord.User):
    ''''returns the mention of a user'''
    if user is None:
        mention = 'a user who is not here'
    else:
        mention = user.mention
    return mention

def has_mentions(message: discord.Message):
    '''returns True if the message has a mention'''
    if not message.mentions:
        return False
    return True

def get_first_mention_id(message: discord.Message):
    '''returns the userID of the first mention in a message'''
    return message.mentions[0].id

def get_first_mention_mention(message: discord.Message):
    '''returns a string to mention the first user mentioned in a message'''
    return message.mentions[0].mention

def get_author_id(message: discord.Message):
    '''returns the userID of the message's author'''
    return message.author.id

def get_author_mention(message: discord.Message):
    '''returns a string to mention the message's author'''
    return message.author.mention

def get_row_locked_id(locked_id: int):
    '''returns the rows matching a locked_id'''
    return database_query('''SELECT locked_id, keyholder_id, since_date
    FROM lock WHERE locked_id = ?''', [locked_id])

def get_row_keyholder_id(keyholder_id: int):
    '''returns the rows matching a keyholder_id'''
    return database_query('''SELECT locked_id, keyholder_id, since_date
    FROM lock WHERE keyholder_id = ?''', [keyholder_id])

def get_row_locked_id_keyholder_id(locked_id: int, keyholder_id: int):
    '''returns the rows matching BOTh a locked_id and a keyholder_id'''
    query = '''SELECT locked_id, keyholder_id, since_date
    FROM lock WHERE locked_id = ? AND keyholder_id = ?'''
    return database_query(query, [locked_id, keyholder_id])

def insert_new_session(locked_id: int, keyholder_id: int):
    '''insert a new session between a locked_id and a keyholder_id'''
    query = '''INSERT INTO lock (locked_id, keyholder_id, since_date)
    VALUES (?,?, strftime('%s','now', 'utc'))'''
    database_query(query, [locked_id, keyholder_id])

def delete_session_locked_id(locked_id: int):
    '''removes a session from a locked_id'''
    query = 'DELETE FROM lock WHERE locked_id = ?'
    database_query(query, [locked_id])

def delete_session_locked_id_keyholder_id(locked_id: int, keyholder_id: int):
    '''removes a session between a locked_id and keyholder_id'''
    # pylint: disable=C0103
    # disable the "doesn't conform to snake_case naming style"
    query = 'DELETE FROM lock WHERE  locked_id = ? AND keyholder_id = ?'
    database_query(query, [locked_id, keyholder_id])

def days_from_now(timestamp):
    '''returns the number of days between now and date'''
    now = datetime.datetime.utcnow()
    then = datetime.datetime.fromtimestamp(timestamp)
    delta = now - then
    days = delta.days
    return days

@BOT.command(pass_context=True)
async def lockme(context):
    '''locks the author to the mentioned keyholder'''
    message = context.message
    locked_mention = get_author_mention(message)
    locked_id = get_author_id(message)
    # needs a mention! Names [mention] as the author's keyholder
    if has_mentions(message):
        keyholder_id = get_first_mention_id(message)
        # check if locked_id is already locked
        locked_id_result = get_row_locked_id(locked_id)
        # check if locked_id is already in a session with keyholder_id
        keyholder_id_result = get_row_keyholder_id(keyholder_id)
        keyholder_mention = get_first_mention_mention(message)
        # if the locked is not in a session
        if locked_id_result == []:
            # if the wished keyholder is not in a session with the locked
            if keyholder_id_result == []:
                insert_new_session(locked_id, keyholder_id)
                say = 'Congratulations {locked}! You are now held by {keyholder}!'
                say = say.format(locked=locked_mention,
                                 keyholder=keyholder_mention)
                await BOT.say(say)
            else:
                say = '{locked}: you are already locked by {keyholder}!'
                say = say.format(locked=locked_mention, keyholder=keyholder_mention)
                await BOT.say(say)

        # if the locked is already locked
        else:
            say = '{locked}: you are already locked!'
            say = say.format(locked=locked_mention)
            await BOT.say(say)
    # if nobody has been mentioned
    else:
        say = '{locked}: you have to mention someone to be your keyholder!'
        say = say.format(locked=locked_mention)
        await BOT.say(say)

@BOT.command(pass_context=True)
async def unlockme(context):
    ''''unlocks the author from their keyholder'''
    server = context.message.server
    message = context.message
    locked_id = get_author_id(message)
    locked_mention = get_author_mention(message)
    locked_id_result = get_row_locked_id(locked_id)
    # if the locked is not in a session
    if locked_id_result == []:
        say = '{locked}: you are not locked (yet!)'
        say = say.format(locked=locked_mention)
        await BOT.say(say)
    # if the locked is in a session
    else:
        keyholder_id = locked_id_result[0]['locked_id']
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = get_mention(keyholder_user)
        delete_session_locked_id(locked_id)
        say = '{locked} is no longer held by {keyholder}'
        say = say.format(locked=locked_mention, keyholder=keyholder_mention)
        await BOT.say(say)

@BOT.command(pass_context=True)
async def unlock(context):
    '''needs a mention! Lets a keyholder free [mention]'''
    message = context.message
    keyholder_id = get_author_id(message)
    keyholder_mention = get_author_mention(message)
    if has_mentions(message):
        locked_id = get_first_mention_id(message)
        locked_mention = get_first_mention_mention(message)
        lock_result = get_row_locked_id_keyholder_id(locked_id, keyholder_id)
        # if the keyholder is NOT holding [mention]
        if lock_result == []:
            say = '{keyholder}: you are not holding {locked}'
            say = say.format(keyholder=keyholder_mention, locked=locked_mention)
            await BOT.say(say)
        # if the keyholder is holding [mention]
        else:
            delete_session_locked_id_keyholder_id(locked_id, keyholder_id)
            say = '{keyholder} is no longer holding {locked}'
            say = say.format(keyholder=keyholder_mention, locked=locked_mention)
            await BOT.say(say)
    else:
        say = '{keyholder}: you have to mention someone to unlock!'
        say = say.format(keyholder=keyholder_mention)
        await BOT.say(say)

@BOT.command(pass_context=True)
async def keyholder(context):
    '''shows who is currently holding the author or the [mention]'''
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
    keyholder_id_result = get_row_locked_id(locked_id)
    # if no results are returned, the author or [mention] is not help
    if keyholder_id_result == []:
        say = '{locked} is not held (yet!)'
        say = say.format(locked=locked_mention)
        await BOT.say(say)
    # if there is a result, get the keyholder and mention them!
    else:
        keyholder_id = keyholder_id_result[0]['keyholder_id']
        keyholder_user = server.get_member(str(keyholder_id))
        keyholder_mention = get_mention(keyholder_user)
        since_date = keyholder_id_result[0]['since_date']
        say = '{locked} has been held by {keyholder} for {days} day(s)'
        say = say.format(locked=locked_mention,
                         keyholder=keyholder_mention,
                         days=str(since_date))
        await BOT.say(say)

@BOT.command(pass_context=True)
async def subs(context):
    '''lists the subs of the author or [mention]'''
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
    locked_id_result = get_row_keyholder_id(keyholder_id)
    # if there is no results, the author or [mention] is not holding someone
    if locked_id_result == []:
        say = '{keyholder} is holding no one (yet!)'
        say = say.format(keyholder=keyholder_mention)
        await BOT.say(say)
    # if there are results, the author or [mention] is holding someone, mention them!
    else:
        locked_mentions = ''
        for locked in locked_id_result:
            locked_id = locked['locked_id']
            locked_user = server.get_member(str(locked_id))
            locked_mention = get_mention(locked_user)
            since_date = days_from_now(locked['since_date'])
            locked_mentions += ' {locked} ({days} day(s))'.format(locked=locked_mention,
                                                                  days=str(since_date))
        say = '{keyholder} is holding:{locked_mentions}'
        say = say.format(keyholder=keyholder_mention, locked_mentions=locked_mentions)
        await BOT.say(say)

@BOT.command()
async def help():
    '''list the commands'''
    # pylint: disable=W0622
    # disable the "redefining built-in" pylint message
    await BOT.say(
        '''Available commands:
    - `!lockme [mention]`: name [mention] as your keyholder
    - `!unlockme`: removes you from being held
    - `!unlock [mention]`: frees [mention] from your holding
    - `!keyholder`: shows your current keyholder
    - `!keyholder[mention]`: shows [mention]'s current keyholder
    - `!subs`: lists your subs
    - `!subs [mention]`: lists [mention]'s subs
*source: https://github.com/EmaLock/LoccBOT*''')

@BOT.event
async def on_ready():
    '''executed when the BOT is ready'''
    print('Logged in as')
    print(BOT.user.name)
    print(BOT.user.id)
    # for testing purposes only
    if 'test' in sys.argv:
        BOT.command_prefix = '?'
    await BOT.change_presence(game=discord.Game(name=BOT.command_prefix + 'help'))
    # Try to connect to database
    try:
        connection = sqlite3.connect('locc.db')
        with connection:
            cursor = connection.cursor()
            # for testing purposes only
            if 'test' in sys.argv:
                cursor.execute('DROP TABLE IF EXISTS lock')
            query = '''CREATE TABLE IF NOT EXISTS lock
            (keyholder_id INTEGER, locked_id INTEGER, since_date INTEGER)'''
            cursor.execute(query)
    except sqlite3.Error as error:
        print('An error occured:', error.args[0])

BOT.run(TOKEN)
