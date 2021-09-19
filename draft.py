import asyncio
import random
import discord
import imagemanipulator
import math
import constants

#------------CONSTANTS------------


# Draft specifications
NUM_PACKS = constants.NUM_PACKS
PACK_SIZE = constants.PACK_SIZE
NUM_STAPLES = constants.NUM_STAPLES
STAPLES_USED = constants.STAPLES_USED
NUM_PLAYERS = constants.PLAYERS_PER_DRAFT
CHIPS_PER_WIN = constants.CHIPS_PER_WIN
CHIPS_PER_LOSS = constants.CHIPS_PER_LOSS

# Loot Table for card rewards
LOOT_TABLE = constants.LOOT_TABLE

reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣', '🇦', '🇧','🇨','🇩','🇪']

#Starting with a list that will hold pick data
pickdata = [['Name', 'Pick', 'User', 'Cube']]

shadow = 'spoilers/shadow.png'
gem = 'spoilers/gem.png'

#Stores their pool of picked cards and discord user. Store within drafts.
class Player:

    # draft: Draft player is currently in. Draft class
    # pack: Contents of pack player is currently drafting
    # pool: Cards player has drafted
    # missedpicks: Number of picks player has missed (max 3)    
    # user: Player information. Discord.member class
    # matchesWon: matches won by player
    # matchesLost: matches lost by player
    def __init__(self, user, draft):
        self.draft = draft
        self.pack = []
        self.pool = []
        self.missedpicks = 0
        self.user = user
        self.matchesPlayed = 0
        self.matchesWon = 0
        self.matchesLost = 0

    # Equality defined by comparing Player's user (class Discord.member)
    # NOTE: Python 2 Users will have to override not equal (__neq__)
    def __eq__(self, other):
        if isinstance(other, Player):
            return self.user == other.user
        return NotImplemented
    
    #String representation of player defined by Discord.member
    def __repr__(self):
        return self.user

    def hasPicked(self):
        return not (len(self.pack) + self.draft.currentPick == self.draft.packSize + 1)

    def pick(self, cardIndex):
        #Checking if the card is in the pack.
        if cardIndex <= (len(self.pack) - 1):
            #Making sure they havent already picked
            if not self.hasPicked():
                asyncio.create_task(self.user.send('You have picked ' + self.pack[cardIndex].name + '.'))
                self.pool.append(self.pack[cardIndex])
                
                temppickdata = []
                tempcardname = str(self.pack[cardIndex].name) #Adding the card name to the temppickdata vector to append to file

                self.pack.pop(cardIndex)
                self.draft.checkPacks()

                tempcardname = tempcardname.replace(',', " ") #Removing commas for CSV purposes
                temppickdata.append(tempcardname)
                temppickdata.append(len(self.pack)) #Adding pick #
                temppickdata.append(self.user) #Adding the person who picked
                temppickdata.append('x') #Noting which cube was used. Will add once I get this working
                pickdata.append(temppickdata)
  
