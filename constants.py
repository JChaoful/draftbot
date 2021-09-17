#------------DRAFT SPECIFICATIONS------------
# 0 < PACK_SIZE <=15
PACK_SIZE = 2
# If you do not want to use staples, set STAPLES_CUB to None
# 0 < NUM_STAPLES <= 15
NUM_STAPLES = 8
# 0 < STAPLES_USED <= 15
STAPLES_USED = 3
# 0 < NUM_PACKS
NUM_PACKS = 1

# Draft Rewards
CHIPS_PER_WIN = 5
CHIPS_PER_LOSS = 3

# If cube file is used, file must in /staples folder
# Set to None if no staples are to be used
# Make sure to update NUM_STAPLES in draft.py according
# to number of staples in provided file
#STAPLES_CUB = 'staples.cub'
STAPLES_CUB = None

# Draft creation limitations
# 1 < NUM_PLAYERS
NUM_PLAYERS = 4
ALLOWED_CHANNELS = ['draft', 'general']
MAX_DRAFTS = 4

# 15 < IGNORED_REACTION. Reactions are mapped from 1-15 based
# on PACK_SIZE, so the ignored value must be greater than those
# values
IGNORED_REACTION = 100

reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣', '🇦', '🇧','🇨','🇩','🇪']


#------------Card Characteristics------------
attributes = ['DARK', 'DIVINE', 'EARTH', 'FIRE', 'LIGHT', 'WATER', 'WIND'] 
levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
monsterTypes = ['Aqua', 'Beast', 'Beast-Warrior', 'Cyberse', 'Dinosaur', 'Divine-Beast', 'Dragon', 'Fairy', 'Fiend', 'Fish', 'Insect',
'Machine', 'Plant', 'Psychic', 'Pyro', 'Reptile', 'Rock', 'Sea Serpent', 'Spellcaster', 'Thunder', 'Warrior', 'Winged Beast', 'Wyrm', 'Zombie']
cardTypes = ['Normal Monster', 'Gemini Monster', 'Effect Monster', 'Tuner Monster', 'Spell', 'Trap', 'Fusion','Synchro', 'XYZ']

#------------!Help Constants------------
COMMAND_LIST = {
    'draftcreate' : 'draft',
    'draftjoin' : 'draft',
    'draftleave' : 'draft',
    'showdrafts' : 'show',
    'showplayers' : 'show',
    'mypool' : 'my',
    'myydk' : 'my',
    'matchloss' : 'match',
    'gamehelp' : 'game',
    'draftstart' : 'draft',
    'draftend' : 'draft',
    'draftkick' : 'draft',
    'showcubemetrics' : 'show',
    'showpools' : 'show',
    'matchundo' : 'match',
    'matchmanual' : 'match',
    'matchnoshow' : 'match'}

COMMAND_GUIDES = ['rules', 'startguide', 'cubeguide']

ADMIN_COMMAND_GUIDES = ['adminguide']

