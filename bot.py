import discord
from discord.ext import commands
import dotenv
import os
from views.delete import ConfirmDeleteModal
from views.poll import PollView
from helpers.db_funcs import add_poll, init_db, load_poll_data

dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


intents = discord.Intents.default()
intents.message_content = True  # Ensure the bot can read message content

bot = commands.Bot(command_prefix="/", intents=intents)


init_db()


# Find and load previous polls that contain a Poll ID.
# This is necessary to ensure that the bot can recover from a restart.
# Search through the previous 100 messages in each channel the bot can see.
async def load_previous_polls(bot: commands.Bot) -> None:
    for channel in bot.get_all_channels():
        if not isinstance(channel, discord.TextChannel):
            continue
        async for message in channel.history(limit=100):
            if message.author == bot.user:
                # Check if the message content contains the Poll ID
                if "Poll ID: " in message.content:
                    poll_id = get_poll_id_from_message(message.content)
                    poll_data = load_poll_data(poll_id)
                    # print(f"Loaded poll {poll_data}")
                    if poll_data:
                        view = PollView(poll_data[0], message.author.id)
                        await message.edit(
                            content=view.format_poll(), view=view
                        )


def get_poll_id_from_message(content: str) -> int:
    # Extract the Poll ID from discord message content
    prefix = "Poll ID: "
    start = content.find(prefix) + len(prefix)
    poll_id = content[start:]
    # print(f"Extracted Poll ID {poll_id}")
    return int(poll_id)


async def get_message_from_poll_id(poll_id: int) -> discord.Message | None:
    for channel in bot.get_all_channels():
        if not isinstance(channel, discord.TextChannel):
            continue
        async for message in channel.history(limit=100):
            if message.author == bot.user:
                if "Poll ID: " in message.content:
                    if poll_id == get_poll_id_from_message(message.content):
                        return message
    return None


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}!")
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")
    await load_previous_polls(bot)


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

    poll_id = add_poll(question, options_list)
    view = PollView(poll_id, interaction.user.id)  # type: ignore
    await interaction.followup.send(f"**{question}**", view=view)


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

    modal = ConfirmDeleteModal(poll_id, message)  # type: ignore

    await interaction.response.send_modal(modal)


# Error handling
@bot.event
async def on_command_error(ctx, error) -> None:  # type: ignore
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore commands that are not found
    else:
        raise error  # other errors to be handled by the default handler


bot.run(BOT_TOKEN)
