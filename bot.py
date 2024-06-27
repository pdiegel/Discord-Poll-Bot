import discord
from discord.ext import commands
import dotenv
import os
from views.poll import PollView
from helpers.db_funcs import add_poll, init_db

dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content

bot = commands.Bot(command_prefix="/", intents=intents)


init_db()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")


@bot.tree.command(name="createpoll")  # type: ignore
async def create_poll(
    interaction: discord.Interaction, question: str, options: str
):
    options_list = [opt.strip() for opt in options.split(",")]
    if len(options_list) < 2:
        await interaction.response.send_message(
            "You need at least two options to create a poll.", ephemeral=True
        )
        return

    poll_id = add_poll(question, options_list)
    is_admin = interaction.user.guild_permissions.administrator  # type: ignore
    view = PollView(poll_id, interaction.user.id, is_admin)  # type: ignore
    await interaction.response.send_message(f"**{question}**", view=view)


bot.run(BOT_TOKEN)