COMMANDS = {
    'draft' : {
        'classDescription': 'Commands that create and delete drafts, or modify the players inside them',
        'draftcreate' : {
            'basicDef' : 'Creates a draft from a user-specified .cub file with a user-specified name',
            'complexDef' : ('[Usage: !draftcreate cubefile draftname]\n' + ' ' * 14 + 
                            'Creates a draft in the message channel from cubefile.cub named draftname, up to ' +
                            str(MAX_DRAFTS))
        },
        'draftjoin' : {
            'basicDef' : 'Join user-specified draft in the message channel if it exists',
            'complexDef' : ('[Usage: !draftjoin draftname (in channel of draft)]\n' + ' ' * 13 +
                            'Joins draft draftname in the message channel, trying to fire the cube if the draft now has ' +
                            str(NUM_PLAYERS) + ' players')
        },
        'draftleave' : {
            'basicDef' : 'Leaves any draft in the message channel the user is in',
            'complexDef' : ('[Usage: !draftleave]\n' + ' ' * 14 +
                            'Leaves any draft in the message channel the user is in that has not started')
        }
    },
    'show' : {
        'classDescription': 'Commands that display aggregate information',
        'showdrafts' : {
            'basicDef' : 'View all drafts in the message channel',
            'complexDef' : ('[Usage: !showdrafts]\n' + ' ' * 13 +
                            'View all drafts in the message channel and the number of players in each draft')
        },
        'showplayers' : {
            'basicDef' : 'View all players in user-specified draft in the message channel',
            'complexDef' : ('[Usage: !showplayers draftname]\n' + ' ' * 14 +
                            'View all players in draftname in the message channel')
        }
    },
    'my' : {
        'classDescription': 'Commands that display information about their user',
        'mypool' :  {
            'basicDef' : 'Shows the cards drafted by user. Cards shown can be filtered optionally based on additional argument',
            'complexDef' : ('[Usage: !mypool \*filter]\n' + ' ' * 10 +
                            'Show the cards drafted by user, optionally filtered by \*filter, ' +
                            'where filter can be \"attr\", \"type\", \"level\", \"tuner\", \"extra\", \"all\"')
        },
        'myydk' : {
            'basicDef' : 'Extracts the cards drafted by user into a .ydk file',
            'complexDef' : ('[Usage: !myydk]\n' + ' ' * 9 +
                            'Extracts the cards drafted by user into a .ydk file')
        }
    },
    'match' : {
        'classDescription': 'Commands that record matches',
        'matchloss' :{
            'basicDef' : 'Reports a loss to another player',
            'complexDef' : ('[Usage: !matchloss @player]\n' + ' ' * 13 +
                            'Reports a loss to @player, ending the draft if the loss was the final match')
        }
    },
    'game' : {
        'classDescription': 'Commands that inform you about draft',
        'gamehelp' :{
            'basicDef' : 'Provides user information based on arguments.',
            'complexDef' : ('[Usage: !gamehelp \*filter]\n' + ' ' * 12 +
                            'If \*filter is empty, show all commands and their basic descriptions.\n' + ' ' * 12 +
                            'If \*filter is a command class, shows all commands categorized under that class and their '+
                            'detailed descriptions\n' + ' ' * 12 +
                            'If \*filter is a command, shows the command\'s detailed description\n' + ' ' * 12 +
                            'If \*filter is a guide, show the guide\'s contents')
        }
    }
}

ADMIN_COMMANDS = {
    'draft' : {
        'draftstart' : {
            'basicDef' : 'Manually fires user-specified draft in the message channel if it exists',
            'complexDef' : ('[Usage: !draftstart draftname]\n' + ' ' * 14 +
                            'Manually fires draftname in the message channel if it exists')
        },
        'draftend' : {
            'basicDef' : 'Manually concludes user-specified draft in the message channel if it exists',
            'complexDef' : ('[Usage: !draftend draftname]\n' + ' ' * 12 +
                            'Manually concludes and deletes draftname in the message channel if it exists')
        },
        'draftkick' : {
            'basicDef' : 'Kick player from drafts in the message channel they\'re in',
            'complexDef' : ('[Usage: !kick @player]\n' + ' ' * 13 +
                            'Kick @player from drafts in the message channel they\'re in. If the player ' +
                            'was in the middle of a draft, removes all cards in the pack they were drafting from ' +
                            'the draft pool.')
        }
    },
    'show' : {
        'showcubemetrics' : {
            'basicDef' : 'Lists cards in user-specified .cub file. Cards shown can be filtered optionally based on additional argument',
            'complexDef' : ('[Usage: !showcubemetrics cubefile \*filter]\n' + ' ' * 17 +
                            'Lists all cards in cubefile. Cards shown can be filtered optionally by \*filter, ' +
                            'where filter can be \"attr\", \"type\", \"level\", \"tuner\", \"extra\"')
        },
        'showpools' : {
            'basicDef' : 'Extracts all cards in all pools into .ydks for a user-specified draft in message channel if it exists',
            'complexDef' : ('[Usage: !showpools draftname]\n' + ' ' * 13 +
                            'Extracts all cards in all pools into .ydks (one per player) for draftname. Can use to manually verify '+
                            'if a player used cards they did not draft')
        }
    },
    'match' : {
        'matchundo' : {
            'basicDef' : 'Undoes a match between two players in the message channel. Does not work if last match of game',
            'complexDef' : ('[Usage: !matchundo @loser @winner]\n' + ' ' * 13 +
                            'Undoes a match between @loser and @winner if they are in a same draft in the message channel. ' +
                            'Does not work if last match of game. Inverse of \"!matchmanual\".')
        },
        'matchmanual' : {
            'basicDef' : 'Manually records a loss between two players in the message channel',
            'complexDef' : ('[Usage: !matchmanual @loser @winner]\n' + ' ' * 15 +
                            'Manually records a loss from @loser to @winner if they are in the same draft in the message channel.' +
                            'Inverse of \"!matchmanual\".')
        },
        'matchnoshow' : {
            'basicDef' : 'Manually record a player as not having shown up for a match in the message channel, kicking them based on additional argument',
            'complexDef' : ('[Usage: !matchnoshow afk(*can be y or n*) @missingPlayer @activePlayer]\n' + ' ' * 15 +
            'Manually record @missingPlayer as not having shown up for a match in the message channel, kicking them based on afk')
        }
    }
}

