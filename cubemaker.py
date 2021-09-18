import sys
import json
import os
import os.path
from os import path

# Takes a filepath expected to be newline delimited list of desired cards
def read_card_list(filepath):
    f = open(filepath)
    card_list = f.read().splitlines()
    f.close()
    return card_list

# Takes a filepath expected to be JSON file of "all yugioh cards" and reads them to a dictionary
def read_all_card_list(filepath):
    with open(filepath, "r") as f:
        cardDict = json.load(f)
        f.close()
        return cardDict["data"]

# Read user arguments and processes files as dictionaries/lists
allCards = read_all_card_list(sys.argv[1])
cardList = read_card_list(sys.argv[2])

#These are what we're gonna be exporting
exportCards = []
unidentifiedCards = []

# Tracks rarity of cards if specified
rarity = None
#heart of it
for line in cardList:
    # If a line is found that starts and end with dashes, interpret the line
    # as a rarity to start categorizing cards into
    if line.startswith('-') and line.endswith('-'):
        rarity = line.lstrip('-').rstrip('-')
        continue
    # Otherwise, line is a card
    else:
        # Stores any alt image URLs
        nameComponents = line.split('|')
        match = [card for card in allCards if card['name'].lower() == nameComponents[0].lower().strip()]
        
        # If card name could not be found, list it as unidentified
        if not match:
            print('Could not find card ' + line.strip() + '. Please check spelling.')
            unidentifiedCards.append(line)
        # If card name is found, store it as a matched card (alongside user-specified alt-art and alt card ids)
        else:    
            # NOTE: match could have multiple elements. We only ever expect it to have one.
            matchedCard = match[0]
            imageUrl = ''
            cardId = ''
            # User requested alt-art and alt card ID
            if len(nameComponents) == 3:
                imageUrl = nameComponents[1] if not nameComponents[1].isnumeric() else nameComponents[2]
                cardId = nameComponents[1] if nameComponents[1].isnumeric() else nameComponents[2]
            # User requested either alt-art or alt card ID  
            elif len(nameComponents) == 2:
                imageUrl = nameComponents[1] if not nameComponents[1].isnumeric() else matchedCard['card_images'][0]['image_url']
                cardId = nameComponents[1] if nameComponents[1].isnumeric() else matchedCard['id']
            # User only requested card   
            elif len(nameComponents) == 1:
                imageUrl = matchedCard['card_images'][0]['image_url']
                cardId = matchedCard['id']
            # Malformed card
            else:
                print('Could not find card ' + line.strip() + '. Malformatted input line.')
                unidentifiedCards.append("Malformatted line => " + line)
                continue        
            # Print out the card that was found and successfully interpreted
            print('Name: %s | Id: %s | Type: %s | Image Link: %s \n' % (matchedCard['name'], cardId, matchedCard['type'], imageUrl))
            
            # Store the image URL of the requested card
            matchedCard['card_images'][0]['image_url'] = imageUrl
            # Store the id of the requested card
            matchedCard['id'] = cardId
            # Store the rarity of the card if necessary
            if rarity != None:
                matchedCard['rarity'] = rarity
            exportCards.append(matchedCard)

# The cardList was a set, and should be stored as a .set
if rarity != None and path.exists('list.set'):
    os.remove('list.set')
    setFile = open("list.set", "w")
    with setFile as export_list:
        json.dump(exportCards, export_list)
    setFile.close()
# The cardList was a cube, and should be stored as a .cub
else: 
    if(path.exists('list.cub')):
        os.remove('list.cub')
    cubeFile = open("list.cub", "w")
    with cubeFile as export_list:
        json.dump(Cards, export_list)
    cubeFile.close()
        

# Generate .txt file of missing cards if necessary
if(path.exists('missed_cards.txt')):
    os.remove('missed_cards.txt')

#dump any and all unfound card names to a new text file
if(unidentifiedCards):
    missedCardsFile = open("missed_cards.txt", 'w')
    with missedCardsFile as whoops:
        for missedCard in unidentifiedCards:
            whoops.write(missedCard + '\n')
    missedCardsFile.close()

#Download all card images
import imagemanager
imagemanager.cache_all_images()
