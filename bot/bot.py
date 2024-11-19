from utils.data import token
from discord.ext import commands
from discord import Message
from discord import Intents
from challenge import challenge
from play import play_action_card
from game import start_game, reset_game, get_game_code, test
from check import check, map
from preview import preview
from more import claim_line, clear_curse



bot = commands.Bot(intents=Intents.all())

commands = [check, preview, map, challenge, claim_line, play_action_card, clear_curse]
for command in commands:
    bot.add_application_command(command)
    
authorised_starters = [1194359566712979549, 1225001366586523699]

# just check if the game has to start
async def check_start(message:Message):
    if message.author.id not in authorised_starters:
        return
    ####
    if message.content=='!start game' or message.content.startswith("!start game "):
        await message.reply("Entering pre-game phase now...")
        args = message.content.split()[2:]
        await start_game(message.guild,
                         int(args[-1]) if args and args[-1].isnumeric() else 5,
                         rewards=False if 'norewards' in args else True,
                         secrets=False if 'nosecrets' in args else True)
    elif message.content == '!reset game':
        await message.reply("Resetting game now...")
        reset_game(message.guild)
        await message.channel.send("Successfully reset!")
    elif message.content == "!code":
        await message.reply(f"Game code: {get_game_code(message.guild)}")
    elif message.content == "!test":
        await test(message.guild)

bot.add_listener(check_start, 'on_message')


token = token()
bot.run(token)