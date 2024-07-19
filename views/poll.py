import discord
from discord.ui import Button, View
from helpers.db_funcs import get_poll, record_vote
from views.delete import ConfirmDeleteModal
from typing import Any, Awaitable, Callable
import asyncio
import logging


class PollView(View):
    def __init__(
        self,
        poll_id: int,
        user_id: int,
    ):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        self.user_id = user_id
        self.buttons_added = False  # To track if buttons have been added
        asyncio.create_task(self.init_poll_view())

    async def init_poll_view(self):
        await self.refresh_data()
        if not self.buttons_added:
            self.add_buttons()
            self.buttons_added = True

    async def refresh_data(self) -> None:
        poll = await get_poll(self.poll_id)
        if poll is None:
            raise ValueError("Poll not found")

        question, options = poll

        self.question = question
        self.options = options
        self.votes = {option_id: votes for option_id, _, votes in options}

    def add_buttons(self) -> None:
        for option_id, option, _ in self.options:
            label = option
            button = Button(  # type: ignore
                label=label,
                style=discord.ButtonStyle.primary,
            )
            button.callback = self.create_callback(option_id)  # type: ignore
            self.add_item(button)  # type: ignore

    def create_callback(
        self, option_id: int
    ) -> Callable[[discord.Interaction], Awaitable[Any]]:

        async def callback(interaction: discord.Interaction) -> None:
            user_id = interaction.user.id

            try:
                await interaction.response.defer()
                await record_vote(self.poll_id, user_id, option_id, True)
                await self.refresh_data()
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,  # type: ignore
                    content=self.format_poll(),
                    view=self,
                )
                logging.info(
                    f"Vote recorded for poll {self.poll_id} by user {user_id}"
                )
            except discord.errors.NotFound:
                logging.warning(
                    f"Interaction {interaction.id} is no longer valid."
                )
                await interaction.followup.send(
                    "Sorry, this interaction is no longer valid.",
                    ephemeral=True,
                )
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                await interaction.followup.send(
                    "An error occurred while processing your vote.",
                    ephemeral=True,
                )

        return callback

    async def confirm_delete(
        self,
        interaction: discord.Interaction,
    ) -> None:
        modal = ConfirmDeleteModal(
            self.poll_id,
            interaction.message.id,  # type: ignore
        )
        try:
            await interaction.response.send_modal(modal)
        except discord.errors.NotFound:
            logging.error(f"Interaction {interaction.id} is no longer valid.")
            await interaction.followup.send(
                "Sorry, this interaction is no longer valid.", ephemeral=True
            )
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            await interaction.followup.send(
                "An error occurred while processing your request.",
                ephemeral=True,
            )

    def format_poll(self) -> str:
        total_votes = self.total_votes
        result = f"**{self.question}**\n\nPoll Results:\n"
        for _, option, votes in self.options:
            plural = "s" if votes != 1 else ""
            percent_of_total_votes = (
                (votes / total_votes) * 100 if total_votes != 0 else 0
            )
            result += f"{option}: {votes} vote{plural} - \
{percent_of_total_votes:.0f}%\n"
        result += f"\nPoll ID: {self.poll_id}"
        return result

    @property
    def total_votes(self) -> int:
        return sum(self.votes.values())