RULES_GUIDE = ('```css\n[RULES GUIDE]```\n' +
                'Each of the ' + str(NUM_PLAYERS) + ' players gets ' + str(NUM_PACKS) + ' ' + str(PACK_SIZE) + 
                '-card pack(s) from a pool of ~160 cards (that has duplicates of some cards).\n' +
                '\t1) Each player opens 1 of their packs\n' + '\t2) Each player takes 1 card from their pack\n' +
                '\t3) The players pass the pack between themselves in a circle, taking turns picking 1 card from ' +
                'their packs, until all ' + str(NUM_PACKS) + ' packs have been picked clean\n\n' +
                'At the end, players also have a pool of ' + str(NUM_STAPLES) + ' staples from which they can choose ' + 
                str(STAPLES_USED) +' cards from to add to their decks.\n\n' +
                'Each person ends up with a pool of ' + str((PACK_SIZE * NUM_PACKS) + STAPLES_USED) + ' cards (' +
                str(PACK_SIZE * NUM_PACKS) + ' cards drafted + ' + str(STAPLES_USED) + ' staples), '
                'that they will construct a 30-card deck from.\n\n' +
                'The gameplay rules used will be:\n' +
                '\t1) \"forged 4 format\" rules, besides the 30-card decks\n' +
                '\t2) \"forged 4 format\" rulings, as dictated in #rulings\n' +
                '\t3) Best-of-1 games\n\n'+
                'The entry fee is 50 dust. Players earn 5 chips per win and 3 chips per loss. Players who ' +
                'play all their matches will also ' +
                ' recieve a drop from a loot table. More wins means a higher chance at better loot. ' +
                'See \"gamehelp loot\" for more information.')
                
START_GUIDE = ('```css\n[START GUIDE]```\n' +
                'Welcome to Draft! Make sure to read the rules guide (\"!gamehelp rules\") before continuing to read this guide!\n\n' +
                'To get a draft running, either use \"!createdraft\" to create a new draft or \"!joindraft\" to join an existing draft' +
                '(\"!showdrafts\" will show you the drafts you can join). ' +
                'Once the draft fills up, all players will be DMd to check whether they are afk. If everyone\'s ready, then the draft will ' +
                'begin!\n\n' +
                'During and after the draft, feel free to use \"!mypool\" to see the cards you\'ve drafted. There are some filters you can ' +
                'use to change how your card pool is displayed (refer to \"!gamehelp mypool\").\n\n' +
                'When the draft ends, use !myydk to get a file containing the cards you drafted. This can be imported into duelingbook ' +
                'with the \"Import Deck\" button in the deck building screen, near the top of the bottom-left menu. At this point, please compare ' +
                'the cards imported in duelingbook with the cards shown in \"!mypool\" and make sure they match. ' +
                'There are known issues importing cards with multiple artworks (ex. Mystic Tomato, Dark Magician, Blue-Eyes White Dragon).\n\n' +
                'During the games, report losses with \"!matchloss\". Make sure someone screenshots the tournament final results in ' +
                '#mod-help so everyone gets rewarded.\n\n' +
                'If you want to learn more about the cube contents, check \"!gamehelp cubeguide\". If you have questions, refer to \"!gamehelp\" ' +
                'and never be afraid to ask a mod for help!')
                
CUBE_GUIDE = ('```css\n[CUBE GUIDE]```\n' +
                'Check pinned for cube contents, dummy\n' +
                '\t\"beta.cub\" has 179 cards: 103 monsters, 40 spells, 36 traps')
              
ADMIN_GUIDE = ('```css\n[ADMINS GUIDE]```\n' +
                '\"!gamehelp command\" should be informative enough for the admin commands, so this guide will mostly note differences ' +
                'compared to Merchbot commands.\n\n' + '\t1)\"!matchmanual\" and \"matchnoshow\" are used with the loser/noshow player argument ' +
                'passed in before the winner, unlike !manual, which has the winning player first. \"matchnoshow\" also has another argument ' +
                'indicating whether the noshow player will be afk for the remainder of the draft.\n'+
                '\t2)\"matchundo\" can reverse games beyond the scope of the \"last reported game\". You should be able to use combinations of ' +
                '\"!matchmanual\" and \"!matchundo\" to set a draft to any game in any round for a given draft.\n'+
                '\t3)\"!showpools\" main use is to manually deck check players suspected of cheating with their draft pools')
                