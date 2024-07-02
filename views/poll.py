import discord
from discord.ui import Button, View
from helpers.db_funcs import get_poll, record_vote
from views.delete import ConfirmDeleteModal
from views.vote_warning_modal import VoteWarningModal


class PollView(View):
    def __init__(self, poll_id: int, user_id: int):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        self.user_id = user_id
        self.refresh_data()
        for option_id, option, _ in self.options:
            label = option
            button = Button(  # type: ignore
                label=label,
                style=discord.ButtonStyle.primary,  # type: ignore
            )
            button.callback = self.create_callback(option_id)  # type: ignore
            self.add_item(button)  # type: ignore

    def refresh_data(self):
        question, options = get_poll(self.poll_id)
        self.question = question
        self.options = options
        self.votes = {option_id: votes for option_id, _, votes in options}

    def create_callback(self, option_id: int):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id

            vote_was_recorded = record_vote(self.poll_id, user_id, option_id)
            if not vote_was_recorded:
                modal = VoteWarningModal(self.options[option_id], self.poll_id)
                await interaction.response.send_modal(modal)
                return
            self.refresh_data()
            await interaction.response.edit_message(
                content=self.format_poll(),
                view=PollView(self.poll_id, user_id),
            )

        return callback

    async def confirm_delete(self, interaction: discord.Interaction):
        modal = ConfirmDeleteModal(
            self.poll_id,
            interaction.message.id,  # type: ignore
        )
        await interaction.response.send_modal(modal)

    def format_poll(self):
        total_votes = self.total_votes
        result = f"**{self.question}**\n\nPoll Results:\n"
        for _, option, votes in self.options:
            percent_of_total_votes = (
                (votes / total_votes) * 100 if total_votes != 0 else 0
            )
            result += (
                f"{option}: {votes} votes - {percent_of_total_votes:.0f}%\n"
            )
        result += f"\nPoll ID: {self.poll_id}"
        return result

    @property
    def total_votes(self) -> int:
        return sum(self.votes.values())
