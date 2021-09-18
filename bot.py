import discord
import asyncio
import json
import os
import csv
from io import StringIO
import cardInfo
import constants
from draft import *

#------------CONSTANTS------------

client = discord.Client()

# Draft specifications
PACK_SIZE = constants.PACK_SIZE
NUM_PACKS = constants.NUM_PACKS
NUM_PLAYERS = constants.PLAYERS_PER_DRAFT

STAPLES_CUB = constants.STAPLES_CUB

# Draft creation limitations
ALLOWED_CHANNELS = constants.ALLOWED_CHANNELS
MAX_DRAFTS = constants.DRAFTS_PER_CHANNEL

# 15 < IGNORED_REACTION. Reactions are mapped from 1-15 based
# on PACK_SIZE, so the ignored value must be greater than those
# values
IGNORED_REACTION = 100

# Command information
COMMAND_LIST = constants.COMMAND_LIST
COMMANDS = constants.COMMANDS
ADMIN_COMMANDS = constants.ADMIN_COMMANDS
COMMAND_CLASSES = list(COMMANDS.keys())
COMMAND_GUIDES = constants.COMMAND_GUIDES
ADMIN_COMMAND_GUIDES = constants.ADMIN_COMMAND_GUIDES

# Card charcteristics
attributes = constants.ATTRIBUTES
levels = constants.LEVELS
monsterTypes = constants.MONSTER_TYPES
cardTypes = constants.CARD_TYPES

# Maps: channel names->{draft names->drafts}
drafts = {}
# Maps: cube filenames->cards (cardInfo objects)
cubes = {}
# Maps: set filenames->{rarities->cards (cardInfo objects)}
sets = {}
# Maps: staples filenames->cards (cardInfo objects)
staples = {}
# Maps: id of users current playing ->{draftInformation}
# draftInformation contains the following mappings:
#   "draftName"->name of draft player is playing in
#   "draftChannel"->channel of draft player is playing in
currentPlayers = {}

#------------HELPER METHODS------------

# Import and map cube files to their card pools.
def __import_cubes():
    global cubes
    for cub in os.listdir('cubes'):
        if cub.endswith('.cub'):
            CardList = []
            print('Cube list discovered. Importing.')
            with open('cubes/' + cub) as cubeFile:
                cardDict = json.load(cubeFile)
                # Instantiate a new CardInfo object for each card in the list. Definitely could pull in more info from the JSON - there's a lot there.
                for card in cardDict:
                    CardList.append(cardInfo.cardJsonToCardInfo(card))
            cubes[cub] = CardList

# Import and map staple files to their card pools.
def __import_staples():
    global staples
    for cub in os.listdir('cubes/staples'):
        if cub.endswith('.cub'):
            CardList = []
            print('Staple list discovered. Importing.')
            with open('cubes/staples/' + cub) as stapleFile:
                cardDict = json.load(stapleFile)
                # Instantiate a new CardInfo object for each card in the list. Definitely could pull in more info from the JSON - there's a lot there.
                for card in cardDict:
                    CardList.append(cardInfo.cardJsonToCardInfo(card))
            staples[cub] = CardList
            if len(staples[cub]) != NUM_STAPLES:
                raise Exception('staples/' + str(cub) + 'does not contain ' + str(NUM_STAPLES) + ' cards')

# Dictionaries mapping cards to certain characteristics
def __createAttributeDictionary(cardList):
    global attributes
    attributeDict = {} 
    for attr in attributes:
        # Add an entry to our dictionary with the attribute name and count of cards with that attribute
        attributeDict[attr] = len([card for card in cardList if card.attribute == attr])
    return {'**' + str(k) + '**': v for k, v in sorted(attributeDict.items(), key=lambda item: item[1], reverse=True) if v != 0}
    
def __createTypeDictionary(cardList):
    global monsterTypes
    monsterTypeDict = {} 
    for monsterType in monsterTypes:
        # Add an entry to our dictionary with the type name and count of cards with that type
        monsterTypeDict[monsterType] = len([card for card in cardList if card.race == monsterType])
    return {'**' + str(k) + '**': v for k, v in sorted(monsterTypeDict.items(), key=lambda item: item[1], reverse=True) if v != 0}

def __createLevelDictionary(cardList):
    global levels
    levelDict = {} 
    for level in levels:
        # Add an entry to our dictionary with the level and count of cards of that level (not in extra)
        levelDict[level] = len([card for card in cardList if card.level == level and 'synchro' not in card.cardType.lower() and 'xyz' not in card.cardType.lower()])
    return {'**Level ' + str(k) + '**': v for k, v in levelDict.items() if v != 0}

def __createTunerDictionary(cardList):
    global levels
    tunerDict = {} 
    for level in levels:
        # Add an entry to our dictionary with the level and count of tuners with that level
        tunerDict[level] = len([card for card in cardList if card.level == level and 'tuner' in card.cardType.lower() and 'synchro' not in card.cardType.lower()])
    return {'**Level ' + str(k) + '**': v for k, v in tunerDict.items() if v != 0}

def __createExtraMessage(cardList):
    global levels
    fusionDict = {}
    syncDict = {} 
    xyzDict = {} 
    for level in levels:
        # Add an entry to fusion dictionary with the level and count of synchros with that level
        fusionDict[level] = len([card for card in cardList if card.level == level and 'fusion' in card.cardType.lower()])
        # Add an entry to synchro dictionary with the level and count of synchros with that level
        syncDict[level] = len([card for card in cardList if card.level == level and 'synchro' in card.cardType.lower()])
        # Add an entry to xyz dictionary with the level and count of xyz with that level
        xyzDict[level] = len([card for card in cardList if card.level == level and 'xyz' in card.cardType.lower()])
    fusionOutput = '__Fusion__ ' + str({'**Level ' + str(k) + '**': v for k, v in fusionDict.items() if v != 0})
    syncOutput = '__Synchro__ ' + str({'**Level ' + str(k) + '**': v for k, v in syncDict.items() if v != 0})
    xyzOutput = '__XYZ__ ' + str({'**Rank ' + str(k) + '**': v for k, v in xyzDict.items() if v != 0})
    return fusionOutput + '\n' + syncOutput + '\n' + xyzOutput 

def __createSpreadDictionary(cardList):
    global cardTypes
    cardTypeDict = {} 
    for cardType in cardTypes:
        # Add an entry to our dictionary with the level and count of cards with that card type
        cardTypeDict[cardType] = len([card for card in cardList if cardType.lower() in card.cardType.lower()])
    return {'**' + str(k) + '**': v for k, v in cardTypeDict.items() if v != 0}
    
