#------------DRAFT SPECIFICATIONS------------
# 0 < PACK_SIZE <=15
PACK_SIZE = 2
# If you do not want to use staples, set STAPLES_CUB to None
# 0 < NUM_STAPLES <= 15
NUM_STAPLES = 9
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
COMMAND_LIST = ['draftcreate', 'draftjoin', 'draftleave', 'showdrafts', 'showplayers', 'mypool', 'myydk', 'matchloss',
                'draftstart', 'draftend', 'draftkick', 'showcubemetrics', 'showpools', 'matchundo', 'matchmanual', 'matchnoshow']
COMMANDS = {
    'draft' : {
        'draftcreate' : {
            'basicDef' : 'Creates a draft from a user-specified .cub file with a user-specified name',
            'complexDef' : ('Usage: !draftcreate cubefile draftname\n' + ' ' * 10 + 
                            'Creates a draft in the message channel from cubefile.cub named draftname, up to ' +
                            MAX_DRAFTS)
        },
        'draftjoin' : {
            'basicDef' : 'Join user-specified draft in the message channel if it exists',
            'complexDef' : ('Usage: !draftjoin draftname (in channel of draft)\n' + ' ' * 9 +
                            'Joins draft draftname in the message channel, trying to fire the cube if the draft now has ' +
                            NUM_PLAYERS + ' players')
        },
        'draftleave' : {
            'basicDef' : 'Leaves any draft in the message channel the user is in',
            'complexDef' : ('Usage: !draftleave\n' + ' ' * 10 +
                            'Leaves any draft in the message channel the user is in that has not started')
        }
    },
    'show' : {
        'showdrafts' : {
            'basicDef' : 'View all drafts in the message channel',
            'complexDef' : ('Usage: !showdrafts\n' + ' ' * 9 +
                            'View all drafts in the message channel and the number of players in each draft')
        },
        'showplayers' : {
            'basicDef' : 'View all players in user-specified draft in the message channel',
            'complexDef' : ('Usage: !showplayers draftname' + ' ' * 10 +
                            'View all players in draftname in the message channel')
        }
    },
    'my' : {
        'mypool' :  {
            'basicDef' : 'Shows the cards drafted by user. Cards shown can be filtered optionally based on additional argument',
            'complexDef' : ('Usage: !mypool *filter\n' + ' ' * 6 +
                            'Show the cards drafted by user, optionally filtered by *filter, ' +
                            'where filter can be \"attr\", \"type\", \"level\", \"tuner\", \"extra\", \"all\"')
        },
        'myydk' : {
            'basicDef' : 'Extracts the cards drafted by user into a .ydk file',
            'complexDef' : ('Usage: !myydk\n' + ' ' * 5 +
                            'Extracts the cards drafted by user into a .ydk file')
        }
    },
    'match' : {
        'matchloss' :{
            'basicDef' : 'Reports a loss to another player',
            'complexDef' : ('Usage: !matchloss @player' + ' ' * 9 +
                            'Reports a loss to @player, ending the draft if the loss was the final match')
        }
    }
}

ADMIN_COMMANDS = {
    'draft' : {
        'draftstart' : {
            'basicDef' : 'Manually fires user-specified draft in the message channel if it exists',
            'complexDef' : ('Usage: !draftstart draftname\n' + ' ' * 10 +
                            'Manually fires draftname in the message channel if it exists')
        },
        'draftend' : {
            'basicDef' : 'Manually concludes user-specified draft in the message channel if it exists',
            'complexDef' : ('Usage: !draftend draftname\n' + ' ' * 8 +
                            'Manually concludes and deletes draftname in the message channel if it exists')
        },
        'draftkick' : {
            'basicDef' : 'Kick player from drafts in the message channel they\'re in',
            'complexDef' : ('Usage: !kick @player\n' + ' ' * 9 +
                            'Kick @player from drafts in the message channel they\'re in')
        }
    },
    'show' : {
        'showcubemetrics' : {
            'basicDef' : 'Lists cards in user-specified .cub file. Cards shown can be filtered optionally based on additional argument',
            'complexDef' : ('Usage: !showcubemetrics cubefile *filter\n' + ' ' * 13 +
                            'Lists all cards in cubefile. Cards shown can be filtered optionally by *filter, ' +
                            'where filter can be \"attr\", \"type\", \"level\", \"tuner\", \"extra\"')
        },
        'showpools' : {
            'basicDef' : 'Extracts all cards in all pools into .ydks for a user-specified draft in message channel if it exists',
            'complexDef' : ('Usage: !showpools draftname\n' + ' ' * 9 +
                            'Extracts all cards in all pools into .ydks (one per player) for draftname')
        }
    },
    'match' : {
        'matchundo' : {
            'basicDef' : 'Undoes a match between two players in the message channel. Does not work if last match of game'
            'complexDef' : ('Usage: !matchundo @loser @winner\n' + ' ' * 9 +
                            'Undoes a match between @loser and @winner if they are in a same draft in the message channel. ' +
                            'Does not work if last match of game')
        },
        'matchmanual' : {
            'basicDef' : 'Manually records a loss between two players in the message channel',
            'complexDef' : ('Usage: !matchmanual @loser @winner\n' + ' ' * 11 +
                            'Manually records a loss from @loser to @winner if they are in the same draft in the message channel')
        },
        'matchnoshow' : {
            'basicDef' : 'Manually record a player as not having shown up for a match in the message channel, kicking them based on additional argument',
            'complexDef' : ('Usage: !matchnoshow afk(can be y or n) @missingPlayer @activePlayer\n' + ' ' * 11 +
            'Manually record @missingPlayer as not having shown up for a match in the message channel, kicking them based on afk')
        }
    }
}