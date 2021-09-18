This bot originated from Jack Lee and slindvall's Meta-Repository Draftbot

# How To Use

## Step 1
Create a .txt file containing the names of the cards you want to use in a cube
* If you desire alternative images from the latest version of your card, you'll want to format it like so: Treeborn Frog|https://www.bbtoystore.com/mm5/yugioh/YU_GLD2EN010_496x705.jpg (no spaces, I'm _lazy_.)
* You can also use this same separator to specify alternative card IDs (ex. Monster Reborn|83764718).
* NOTE: There is an error in the database(allcards.json) where the card IDs for cards with multiple artworks is off by one. Some of these will be listed in "updateDatabase/altartcards.txt". If you plan to use these cards, either specify the card ID with "|" or change the stored card ID in allcards.json manually

## Step 2
From your local copy of the repository, run the cubemaker.py script passing allcards.json as the first argument and your desired cube list (one card per line) as the second.
USAGE: python cubemaker.py allcards.json PATH_TO_CUBE_TXT_FILE
ex. if your text file is beta.txt in cubes/cubeTxts, you should run "python cubemaker.py allcards.json cubes/cubeTxts/beta.txt"

Once the script has executed, you should have a shiny new .cub file in the directory called list.cub, which you should move to "cubes/". If any cards could not be found, they will be output in a one card per line list as missed_cards.txt. You'll wanna run the whole thing again once you figure out the spelling/formatting issues of these cards.

## Step 3
Add a discord bot api token to the config.json file. This can be obtained through the [discord developer portal](https://discord.com/developers/). 

## Step 4
Configure the constants in constants.py per your draft specifications

## Step 5
Run bot.py. All cube.cub files should be in "cubes/", and the staple.cub file, if you choose to use it, should be in "cubes/staples/". 

## TODO:
* test cubestats and mypool with fusions
* try making cards picked through messages intead of reacts
* Add rarity-based packs
* make showcubestats include spirit monsters
