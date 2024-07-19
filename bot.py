import discord
from discord.ext import commands
from constants import BOT_TOKEN
from views.delete import ConfirmDeleteModal
from views.poll import PollView
from helpers.db_funcs import add_poll, load_poll_data, connect_db
from helpers.discord_funcs import get_server_id
import logging
import os

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Heroku includes a 'DYNO' environment variable.
if "DYNO" in os.environ:
    import sys

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)


intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content

bot = commands.Bot(command_prefix="/", intents=intents)


# Find and load previous polls that contain a Poll ID.
# This is necessary to ensure that the bot can recover from a restart.
# Search through the previous 100 messages in each channel the bot can see.
async def load_previous_polls(bot: commands.Bot) -> None:
    for channel in bot.get_all_channels():
        if not isinstance(channel, discord.TextChannel):
            continue
        try:
            async for message in channel.history(limit=100):
                if message.author == bot.user:
                    # Check if the message content contains the Poll ID
                    if "Poll ID: " in message.content:
                        poll_id = get_poll_id_from_message(message.content)
                        poll_data = await load_poll_data(poll_id)
                        if poll_data:
                            logger.info(
                                f"Loaded poll {poll_id} in channel \
{channel.name}"
                            )
                            view = PollView(poll_data[0], message.author.id)
                            await view.init_poll_view()  # Ensure initialization
                            await message.edit(
                                content=view.format_poll(), view=view
                            )
        except discord.Forbidden:
            logging.error(
                f"Permission error while accessing channel {channel.name}"
            )
        except Exception as e:
            logging.error(
                f"Error loading previous polls in channel {channel.name}: {e}"
            )


def get_poll_id_from_message(content: str) -> int:
    # Extract the Poll ID from discord message content
    prefix = "Poll ID: "
    start = content.find(prefix) + len(prefix)
    poll_id = content[start:]
    logging.debug(f"Extracted Poll ID {poll_id}")
    return int(poll_id)


async def get_message_from_poll_id(poll_id: int) -> discord.Message | None:
    for channel in bot.get_all_channels():
        if not isinstance(channel, discord.TextChannel):
            continue
        async for message in channel.history(limit=100):
            if message.author == bot.user:
                if "Poll ID: " in message.content:
                    if poll_id == get_poll_id_from_message(message.content):
                        logging.debug(
                            f"Found message for Poll ID {poll_id}: \
{message.content}"
                        )
                        return message
    return None


@bot.event
async def on_ready() -> None:
    logging.info(f"Logged in as {bot.user}!")
    try:
        await connect_db()
        logging.info("Connected to database successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
    try:
        await bot.tree.sync()
        logging.info("Slash commands synced successfully.")
    except Exception as e:
        logging.error(f"Failed to sync slash commands: {e}")

    await load_previous_polls(bot)
    logging.info("Loaded previous polls successfully.")


@bot.tree.command(name="createpoll")  # type: ignore
async def create_poll(
    interaction: discord.Interaction, question: str, options: str
) -> None:
    options_list = [
        opt.strip() for opt in options.split(",") if opt.strip() != ""
    ]
    if len(options_list) < 2:
        await interaction.response.send_message(
            "You need at least two options to create a poll.", ephemeral=True
        )
        return

    # Give the bot more time to respond to the interaction
    await interaction.response.defer()

    discord_server_id = get_server_id(interaction)
    try:
        poll_id = await add_poll(question, options_list, discord_server_id)
        if poll_id is None:
            logging.error("Failed to create poll")
            raise ValueError("Failed to create poll")
        view = PollView(poll_id, interaction.user.id)
        await view.init_poll_view()  # Ensure initialization completes
        await interaction.followup.send(
            f"**{question}** Poll ID: {poll_id}", view=view
        )
    except discord.Forbidden:
        if interaction.guild:
            logging.error(
                f"Permission error while creating poll in guild \
{interaction.guild.name}"
            )
        await interaction.followup.send(
            "I don't have permission to create a poll in this channel.",
            ephemeral=True,
        )
    except Exception as e:
        if interaction.guild:
            logging.error(
                f"Error creating poll in guild {interaction.guild.name}: {e}"
            )
        await interaction.followup.send(
            "An error occurred while creating the poll.",
            ephemeral=True,
        )


@bot.tree.command(name="deletepoll")  # type: ignore
async def delete_poll(
    interaction: discord.Interaction,
    poll_id: int,
) -> None:
    is_admin = interaction.user.guild_permissions.administrator  # type: ignore

    if not is_admin:
        await interaction.response.send_message(
            "You must be an administrator to delete a poll.", ephemeral=True
        )
        return

    message = await get_message_from_poll_id(poll_id)

    if message is None:
        await interaction.response.send_message(
            "Poll not found or already deleted.", ephemeral=True
        )
        return

    try:
        modal = ConfirmDeleteModal(poll_id, message)  # type: ignore
        await interaction.response.send_modal(modal)
    except discord.Forbidden:
        if interaction.guild:
            logging.error(
                f"Permission error while deleting poll in guild \
{interaction.guild.name}"
            )
        await interaction.followup.send(
            "I don't have permission to delete this poll.",
            ephemeral=True,
        )
    except Exception as e:
        if interaction.guild:
            logging.error(
                f"Error deleting poll in guild {interaction.guild.name}: {e}"
            )
        await interaction.followup.send(
            "An error occurred while deleting the poll.",
            ephemeral=True,
        )


# Error handling
@bot.event
async def on_command_error(ctx, error) -> None:  # type: ignore
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore commands that are not found
    else:
        logging.error(f"An error occurred: {error}")
        raise error  # other errors to be handled by the default handler


bot.run(BOT_TOKEN)