# Filter for commands being issued in the correct channels
async def __allowChannel(message):
    # Check if command was issued in #draft and has two arguments
    if message.channel.name == 'general':
        await message.channel.send('https://www.youtube.com/watch?v=2cPW2xDKUIU')
    if isinstance(message.channel, discord.DMChannel) or message.channel.name not in ALLOWED_CHANNELS:
        outputMsg = 'Command can only be issued in channel(s) named '
        lastChannel = len(ALLOWED_CHANNELS) - 1
        for channel in range(lastChannel):
            outputMsg += '#' + ALLOWED_CHANNELS[channel] + ', '
        outputMsg += '#' + ALLOWED_CHANNELS[lastChannel]
        await message.channel.send(outputMsg)
        return False
    return True


#------------INITIALIZATION------------

__import_cubes()
print('Cubes imported')
__import_staples()
print('Staples imported')

# Load the bot's API key from config.json
key = None
with open('config.json', 'r') as config_file:
    config_json = json.load(config_file)
    key = config_json['key']

#------------EVENT RESPONSES------------

# If the user reacts to a bot message in DMs while in a draft with packs
# available, pick a card from the pack based on the reaction
@client.event
async def on_raw_reaction_add(payload):
    global drafts

    userID = payload.user_id
    botID = client.user
    channelType = str(type(client.get_channel(payload.channel_id)))
    emoji = str(payload.emoji.name)
    
    # Makes sure:
    # (1) Reaction is in DM
    # (2) Reaction is not from a bot
    # (3) Reaction is from a user currently playing
    # (4) the draft has started.
    if ('DMChannel' not in channelType or userID == botID or userID not in currentPlayers):
        return
        
    authorDraftName = currentPlayers[userID]["draftName"]
    authorDraftChannel = currentPlayers[userID]["draftChannel"]
    draft = drafts[authorDraftChannel][authorDraftName]
    player = draft.players[userID]

    if draft.draftStarted():
        # Pick a card from pack if the reaction can be mapped to a card in the pack
        # (1-9 for cards 1 to 9, 0 for card 10, then A-E for cards 11 - 15
        # If the reaction can't be mapped, ignore it
        cardIndex = reactions.index(emoji) if emoji in reactions else IGNORED_REACTION
        player.pick(cardIndex)
    return