# Timer for ready checking and drafting
class Timer:

    # length: how long the timer should last
    # draft: the draft the timer is associated with, or None if timer is for ready checking
    # expired: indicates whether timer has reached its end
    def __init__(self, draft = None, length = 150):
        self.length = length
        self.draft = draft
        self.expired = False
        asyncio.create_task(self.start())

    async def start(self):
        # Ready check timer
        if self.draft == None:
            self.expired = False
            await asyncio.sleep(self.length)
            self.expired = True
        
        # Draft timer
        else:
            #Scales the length of the timer to the pick number.
            #Mathematica:
            #In: NSolve[{a*Log[10, b*5] == 150, a*Log[10, b*19] == 30}, {a, b}]
            #Out: {{a -> -206.974, b -> 0.0376965}}
            #Pick + 4
            self.expired = False
            numPicks = self.draft.currentPick
            if numPicks < 0:
              numPicks = 6
            newLength = -206.974 * math.log10(0.0476965 * (numPicks + 3))
            self.length = round(newLength)
            #A little bit of psych here. Tell them there is shorter left to pick than there really is.
            await asyncio.sleep(self.length - 12)
            #Return if this thread is now a outdated and no longer needed timer.
            if self != self.draft.timer:
                return
            for player in self.draft.players.values():
                if not player.hasPicked():
                    asyncio.create_task(player.user.send('Hurry! Only ten seconds left to pick!'))
            await asyncio.sleep(12)
            self.expired = True
            if self != self.draft.timer:
                return
            players = [player for player in self.draft.players.values() if not player.hasPicked()]
            for player in players:
                if not player.hasPicked() and self == self.draft.timer:
                    player.missedpicks = player.missedpicks + 1
                    if player.missedpicks == 2:
                        asyncio.create_task(player.user.send('Ran out of time. WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! WARNING! IF YOU MISS ONE MORE PICK YOU WILL BE KICKED FROM THE DRAFT! https://tenor.com/view/wandavision-wanda-this-will-be-warning-gif-20683220'))
                    if player.missedpicks == 3:
                        asyncio.create_task(player.user.send('Ran out of time. You have been kicked for missing 3 picks. Three strikes! you\'re out! https://tenor.com/view/strike-ponche-bateador-strike-out-swing-gif-15388719'))
                        asyncio.create_task(self.draft.channel.send('You\'re way too slow at picking.. Maybe these\'ll help?', file = discord.File(open(shadow, 'rb'))))
                        asyncio.create_task(self.draft.channel.send('Player ' + player.user.name + ' has missed 3 picks and has been kicked!'))
                        self.draft.kick(player.user.id)

                    else:
                        asyncio.create_task(player.user.send('Ran out of time. You have automatically picked the first card in the pack. Please pay attention to avoid wasting time!'))
                        player.pick(0)