# Responds to user messages based on contained command
@client.event
async def on_message(message):
    global drafts
    global cubes

    author = message.author
    msgChannel = message.channel
    splitMsg = message.content.lower().strip().split()
    
    # Ignores the bots own messages and empty messages
    if author == client.user or len(splitMsg) == 0:
        return

    #------------USER COMMANDS------------

    # View commands and their descriptions, optionally filtered 
    # Usage: !gamehelp *filter
    #   where filter can be a command class: "draft", "show", "my", "match"
    #   where filter can be a command: (any of the commands listed below without "!")
    #   where filter can be a guide: "rules", "startguide", "adminguide", "cubeguide"
    if '!gamehelp' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) > 2:
            await msgChannel.send('Command should be used in the form \"!gamehelp *filter\", ' +
                'where filter can be a command, a command class(' + str(COMMAND_CLASSES) + '), or a guide(' +
                str(COMMAND_GUIDES) + ')')
            return
        
        if len(splitMsg) == 2:
            argument = splitMsg[1]
            if argument in COMMAND_CLASSES:
                # Print out complex definitions of commands in the requested class
                commandClass = argument
                outputMsg = '```css\n.' + commandClass + ': ' + COMMANDS[commandClass]['classDescription'] + '```\n'
                for command, definitions in COMMANDS[commandClass].items():
                    if command != 'classDescription':
                        outputMsg += '**!' + command + '** - ' + definitions['complexDef'] + '\n\n'
                if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
                    if commandClass in ADMIN_COMMANDS.keys():
                        for adminCommand, adminDefinitions in ADMIN_COMMANDS[commandClass].items():
                            outputMsg += '__**!' + adminCommand + '**__ - ' + adminDefinitions['complexDef'] + '\n\n'
                await msgChannel.send('I sent you the requested gamehelp command class!')
                await author.send(outputMsg)
            elif argument in COMMAND_LIST.keys():
                # Print out complex definition of requested command
                try:
                    complexDef = COMMANDS[COMMAND_LIST[argument]][argument]['complexDef']
                    await msgChannel.send('I sent you the requested gamehelp command definition!')
                    await author.send('**' + argument + '** - ' + complexDef + '\n')
                except KeyError as e:
                    if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
                        complexDef = ADMIN_COMMANDS[COMMAND_LIST[argument]][argument]['complexDef']
                        await msgChannel.send('I sent you the requested gamehelp command definition!')
                        await author.send('__**' + argument + '**__ - ' + complexDef + '\n')
                    else:
                        await msgChannel.send('That command can only be viewed by admins!')
            elif argument in COMMAND_GUIDES.keys():
                # Print out requested user guide
                # Maybe use dictionary to reduce ifs
                await author.send(COMMAND_GUIDES[argument])
                await msgChannel.send('I sent you the requested gamehelp user guide!')
            elif argument in ADMIN_COMMAND_GUIDES.keys():
                # Print out requested admin guide if user is admin
                if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
                    await author.send(ADMIN_COMMAND_GUIDES[argument])
                    await msgChannel.send('I sent you the requested gamehelp admin guide!')
                else:
                    await msgChannel.send('That guide can only be viewed by admins!')
            else:
                await msgChannel.send('Invalid filter argument! Check \"!gamehelp gamehelp\"!')
        else:
            outputMsg = ('```css\n[DRAFTBOT MANUAL]\n' +
                        'Can view more detailed information about subset of commands with \"!gamehelp commandclass\", ' +
                        'where commandclass\n\tis one of the following: ' + str(COMMAND_CLASSES) + '\n\n' +
                        'Can view more detailed information about a specific command with \"!gamehelp command\" ' + 
                        '(ex. \"!gamehelp gamehelp\")\n\n' + 'Can view guides with \"!gamehelp guide\". Current guides: ' +
                        str(COMMAND_GUIDES) + '```\n')
                        
            if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
                outputMsg += 'Admin-only commands are underlined.\n' +'__Admin Guides__: ' + str(ADMIN_COMMAND_GUIDES) + '\n'
            # Print the basic information for each command, including admin commands if player is admin
            for commandClass in COMMAND_CLASSES:
                # Make sure message doesn't exceed discord message cap
                if len(outputMsg) > 1600:
                    await author.send(outputMsg)
                    outputMsg = '_ _'
                try:
                    classCommands = COMMANDS[commandClass]
                    outputMsg += '\n**' + commandClass + '**: '
                    for command in classCommands:
                        if command == 'classDescription':
                            outputMsg += classCommands[command] + '\n'
                        else:
                            outputMsg += '\t!' + command + ' - ' + classCommands[command]['basicDef'] + '\n'
                    if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
                        classAdminCommands = ADMIN_COMMANDS[commandClass]
                        for adminCommand in classAdminCommands:
                            outputMsg += '\t__!' + adminCommand + '__ - ' + classAdminCommands[adminCommand]['basicDef'] + '\n'
                except KeyError as e:
                    continue
            await msgChannel.send('I sent you the requested gamehelp manual!')
            await author.send(outputMsg)
        return
        


    # Creates a draft from a user-specified .cub file with a user-specified name
    # Usage: !draftcreate cubefile draftname
    if '!draftcreate' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 3:
            await msgChannel.send('Command should be used in form \"!draftcreate cubefile draftname\", ' +
                 'where cubefile is one of the following: ' + str(list(cubes.keys())))
            return
 
        cubeFile = splitMsg[1]
        draftName = splitMsg[2]

        # Check if the user-specified .cub file exists
        if cubeFile in cubes:
            # Check if the user-specified .cub contains adequate number of cards
            requiredCubeSize = PACK_SIZE * NUM_PACKS * NUM_PLAYERS
            userCubeSize = len(cubes[cubeFile])

            if (userCubeSize < requiredCubeSize):
                await msgChannel.send('Cube ' + cubeFile + ' has ' + str(userCubeSize) +
                    ' cards, but you need '  + str(requiredCubeSize))
            else:
                # Check if a draft already exists in the channel the command was issued in
                # Add the new draft to the other name->draft mappings if drafts existed in the channel prior
                if msgChannel in drafts:
                    # Check if a draft with the same name already exists in the channel the command was issued in
                    if draftName in drafts[msgChannel]:
                        await msgChannel.send('Cannot create a draft with the same name as one ' +
                            'that already exists in this channel')
                        return
                    elif len(drafts[msgChannel]) >= MAX_DRAFTS:
                        await msgChannel.send('Only ' + str(MAX_DRAFTS) + ' drafts are allowed in a channel!')
                        return
                    else:
                        if STAPLES_CUB == None:
                            drafts[msgChannel][draftName] = Draft(draftName, cubes[cubeFile], msgChannel)
                        else:
                            drafts[msgChannel][draftName] = Draft(draftName, cubes[cubeFile], msgChannel, staples[STAPLES_CUB])
                # Create a new channel->{name->draft} mapping otherwise
                else:
                    if STAPLES_CUB == None:
                        drafts[msgChannel] = {draftName: Draft(draftName, cubes[cubeFile], msgChannel)}
                    else:
                        drafts[msgChannel] = {draftName: Draft(draftName, cubes[cubeFile], msgChannel, staples[STAPLES_CUB])}
                await msgChannel.send('Draft created. Players can now join.')
        else:
            await msgChannel.send('Cube not found, please enter one from this list next time:\n' + str(list(cubes.keys())))
        return

    # Join user-specified draft in the message channel if it exists. If that draft now contains NUM_PLAYERS players,
    # ready check players and then fire the draft if all players are ready
    # Usage: !draftjoin draftname (in channel of draft)
    if '!draftjoin' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 2:
            await msgChannel.send('Command should be used in form \"!draftjoin draftname\" ' +
                 'in the channel of the draft you want to join. Use \"!showdrafts\" to show ' +
                 'current drafts, or \"!draftcreate\" to create a draft in the channel you are in.')
            return

        draftName = splitMsg[1]
        tryCreateDraft = ' Try \"!draftcreate\" to create a draft.'
        
        # Makes sure:
        # (1) Player is not already playing
        # (2) there is a draft in the channel,
        # (3) the draft has the user-specified name
        # (4) the draft has not started.
        # (5) the draft is not full
        if author.id in currentPlayers:
            await msgChannel.send('You are already in a draft!' + 
                ' Try \"!draftleave\" to leave the draft you are in.')
            return
                    
        try:
            draft = drafts[msgChannel][draftName]
            
            if draft.draftStarted():
                await msgChannel.send('Draft \"' + draftName + '\" is already in progress.' + tryCreateDraft)
            elif len(draft.players) >= NUM_PLAYERS:
                await msgChannel.send('Draft \"' + draftName + '\" is full!' + tryCreateDraft)
            else:
                draft.players[author.id] = Player(author, draft)
                currentPlayers.update({author.id: {"draftName": draftName, "draftChannel": msgChannel}})
                await msgChannel.send(author.name + ' has joined the draft!')
                # If the player that joined was the fourth, issue a ready check to see if players respond
                if len(draft.players) == NUM_PLAYERS:
                    await msgChannel.send('Draft \"' + draftName + '\" is ready to fire! All participants ' +
                        'please respond to the ready check in DMs within the next 15 seconds!')
                    for player in draft.players.values():
                        await player.user.send('Draft \"' + draftName + '\" is ready to fire! Please respond with ' +
                        '\"y\" or \"n\" to indicate whether or not you are ready in the next 15 seconds!')
                    timer = Timer(length = 11)
                    readyPlayers = []               
                    afkPlayers = []
                    # Timer has expired
                    # OR
                    # Ready check passes if user is a player in the draft that has not already responded, and
                    # the message is in DMs and starts with "y" or "n"
                    def check(m):
                        return (timer.expired == True or m.author.id in draft.players and
                            isinstance(m.channel, discord.DMChannel) and
                            m.author not in readyPlayers and m.author not in afkPlayers and
                            (m.content.lower().startswith("y") or m.content.lower().startswith("n")))
                    
                    while timer.expired == False and len(readyPlayers) < NUM_PLAYERS:
                        response = await client.wait_for('message', check = check)
                        # Ignore messages very near the end of the timer
                        if timer.expired == False:
                            if response.content.lower().startswith("y"):
                                await msgChannel.send('Player ' + response.author.name + ' is ready!')
                                await response.author.send("You have confirmed that you are ready!")
                                readyPlayers.append(response.author)
                            elif response.content.lower().startswith("n"):
                                await msgChannel.send('Player ' + response.author.name + ' is NOT ready!')
                                await response.author.send("You have confirmed that you are NOT ready!")
                                afkPlayers.append(response.author)
                    
                    # All players that did not respond in time are treated as AFK
                    for player in draft.players.values():
                        if player.user not in readyPlayers and player.user not in afkPlayers:
                            await msgChannel.send('Player ' + player.user.name + ' did not respond ' +
                                'to the ready check in time!')
                            await player.user.send("You did not respond in time for draft \"" + draftName +
                                "\" in channel " + str(msgChannel))
                            afkPlayers.append(player.user)

                    for player in afkPlayers:
                        currentPlayers.pop(player.id)
                        draft.kick(player.id)
                    # Check that all players are ready and no one left in the middle of ready check
                    if len(readyPlayers) == NUM_PLAYERS and len(draft.players) == NUM_PLAYERS:
                        await msgChannel.send(str(NUM_PACKS * NUM_PLAYERS) + ' packs of Draft, starting NOW!')
                        draft.startDraft()
                    else:
                        await msgChannel.send('The ready check has failed. Draft \"' + draftName + '\" cannot fire :(.')
        except KeyError as e:
            await msgChannel.send('Draft \"' +  draftName + 
                '\" does not exist in this channel. Use \"!showdrafts\" to show current drafts.')
        return



    # Player leaves draft if they are in one that has not started in the message channel
    # Usage: !draftleave
    if '!draftleave' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 1:
            await msgChannel.send('Command should be used in form \"!draftleave\" ' +
                 'in the channel of the draft you want to leave.')
            return
        
        try:
            authorDraftName = currentPlayers[author.id]["draftName"]
            authorDraftChannel = currentPlayers[author.id]["draftChannel"]
            draft = drafts[authorDraftChannel][authorDraftName]
            if not draft.draftStarted():
                currentPlayers.pop(author.id)
                draft.kick(author.id)
                await msgChannel.send(author.name + ' has left draft \"' + authorDraftName + '\"!')
            else:
                await msgChannel.send('You may not leave in-progress draft')
            return
            await msgChannel.send('You are not in any drafts in this channel.')
        except KeyError as e:
            await msgChannel.send('You are not currently in any drafts.')
        return

    # View drafts in message channel
    # Usage: !showdrafts
    if ('!showdrafts') == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 1:
            await msgChannel.send('Command should be used in form \"!showdrafts\"')
            return
        if len(drafts) == 0:
            await msgChannel.send('There are no drafts at the moment!')
        else:
            # Print the drafts in each channel as separate messages
            for channel, channelDrafts in drafts.items():
                outputMsg = ''
                outputMsg += 'Drafts in: #' + str(channel.name)
                for draftName, draft in channelDrafts.items():
                    outputMsg += '\n\t' + draftName + ': ('
                    if len(draft.players) == NUM_PLAYERS:
                        outputMsg += 'In Progress)'
                    else:
                        outputMsg += (str(len(draft.players)) +
                            '/' + str(NUM_PLAYERS) + ') queued')
            await msgChannel.send(outputMsg)      
        return

    # Sends the name of all registered players in user-specified draft in message channel
    # Usage: !showplayers draftname
    if '!showplayers' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 2: 
            await msgChannel.send('Command should be used in form \"!showplayers draftname\", ' +
                'in the channel of the draft you want to view the players of. ' + 
                'Use \"!showdrafts\" to show current drafts.')
            return
        draftName = splitMsg[1]
        
        # If the draft exists, show all players in the draft
        try:
            outputMsg = 'Players in draft ' + draftName + ': ['
            for player in drafts[msgChannel][draftName].players.values():
                outputMsg += player.user.name + ' '
            await msgChannel.send(outputMsg.rstrip() + ']')
        except KeyError as e:
            await msgChannel.send('Draft \"' +  draftName + 
                '\" does not exist in this channel. Use !showdrafts to show current drafts.')
        return

    # Shows the cards drafted by user. Cards shown can be filtered optionally
    # based on additional argument
    # Usage: !mypool *filter
    #   where filter can be "attr", "type", "level", "tuner", "extra", "all"
    if '!mypool' == splitMsg[0]:
        if len(splitMsg) > 2:
            await msgChannel.send('Command should be used in form \"!mypool *filter\", ' +
            'where filter is optional and can be \"attr\", \"type\", \"level\", \"tuner\", ' +
            '\"extra\", or \"all\"')
            return

        try:
            authorDraftName = currentPlayers[author.id]['draftName']
            authorDraftChannel = currentPlayers[author.id]['draftChannel']
            draft = drafts[authorDraftChannel][authorDraftName]
            player = draft.players[author.id]
            if not draft.draftStarted():
                await msgChannel.send('The draft(' + authorDraftName + ') you\'re in has not started.')
                return
            temppool = player.pool[:]
            if ('attr' in splitMsg): 
                await msgChannel.send(__createAttributeDictionary(temppool))
            elif ('type' in splitMsg):
                await msgChannel.send(__createTypeDictionary(temppool))
            elif ('level' in splitMsg):
                await msgChannel.send(__createLevelDictionary(temppool))
            elif ('tuner' in splitMsg):
                await msgChannel.send(__createTunerDictionary(temppool))
            elif ('extra' in splitMsg):
                await msgChannel.send(__createExtraMessage(temppool))
            elif ('all' in splitMsg):
                await author.send(temppool)
            elif len(splitMsg) == 1:
                mainMonsters = [card for card in temppool if 'monster' in card.cardType.lower() and
                               'synchro' not in card.cardType.lower() and
                               'xyz' not in card.cardType.lower() and
                               'fusion' not in card.cardType.lower()]
                if(len(mainMonsters) > 0):
                    #Async so they dont stall the other messages waiting for the response from the server
                    asyncio.create_task(msgChannel.send('**Monsters (' + str(len(mainMonsters)) + '):** ' + str(mainMonsters)))
                spells = [card for card in temppool if 'spell' in card.cardType.lower()]
                if(len(spells) > 0):
                    asyncio.create_task(msgChannel.send('**Spells (' + str(len(spells)) + '):** ' + str(spells)))        
                traps = [card for card in temppool if 'trap' in card.cardType.lower()]
                if(len(traps) > 0):
                    asyncio.create_task(msgChannel.send('**Traps (' + str(len(traps)) + '):** ' + str(traps)))
                extra = [card for card in temppool if 'xyz' in card.cardType.lower() or
                        'synchro' in card.cardType.lower() or
                        'fusion' in card.cardType.lower()]
                if(len(extra) > 0):
                    asyncio.create_task(msgChannel.send('**Extra Deck (' + str(len(extra)) + '):** ' + str(extra)))
            else:
                await msgChannel.send('Filter \"' + splitMsg[1] + '\" not found')
        except KeyError as e:
            await msgChannel.send('You are not in a draft.')
        return

    # Extracts the cards drafted by user into a .ydk file
    # Usage: !myydk
    if '!myydk' == splitMsg[0]:
        if len(splitMsg) != 1:
            await msgChannel.send('Command should be used in form \"!myydk\"')
            return
        
        try:
            authorDraftName = currentPlayers[author.id]['draftName']
            authorDraftChannel = currentPlayers[author.id]['draftChannel']
            draft = drafts[authorDraftChannel][authorDraftName]
            player = draft.players[author.id]
            if not draft.draftStarted():
                await msgChannel.send('The draft(' + authorDraftName + ') you\'re in has not started.')
                return
            tempidpoolnoextra = []
            tempidpoolextra = []
            tempidpoolside = []
            overflow_counter = 0

            for card in player.pool:
                #print('card name = {0}, card type = {1}, card id = {2}'.format(card.name, card.cardType, card.id))
                if (card.cardType != (('Synchro Monster') or ('Synchro Tuner Monster')) and
                    (card.cardType != 'XYZ Monster') and
                    (card.cardType != 'Fusion Monster')):                
                    tempidpoolnoextra.append(card.id) #puts the ids of the main deck cards in a list
                elif ('xyz' in card.cardType.lower() or
                    'synchro' in card.cardType.lower() or 
                    'fusion monster' in card.cardType.lower()):
                    #Puts the ids of the extra deck cards in the extra deck if there's room
                    if (overflow_counter < 14):
                        tempidpoolextra.append(card.id) 
                        overflow_counter = overflow_counter + 1
                    #Otherwise store extra deck cards in side deck
                    else: 
                        tempidpoolside.append(card.id) #puts the ids of the extra deck cards in an overflow side list

            #This whole block formats their cards for the .ydk format
            ydkString = ''
            ydkstuff = ['#created by ...', '#main']
            for listitem in ydkstuff: #puts in the necessary ydk stuff
                ydkString+='%s\n' % listitem
            for listitem in tempidpoolnoextra:
                ydkString+=('%s\n' % listitem) #should put main deck cards in the ydk file
            ydkextraline = ['#extra']
            for listitem in ydkextraline: #Stuff after this gets put in the extra deck (until side)
                ydkString+='%s\n' % listitem
            for listitem in tempidpoolextra:
                ydkString+='%s\n' % listitem
            ydksidestuff = ['!side'] #Stuff after this gets put in the side
            for listitem in ydksidestuff:
                ydkString+='%s\n' % listitem           
            for listitem in tempidpoolside:
                ydkString+='%s\n' % listitem

            asyncio.create_task(author.send(file = discord.File(fp = StringIO(ydkString),filename = 'YourDraftPool.ydk')))
            return
        except KeyError as e:
            await msgChannel.send('You are not in a draft.')
        return

    # Reports a loss to another player, ending the draft if the loss was the final match
    # Usage: !matchloss @player
    if '!matchloss' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        elif len(splitMsg) != 2 or len(message.mentions) != 1: 
            await msgChannel.send('Command should be used in form \"!matchloss @player\", ' +
                'in the channel of the draft you want to report the loss from. ' + 
                'Use \"!showdrafts\" to show current drafts.')
            return
        player = message.mentions[0]
        
        if author.id == player.id:
            await msgChannel.send('Can\'t report a loss to yourself.')
            return
        
        # Makes sure:
        # (1) Both in a draft
        # (2) Both in the same draft
        # (3) Loss was reported in same channel as draft
        # (4) The draft they are both in has started
        # (5) The players are matched against each other
        try:
            authorDraftName = currentPlayers[author.id]['draftName']
            authorDraftChannel = currentPlayers[author.id]['draftChannel']
            
            playerDraftName = currentPlayers[player.id]['draftName']
            playerDraftChannel = currentPlayers[player.id]['draftChannel']
            
            if authorDraftName == playerDraftName and authorDraftChannel == playerDraftChannel:
                # Should be the same as drafts[playerDraftChannel][playerDraftName]
                draft = drafts[authorDraftChannel][authorDraftName]
                if msgChannel != draft.channel:
                    await msgChannel.send('Please report the loss in the same channel as the draft you\'re in(' +
                        draft.channel.mention + ').')
                elif not draft.draftStarted():
                    await msgChannel.send('The draft(' + authorDraftName + ') you\'re in has not started.')
                elif not draft.gameStarted():
                    await msgChannel.send('The draft(' + authorDraftName + ') you\'re in has not started its games.')
                elif (draft.players[author.id].matchesPlayed == draft.currentRound or
                    draft.players[player.id].matchesPlayed == draft.currentRound):
                    await msgChannel.send('Either you or ' + player.name + ' reported the loss this round ' +
                            'already.')
                elif not draft.pairExists(author.id, player.id, draft.currentRound):
                    await msgChannel.send('You and player ' + player.name + ' are not paired against one another!')
                else:
                    if not draft.reportLoss(author.id, player.id):
                        await msgChannel.send('Either you or ' + player.name + ' reported the loss this round ' +
                            'already.')
                        return
                    await msgChannel.send('Your loss against ' + player.name + ' has been recorded.')
                    
                    # Check if the reported loss was the final match and delete the draft if it was
                    if draft.currentRound > len(draft.matches):
                        drafts[msgChannel].pop(authorDraftName)
            else:
                await msgChannel.send('You are not in the same draft as ' + player.name + '!')
            
        except (KeyError, ValueError) as e:
            if author.id not in currentPlayers:
                await msgChannel.send('You are not currently in a draft!')
            elif player.id not in currentPlayers:
                await msgChannel.send('Player ' + player.name + ' is not currently in a draft!')
            else:
                await msgChannel.send('There was an error reporting a loss: ' + e)
        return


    #------------ADMIN/MOD COMMANDS------------

    # Manually fires user-specified draft in the message channel if it exists.
    # Usage: !draftstart draftname
    if '!draftstart' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles):
            if len(splitMsg) != 2: 
                await msgChannel.send('Command should be used in form \"!draftstart draftname\" ' +
                    'in the channel of the draft you want to manually start. ' +
                    'Use \"!showdrafts\" to show current drafts.')
                return
            draftName = splitMsg[1]

            # If the draft exists and is full and unstarted, start the draft
            try:
                draft = drafts[msgChannel][draftName]
                if draft.draftStarted():
                    await msgChannel.send('Draft \"' +  draftName + 
                        '\" has already started!')
                elif len(draft.players) != NUM_PLAYERS:
                    await msgChannel.send('Draft \"' +  draftName + 
                        '\" does not have ' + str(NUM_PLAYERS) + ' player(s)!')
                else:
                    draft.startDraft()   
                    await msgChannel.send('The draft is MANUALLY starting! ' +
                        'All players have received their first pack. Good luck!')
            except KeyError as e:
                await msgChannel.send('Draft \"' +  draftName + 
                    '\" does not exist in this channel. Use ' +
                    '\"!showdrafts\" to show current drafts')
        else:
            await msgChannel.send('Only admins or moderators can manually start a draft')
        return

    # Manually concludes and deletes a user-specified draft in the message channel if it exists.
    # Usage: !draftend draftname
    if '!draftend' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) != 2: 
                await msgChannel.send('Command should be used in form \"!draftend draftname\" ' +
                    'in the channel of the draft you want to manually end. ' +
                    'Use !showdrafts to show current drafts.')
                return
            draftName = splitMsg[1]
            
            # If the draft exists, delete all players in the draft from the list of currently playing players
            # and then delete the draft mapping. If the draft was in the middle of a round, award players
            # for the games reported.
            try:
                draft = drafts[msgChannel][draftName]
                if draft.gameStarted():
                    outputMsg = 'Draft \"' + draftName + '\" has MANUALLY ended!\nStandings:\n'
                    for player in draft.players.values():
                        chipsEarned = (player.matchesWon * CHIPS_PER_WIN) + (player.matchesLost * CHIPS_PER_LOSS)
                        outputMsg += ('\t' + player.user.name + ': ' + str(player.matchesWon) +
                            '-' + str(player.matchesLost) + ' = ' + str(chipsEarned) + ' chips\n')
                    # Award Players
                    outputMsg += ('Make sure one of the players screenshots this message and posts ' +
                        'in #mod-help so everyone gets their rewards!')
                    await msgChannel.send(outputMsg)
                    for player in draft.players.values():
                        currentPlayers.pop(player.user.id) 
                    drafts[msgChannel].pop(draftName)
                await msgChannel.send('The draft has successfully manually concluded!')
            except KeyError as e:
                await msgChannel.send('Draft \"' +  draftName + 
                    '\" does not exist in this channel. Use !showdrafts to show current drafts.')
        else:
            await msgChannel.send('Only admins or moderators can manually end a draft')
        return
        
    # Kick player from drafts in the message channel they're in.
    # Usage: !draftkick @player
    if '!draftkick' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) != 2 or len(message.mentions) != 1: 
                await msgChannel.send('Command should be used in form \"!kick @player\" ' +
                    'in the channel of the draft from which you want the player removed. ' + 
                    'Use \"!showdrafts to show current drafts\", and \"!showplayers\" to ' +
                    'view player(s) in a given draft')
                return
            player = message.mentions[0]
            
            # If the player is in a draft in the message channel, remove that player from the draft
            try:
                if currentPlayers[player.id]['draftChannel'] == msgChannel:
                    playerDraftName = currentPlayers[player.id]["draftName"]
                    playerDraftChannel = currentPlayers[player.id]["draftChannel"]
                    draft = drafts[playerDraftChannel][playerDraftName]
                    
                    currentPlayers.pop(player.id)
                    draft.kick(player.id)
                    await msgChannel.send('Player ' + player.name +
                        ' has been removed from draft \"' + playerDraftName + '\".')
                else:
                    await msgChannel.send('Player ' + player.name + ' is not in a draft in this channel!')
            except KeyError as e:
                await msgChannel.send('Player ' + player.name + ' is not currently in a draft!')
        else:           
            await msgChannel.send('Only admins or moderators can manually remove players from drafts. ' +
                'If you yourself would like to leave, use \"!leavedraft\".')
        return

    # Lists all cards in user-specified cube file. Cards shown can be filtered optionally
    # based on additional argument
    # Spirits might be bugged
    # Usage: !showcubemetrics cubefile *filter
    #   where filter can be "attr", "type", "level", "tuner", "extra"
    if '!showcubemetrics' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) < 2 or len(splitMsg) > 3:
                await msgChannel.send('Command should be used in form \"!showcube cubefile *filter\", '  +
                    'where filter is optional and can be \"attr\", \"type\", \"level\", \"tuner\", or \"extra\"')
                return
            cubeFile = splitMsg[1]
            
            try:
                CardList = cubes[cubeFile]
                if ('attr' in splitMsg): 
                    asyncio.create_task(msgChannel.send(__createAttributeDictionary(CardList)))
                elif ('type' in splitMsg):
                    asyncio.create_task(msgChannel.send(__createTypeDictionary(CardList)))
                elif ('level' in splitMsg):
                    asyncio.create_task(msgChannel.send(__createLevelDictionary(CardList)))     
                elif ('tuner' in splitMsg):
                    asyncio.create_task(msgChannel.send(__createTunerDictionary(CardList)))
                elif ('extra' in splitMsg):
                    asyncio.create_task(msgChannel.send(__createExtraMessage(CardList)))
                elif len(splitMsg) == 2:
                    asyncio.create_task(msgChannel.send(__createSpreadDictionary(CardList)))
                else:
                    await msgChannel.send('Filter \"' + splitMsg[2] + '\" not found')
            except KeyError as e:
                await msgChannel.send('Cube not found, please enter one from this list next time:\n' + str(list(cubes.keys())))
        else:
            await msgChannel.send('Only admins or moderators can see the cube metrics')
        return
        
    # Extracts all cards in all pools into .ydks for a user-specified draft in message channel, and says who has each card.
    # Could be useful for detecting cheating if necessary
    # Usage: !showpools draftname
    if '!showpools' == splitMsg[0]:
        if not await __allowChannel(message):
            return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) != 2:
                await msgChannel.send('Command should be used in form \"!showpools draftname\" ' +
                    'in the channel of the draft where you want to see all player draft pools. Use ' +
                    '\"!showdrafts\" to show current drafts.')
                return
            draftName = splitMsg[1]
            
            try:
                pooltosend = ''
                draft = drafts[msgChannel][draftName]
                for player in draft.players.values():
                    tempidpoolnoextra = []
                    tempidpoolextra = []
                    tempidpoolside = []
                    overflow_counter = 0
                    for card in player.pool:
                        if ((card.cardType != ('Synchro Monster') or ('Synchro Tuner Monster')) and
                        (card.cardType != 'XYZ Monster') and
                        (card.cardType != 'Fusion Monster')):                
                            tempidpoolnoextra.append(card.id) #puts the ids of the main deck cards in a list
                        elif ('xyz' in card.cardType.lower() or
                        'synchro' in card.cardType.lower() or 
                        'fusion monster' in card.cardType.lower()):
                            #Puts the ids of the extra deck cards in the extra deck if there's room
                            if (overflow_counter < 14):
                                tempidpoolextra.append(card.id) 
                                overflow_counter = overflow_counter + 1
                            #Otherwise store extra deck cards in side deck
                            else: 
                                tempidpoolside.append(card.id) #puts the ids of the extra deck cards in an overflow side list
                                
                    #This whole block formats their cards for the .ydk format
                    ydkName = player.user.name + 'DraftPool.ydk'
                    ydkString = ''
                    ydkstuff = ['#created by ...', '#main']
                    for listitem in ydkstuff: #puts in the necessary ydk stuff
                        ydkString+='%s\n' % listitem
                    for listitem in tempidpoolnoextra:
                        ydkString+=('%s\n' % listitem) #should put main deck cards in the ydk file
                    ydkextraline = ['#extra']
                    for listitem in ydkextraline: #Stuff after this gets put in the extra deck (until side)
                        ydkString+='%s\n' % listitem
                    for listitem in tempidpoolextra:
                        ydkString+='%s\n' % listitem
                    ydksidestuff = ['!side'] #Stuff after this gets put in the side
                    for listitem in ydksidestuff:
                        ydkString+='%s\n' % listitem           
                    for listitem in tempidpoolside:
                        ydkString+='%s\n' % listitem

                    asyncio.create_task(author.send(file = discord.File(fp = StringIO(ydkString),filename = ydkName)))
            except KeyError as e:
                await msgChannel.send('Draft \"' +  draftName + 
                    '\" does not exist in this channel. Use \"!showdrafts\" to show current drafts.')
        else:
            asyncio.create_task(msgChannel.send('Only admins or moderators can view all card pools in a draft'))
        return

    # Undoes a match between two players in message channel. Does not work if last match of game
    # Usage: !matchundo @loser @winner
    if '!matchundo' == splitMsg[0]:
        if not await __allowChannel(message):
                    return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) != 3 or len(message.mentions) != 2: 
                await msgChannel.send('Command should be used in form \"!matchundo @loser @winner\" ' +
                    'in the channel of the match you want to undo. ' + 
                    'Use \"!showdrafts to show current drafts\", and \"!showplayers\" to ' +
                    'view player(s) in a given draft')
                return
            loser = message.mentions[0]
            winner = message.mentions[1]
            if loser.id == winner.id:
                await msgChannel.send('Can\'t undo a match between a user and themself.')
                return
            
            # If both players are in the same draft in the message channel, undo their match
            try:
                loserDraftName = currentPlayers[loser.id]['draftName']
                loserDraftChannel = currentPlayers[loser.id]['draftChannel']
                
                winnerDraftName = currentPlayers[winner.id]['draftName']
                winnerDraftChannel = currentPlayers[winner.id]['draftChannel']
                
                outputMsg = ''
                if loserDraftChannel == msgChannel and winnerDraftChannel == msgChannel:
                    if loserDraftName != winnerDraftName:
                        await msgChannel.send('Players are not in the same draft!')
                        return
                    draft = drafts[loserDraftChannel][loserDraftName]
                    
                    # Check if the undone match was the last match of a round
                    matchesPerRound = math.floor(len(draft.players) / 2)
                    if len(draft.matches[draft.currentRound]) == 2 * matchesPerRound:
                        outputMsg += ('Draft \"' + loserDraftName + '\" has been rewinded back to round ' +
                            str(draft.currentRound) + '.')
                        draft.currentRound -= 1

                    draft.players[loser.id].matchesLost -= 1
                    draft.players[loser.id].matchesPlayed -= 1
                    draft.matches[draft.currentRound].append(loser.id)
                    
                    draft.players[winner.id].matchesWon -= 1
                    draft.players[winner.id].matchesPlayed -= 1
                    draft.matches[draft.currentRound].append(winner.id)
                    
                    outputMsg += 'The match between ' + loser.name + ' and ' + winner.name + ' has been undone.'
                    await msgChannel.send(outputMsg)
                else:
                    if loserDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + loser.name + ' is not in a draft in this channel!')
                    if winnerDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + winner.name + ' is not in a draft in this channel!')
            except (KeyError, ValueError) as e:
                await msgChannel.send('Either ' + loser.name + ' or ' + winner.name + ' is not currently in a draft!')
        else:           
            await msgChannel.send('Only admins or moderators can undo matches in drafts')
        return

    # Manually records a loss between two players in the message channel
    # Usage: !matchmanual @loser @winner
    if '!matchmanual' == splitMsg[0]:
        if not await __allowChannel(message):
                    return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            if len(splitMsg) != 3 or len(message.mentions) != 2: 
                await msgChannel.send('Command should be used in form \"!matchmanual @loser @winner\" ' +
                    'in the channel of the match you want to manually have a player lose in. ' + 
                    'Use \"!showdrafts to show current drafts\", and \"!showplayers\" to ' +
                    'view player(s) in a given draft')
                return
            loser = message.mentions[0]
            winner = message.mentions[1]
            if loser.id == winner.id:
                await msgChannel.send('Can\'t record a match between a user and themself.')
                return
            
            # If both players are in the same draft in the message channel, record loser's loss
            try:
                loserDraftName = currentPlayers[loser.id]['draftName']
                loserDraftChannel = currentPlayers[loser.id]['draftChannel']
                
                winnerDraftName = currentPlayers[winner.id]['draftName']
                winnerDraftChannel = currentPlayers[winner.id]['draftChannel']
                
                if loserDraftChannel == msgChannel and winnerDraftChannel == msgChannel:
                    if loserDraftName != winnerDraftName:
                        await msgChannel.send('Players are not in the same draft!')
                        return
                    draft = drafts[loserDraftChannel][loserDraftName]
                    
                    # Check if the games for the draft have started
                    if not draft.gameStarted():
                        await msgChannel.send('Draft \"' + loserDraftName + '\" has not started its games!')
                        return
                    
                    # Check if the pairing exists in the current round then record the loss
                    if not draft.pairExists(loser.id, winner.id, draft.currentRound):
                        await msgChannel.send(loser.name + ' and ' + winner.name + ' are not paired in \"' +
                            loserDraftName + '\" round ' + str(draft.currentRound))
                        return
                    if not draft.reportLoss(loser.id, winner.id):
                        await msgChannel.send('Either ' + loser.name + ' or ' + winner.name + ' reported a loss this round ' +
                            'already. Consider using \"draftEnd\" if the issue persists.')
                    
                    await msgChannel.send('A manual loss from ' + loser.name + ' to ' + winner.name +
                        ' has been recorded in \"' + loserDraftName + '\".')
                else:
                    if loserDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + loser.name + ' is not in a draft in this channel!')
                    if winnerDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + winner.name + ' is not in a draft in this channel!')
            except (KeyError, ValueError) as e:
                if loser.id not in currentPlayers:
                    await msgChannel.send('Player ' + loser.name + ' is not currently in a draft!')
                elif winner.id not in currentPlayers:
                    await msgChannel.send('Player ' + winner.name + ' is not currently in a draft!')
                else:
                    await msgChannel.send('There was an error MANUALLY reporting a loss: ' + e)
        else:           
            await msgChannel.send('Only admins or moderators can manually record losses between players. ' +
                'If you yourself would like to record a loss, use \"!matchloss\".')
        return

    # Manually record a player as not having shown up for a match in the message channel
    # Based on user input, if the player left, kick them from future games
    # Usage: !matchnoshow afk(y or n) @missingPlayer @activePlayer
    if '!matchnoshow' == splitMsg[0]:
        if not await __allowChannel(message):
                    return
        if 'Admin' in str(author.roles) or 'Moderator' in str(author.roles): 
            usage = ('Command should be used in form \"!matchnoshow afk(y or n) @missingPlayer ' +
                    '@activePlayer\" in the channel of the match you want to manually report a no-show in. ' + 
                    'Use \"!showdrafts to show current drafts\", and \"!showplayers\" to ' +
                    'view player(s) in a given draft')
            
            if len(splitMsg) != 4 or len(message.mentions) != 2: 
                await msgChannel.send(usage)
                return
                
            noShow = message.mentions[0]
            winner = message.mentions[1]
            afk = splitMsg[1]
            
            # Make sure user specified whether or not player left, and the no-show is not from a player
            # to themself
            if afk != 'y' or afk != 'n':
                awaitMsgChannel.send(usage)
            elif noShow.id == winner.id:
                await msgChannel.send('Can\'t record a no-show between a user and themself.')
                return
            
            # If both players are in the same draft in the message channel, record the no-show
            try:
                noShowDraftName = currentPlayers[noShow.id]['draftName']
                noShowDraftChannel = currentPlayers[noShow.id]['draftChannel']
                
                winnerDraftName = currentPlayers[winner.id]['draftName']
                winnerDraftChannel = currentPlayers[winner.id]['draftChannel']
                
                if noShowDraftChannel == msgChannel and winnerDraftChannel == msgChannel:
                    if noShowDraftName != winnerDraftName:
                        await msgChannel.send('Players are not in the same draft!')
                        return
                    draft = drafts[noShowDraftChannel][noShowDraftName]
                    
                    # Check if the games for the draft have started
                    if not draft.gameStarted():
                        await msgChannel.send('Draft \"' + noShowDraftName + '\" has not started its games!')
                        return
                    
                    # Check if the pairing exists in the current round then record the no-show
                    if not draft.pairExists(noShow.id, winner.id, draft.currentRound):
                        await msgChannel.send(noShow.name + ' and ' + winner.name + ' are not paired in \"' +
                            noShowDraftName + '\" round ' + str(draft.currentRound))
                        return
                    if not draft.reportNoShow(noShow.id, winner.id, afk):
                        await msgChannel.send('Either ' + noShow.name + ' or ' + winner.name + ' reported a loss this round ' +
                            'already. Consider using \"draftEnd\" if the issue persists.')
                        return
                    
                    await msgChannel.send('A manual no-show from ' + noShow.name + ' to ' + winner.name +
                        ' has been recorded in \"' + noShowDraftName + '\".')
                else:
                    if noShowDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + noShow.name + ' is not in a draft in this channel!')
                    if winnerDraftChannel != msgChannel:
                        await msgChannel.send('Player ' + winner.name + ' is not in a draft in this channel!')
            except (KeyError, ValueError) as e:
                if noShow.id not in currentPlayers:
                    await msgChannel.send('Player ' + noShow.name + ' is not currently in a draft!')
                elif winner.id not in currentPlayers:
                    await msgChannel.send('Player ' + winner.name + ' is not currently in a draft!')
                else:
                    await msgChannel.send('There was an error MANUALLY reporting a no-show: ' + e)
        else:           
            await msgChannel.send('Only admins or moderators can manually record no-shows between players.')
        return

    #TODO: Low priority. Fix this later.
    # if ('!picklog') in message.content.lower():
    #     if 'Admin' in str(author.roles):
    #         #await author.send(PickLog) 
    #         for thing in PickLog:
    #             logtosend+='%s\n' % thing
    #         asyncio.create_task(author.send(file=discord.File(fp=StringIO(logtosend),filename='PickLog.csv'))) 

    # Anti Merchbot Commands
    if '!join' == splitMsg[0] and message.channel.name in ALLOWED_CHANNELS:
        await msgChannel.send('We do \"!draftjoin\" around these parts, pardner. Check \"!gamehelp\"')
        return
    if '!leave' == splitMsg[0] and message.channel.name in ALLOWED_CHANNELS:
        await msgChannel.send('We do \"!draftleave\" around these parts, partner. Check \"!gamehelp\"')
        return
    if '!q' == splitMsg[0] and message.channel.name in ALLOWED_CHANNELS:
        await msgChannel.send('We do \"!draftshow\" around these parts, gardner. Check \"!gamehelp\"')
        return
    if '!loss' == splitMsg[0] and message.channel.name in ALLOWED_CHANNELS:
        await msgChannel.send('We do \"!matchloss\" around these parts, bartner. \"!undo\" that loss quickly, and check \"!gamehelp\"')
        return

# When bot successfully connects to bot, print all servers it will connect to
@client.event
async def on_ready():
    for guild in client.guilds:
        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

# Run the bot associated with the stored API key, triggering on_ready()
if not key is None and key != '':
    client.run(key)
else:
    print('Key not configured.')