class Draft:
    # name: The name of the draft
    # cardPool: The cardPool the pool was created from
    # pool: The cards remaining to be picked from. Sets do not have pools
    # numPacks: number of packs to open
    # packSize: mumber of cards in each pack
    # mode: whether cardPool is set or cube
    # players: The players in the draft. Player class.
    # channel: The channel the draft was started from
    # timer: The timer tracking the picks. Reassign every pick.
    # currentPick: How many cards have been picked from the current pack. -1
    #   indicates draft has not started
    # currentPack: How many packs have been opened for drafting
    # packsOpened: Whether all numPacks packs have been drafted
    # currentRound: Which round of matches is currently being played
    # matches: Matches to be played, generated at end of draft
    #   Maps: round number->matches
    def __init__(self, name, cardPool, channel, staples = None):
        self.name = name
        if isinstance(cardPool, dict):
            self.cardPool = cardPool.copy()
            self.mode = 'set'
            self.numPacks = 5
            self.packSize = 9
        elif isinstance(cardPool, list):
            self.cardPool = cardPool[:]
            self.pool = cardPool[:]
            self.mode = 'cube'
            self.numPacks = NUM_PACKS
            self.packSize = PACK_SIZE
        else:
            raise Exception('Attempted to initialize Draft object with cardPool that was not a list or dictionary')
        
        if staples != None:
            self.staples = staples[:]
        else:
            self.staples = None
        self.players = {}
        self.channel = channel
        self.timer = None
        self.currentPick = -1
        self.currentPack = 0
        self.packsOpened = False
        self.currentRound = 0
        self.matches = {}
    
    # Send a message to the draft channel about the matches in a given round. Also processes bye rounds
    def __printRound(self, roundNumber):
        matchups = self.matches[roundNumber]
        outputMsg = 'Matches for round ' + str(roundNumber) + ':\n'
        for match in range(math.floor(len(matchups) / 2)):
            playerOneID = matchups[2 * match]
            playerTwoID = matchups[2 * match + 1]
            
            # If a player is in a bye round, output that they have a bye and mark the other player as having
            # played. If both players are marked as afk, pretend the round doesn't exist
            if playerOneID == -1 or playerTwoID == -1:
                if playerOneID == -1 and playerTwoID != -1:
                    outputMsg += '\t' + self.players[playerTwoID].user.mention + ' has a bye this round!\n'
                    self.players[playerTwoID].matchesPlayed += 1
                elif playerTwoID == -1 and playerOneID != -1:
                    outputMsg += '\t' + self.players[playerOneID].user.mention + ' has a bye this round!\n'
                    self.players[playerOneID].matchesPlayed += 1
                self.matches[roundNumber].remove(playerOneID)
                self.matches[roundNumber].remove(playerTwoID)
            # Otherwise output the match
            else:
                outputMsg += ('\t' +  self.players[playerOneID].user.mention + ' vs ' +
                    self.players[playerTwoID].user.mention + '\n')
        asyncio.create_task(self.channel.send(outputMsg))
    
    # Returns the minimum roll from random numRolls rolls (from 0 to 47)
    def __roll(self, numRolls):
        minRoll = 48
        for i in range(numRolls):
            minRoll = min(random.randint(0, 47), minRoll)
        if minRoll == 3:
            asyncio.create_task(self.channel.send(file = discord.File(open(gem, 'rb'))))
        return minRoll
    
    # Checks if two specified players are paired against each other in a given round
    # Implicitly checks if game has started, as self.matches is empty if game has not started
    def pairExists(self, playerOneID, playerTwoID, roundNumber):
        try:
            playerOneIndex = self.matches[roundNumber].index(playerOneID)
            playerTwoIndex = self.matches[roundNumber].index(playerTwoID)
            if math.floor(playerOneIndex / 2) == math.floor(playerTwoIndex / 2):
                return True
            else:
                return False
        except (KeyError, ValueError) as e:
            return False
            
    # Reports a loss from one player to another, removing their pairing in the current round
    # and recording whether each player won or lost. Does nothing if either player already
    # reported in the current round.
    
    # Should use pairExists() prior to verify the match exists
    # Caller should catch KeyError, ValueError
    def reportLoss(self, loserID, winnerID):
        try:
            loser = self.players[loserID]
            winner = self.players[winnerID]
            
            
            # Check if either player has reported already
            if ((not loser.matchesPlayed < self.currentRound) or
                (not winner.matchesPlayed < self.currentRound)):
                return False
            
            # Remove the pairing from the current round
            self.matches[self.currentRound].remove(loserID)
            self.matches[self.currentRound].remove(winnerID)
            
            # Record who won and who lost
            loser.matchesLost += 1
            winner.matchesWon += 1
            loser.matchesPlayed += 1
            winner.matchesPlayed += 1
            
            # Check if reported match was last match in a round
            self.checkMatches()
            return True
        except (KeyError, ValueError) as e:
            return e
            
    # Reports a no-show from one player to another, removing their pairing in the current round
    # and recording the match without a winner or a loser. Does nothing if either player already
    # reported in the current round.
    # If the player is marked as permanently afk, kick them from the draft
    
    # Should use pairExists() prior to verify the match exists
    # Caller should catch KeyError, ValueError
    def reportNoShow(self, noShowID, winnerID, afk):
        try:
            noShow = self.players[noShowID]
            winner = self.players[winnerID]
            
            
            # Check if either player has reported already
            if ((not noShow.matchesPlayed < self.currentRound) or
                (not winner.matchesPlayed < self.currentRound)):
                return False
            
            # Remove the pairing from the current round
            self.matches[self.currentRound].remove(noShowID)
            self.matches[self.currentRound].remove(winnerID)
            
            # Record who played without a winner or loser
            noShow.matchesPlayed += 1
            winner.matchesPlayed += 1
            
            # Make sure the afk marker is "y" or "n"
            if afk == 'y':
                self.kick(noShowID)
            elif afk == 'n':
                # Check if reported no-show match was last match in a round
                self.checkMatches()
            else:
                return False
            return True
        except (KeyError, ValueError) as e:
            return e
        
            
    # Decides if its time to move to the next round
    def checkMatches(self):
        # If there are no matches left in the current round, move to the next round
        # or end the game if there are no more rounds
        if len(self.matches[self.currentRound]) == 0:
            try:
                self.currentRound += 1
                self.__printRound(self.currentRound)
            except KeyError as e:
                # Maybe add tiebreaker functionality?
                outputMsg = 'Draft \"' + self.name + '\" has ended!\nStandings:\n'
                for player in self.players.values():
                    chipsEarned = (player.matchesWon * CHIPS_PER_WIN) + (player.matchesLost * CHIPS_PER_LOSS)
                    outputMsg += ('\t' + player.user.name + ': ' + str(player.matchesWon) +
                        '-' + str(player.matchesLost) + ' = ' + str(chipsEarned) + ' chips')
                    if player.matchesWon > 0:
                        loot = self.__roll(player.matchesWon)
                        if loot < 20:
                            outputMsg += ' ~~and ' + LOOT_TABLE[loot] + '~~'
                        else:
                            outputMsg += ' ~~and 5 dust~~'
                    outputMsg += '\n'    
                outputMsg += ('Make sure one of the players screenshots this message and posts ' +
                    'in #mod-help so everyone gets their rewards!')
                asyncio.create_task(self.channel.send(outputMsg))
    
    # Check if draft has started based on currentPick
    def draftStarted(self):
        return self.currentPick != -1
    
    # Check if games have started based on currentRound
    def gameStarted(self):
        return self.currentRound != 0
    
    # Assigns new packs of packSize to each player
    def openPacks(self):
        self.currentPick = 1
        self.currentPack += 1
        self.timer = Timer(draft = self) # resets the timer
        reversedPlayers = {}
        for playerID in reversed(self.players):
            reversedPlayers[playerID] = self.players[playerID]
        self.players.clear()
        self.players = reversedPlayers
        
        if self.mode == 'set':
            numCommons = 0
            numRares = 0
            numSupers = 0
            numUltras = 0
            numSecrets = 0
            
            if 'COMMON' in self.cardPool.keys():
                numCommons = len(self.cardPool['COMMON'])
            if 'RARE' in self.cardPool.keys():
                numRares = len(self.cardPool['RARE'])
            if 'SUPER' in self.cardPool.keys():
                numSupers = len(self.cardPool['SUPER'])
            if 'ULTRA' in self.cardPool.keys():
                numUltras = len(self.cardPool['ULTRA'])
            if 'SECRET' in self.cardPool.keys():
                numSecrets = len(self.cardPool['SECRET'])
            
            
            for player in self.players.values():
                pack = []
                # Randomly pick some number of commons
                # Make sure duplicate commons aren't pulled
                commonsPulled = []
                if numCommons > 6:
                    while len(commonsPulled) < 7:
                        randomCommon = random.randrange(0, numCommons)
                        if randomCommon not in commonsPulled:
                            commonsPulled.append(randomCommon)
                            pack.append(self.cardPool['COMMON'][randomCommon])
                else:
                    raise Exception('Attempted to draft commons from set with < 7 commons')
                    
                
                # Randomly pick a rare
                pack.append(self.cardPool['RARE'][random.randrange(0, numRares)])
                
                # Randomly pick a card from the pool of supers, ultras, and secrets
                randomHolo = random.randrange(0, numSupers + numUltras + numSecrets)
                
                # If a super was pulled
                if randomHolo < numSupers:
                    superIndex = randomHolo
                    holoCard = self.cardPool['SUPER'][superIndex]
                # If an ultra was pulled
                elif randomHolo < numSupers + numUltras:
                    ultraIndex = randomHolo - numSupers
                    holoCard = self.cardPool['ULTRA'][ultraIndex]
                # If a secret was pulled
                else:
                    secretIndex = randomHolo - numSupers - numUltras
                    holoCard = self.cardPool['SECRET'][secretIndex]
                pack.append(holoCard)
                
                player.pack = pack
                # Splice reactions into pack
                packWithReactions = [a + ': ' + b.name for a, b in zip(reactions, pack)] 
                asyncio.create_task(send_pack_message("Here's your #" + str(self.currentPack) +
                    " pack! React to select a card. Happy drafting!\n"+str(packWithReactions), player, pack))
        else:
            FullList = random.sample(self.pool, len(self.players) * self.packSize)
            self.pool = [q for q in self.pool if q not in FullList] # Removes the cards from the full card list

            # Tracks cards from full list already given to a player in a pack
            i = 0
            for player in self.players.values():
                pack = sortPack(FullList[i:i+self.packSize])
                player.pack = pack #Holds the packs
                # Move onto the next pack of cards for the next player
                i = i + self.packSize
                # Splices reactions into pack
                packWithReactions = [a + ': ' + b.name for a, b in zip(reactions, pack)] 
                asyncio.create_task(send_pack_message("Here's your #" + str(self.currentPack) +
                    " pack! React to select a card. Happy drafting!\n"+str(packWithReactions), player, pack))

    # Rotates existing packs among players
    def rotatePacks(self):
        self.currentPick += 1
        self.timer = Timer(draft = self) #resets the timer

        # Creates a list of all the packs
        packs = [player.pack for player in self.players.values()]
        for player in self.players.values():
            # Gives the player the next pack in the list. If that would be out of bounds give them the first pack.
            player.pack = packs[0] if (packs.index(player.pack) + 1) >= len(packs) else packs[packs.index(player.pack) + 1]
            # Splices reactions into pack
            packWithReactions = [a + ': ' + b.name for a, b in zip(reactions, player.pack)] 
            asyncio.create_task(send_pack_message('Your next pack: \n\n' +
                str(packWithReactions), player, player.pack))
            
    # Assigns staple pack from "staples.cub" to each player
    def openStaplePack(self):
        self.timer = Timer(draft = self) #resets the timer

        # List of NUM_STAPLES staples to pick from
        stapleList = self.staples.copy()
        
        #Give each player a new staple pack
        for player in self.players.values():
            pack = sortPack(stapleList[i:i+NUM_STAPLES])
            player.pack = pack #Holds the packs
            # splices reactions into pack
            packWithReactions = [a + ': ' + b.name for a, b in zip(reactions, pack)] 
            asyncio.create_task(send_pack_message("Pick your staple (1 of 3)!\n" +
                str(packWithReactions), player, pack))
    
    # Redisplays staple pack to each player after they picked a staple
    def updateStaplePack(self):
        self.currentPick += 1
        self.timer = Timer(draft = self) #resets the timer
         
        # Displays to each player their staples and prompts them to pick one
        for player in self.players.values():
            packWithReactions = [a + ': ' + b.name for a, b in zip(reactions, player.pack)] 
            asyncio.create_task(send_pack_message("Pick your staple (" +
                str(self.currentPick - self.packSize + len(self.staples)) +
                " of 3)!\n" + str(packWithReactions), player, player.pack))
        if self.currentPick == (STAPLES_USED + self.packSize - len(self.staples)):
            self.currentPack += 1
    
    # Decides if its time to rotate or send a new pack yet.
    def checkPacks(self):
        # Checks if every player has picked.
        if len([player for player in self.players.values() if not player.hasPicked()]) == 0:
            # If numPacks packs have not been opened for each player, rotate the packs among players if
            # there are cards available. If not, open a new pack.
            if (self.currentPack <= self.numPacks and self.currentPick < self.packSize and
                not self.packsOpened):
                self.rotatePacks()
            elif self.currentPack < self.numPacks:
                self.openPacks()
            # If numPacks have been opened and staples are allowed,
            # have each player pick NUM_STAPLES cards from the staples pool.
            elif self.currentPack == self.numPacks and self.staples != None and self.mode == 'cube':
                self.packsOpened = True
                if self.currentPick == self.packSize:
                    # Set currentPick to allow player.hasPicked() to pass with a pack that is not packSize
                    self.currentPick = self.packSize - len(self.staples) + 1
                    self.openStaplePack()
                else:
                    self.updateStaplePack()
            # If numPacks have been opened and NUM_STAPLES have been selected, draft has concluded.
            else:
                for player in self.players.values():
                    asyncio.create_task(player.user.send('The draft is now finished. ' + 
                    'Use !myydk or !mypool to get started on deckbuilding.'))
                    
                  
                # Round-Robin matchmaking, "Circle Method" algorithm with index 0 as the anchor
                # For n players:
                # If n is even, there will be n - 1 rounds
                rotation = list(self.players.keys())
                numPlayers = len(self.players)
                # Skip if < 2 players available
                if numPlayers > 1:  
                    if numPlayers % 2 == 0:
                        numRounds = numPlayers - 1
                    # If n is odd, there will be n rounds
                    else:
                        # Byes are represented by an extra round, shown as a "Ghost index" (-1)
                        # for when there are an odd number of players
                        numRounds = numPlayers
                        rotation.append(-1)

                    # Number of "players" that are rotated around. If n is even, numIndices = numPlayers
                    # if n is odd, numIndices = numPlayers + 1
                    numIndices = numRounds + 1

                    rotatorIndices =  range(2, numIndices)
                    for rounds in range(numRounds):
                        self.matches[rounds + 1] = []
                        # Pair the "players" into matches
                        for index in range(math.floor(numIndices / 2)):
                            self.matches[rounds + 1].append(rotation[0 + index])
                            self.matches[rounds + 1].append(rotation[numRounds - index])

                        # rotate the players for next round
                        # first index is anchor and is not rotated
                        tempIndex = rotation[1]
                        for index in rotatorIndices:
                            rotation[index - 1] = rotation[index]
                        rotation[numRounds] = tempIndex
                    self.currentRound = 1
                    self.__printRound(self.currentRound)
                    self.checkMatches()
    
    # Start the draft
    def startDraft(self):
        self.openPacks()

    # Remove player from dictionary of players in the draft and existing games
    def kick(self, playerID):
        #A little worried about how we currently call this from the seperate timer thread from all the other main logic.
        #Drops the players pack into the void currently. 
        self.players.pop(playerID)
        
        # Remove the player from scheduled matches and noshow them 
        if self.gameStarted():
            for pairings in self.matches.values():
                # Replace the kicked player's id in a round with -1 if they were paired in that round
                try:
                    index = pairings.index(playerID)
                    pairings[index] = -1
                except ValueError as e:
                    continue
            # Print the pairings for the round against
            asyncio.create_task(self.channel.send('If you have already reported your match this round, ' +
                'or are currently in a previously scheduled match, please continue as though nothing changed.'))
            self.__printRound(self.currentRound)
            self.checkMatches()
        # Continue the draft as though the player just picked
        elif self.draftStarted():
            self.checkPacks()

def sortPack(pack):
    monsters = [card for card in pack if 'monster' in card.cardType.lower() and
        ('synchro' not in card.cardType.lower() and 'xyz' not in card.cardType.lower())]
    spells = [card for card in pack if 'spell' in card.cardType.lower()]
    traps = [card for card in pack if 'trap' in card.cardType.lower()]
    extras = [card for card in pack if 'xyz' in card.cardType.lower() or 'synchro' in card.cardType.lower()]
    return monsters + spells + traps + extras

async def add_reactions(message, emojis):
    for emoji in emojis:
        asyncio.create_task(message.add_reaction(emoji))

#This exists to allow making the pack messages async.
async def send_pack_message(text, player, pack):  
    asyncio.create_task(add_reactions(await player.user.send(content=text, file=discord.File(fp=imagemanipulator.create_pack_image(pack),
         filename="image.jpg")), reactions[:len(pack)]))
