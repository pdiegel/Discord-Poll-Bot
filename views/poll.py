import discord
from discord.ui import Button, View
from helpers.db_funcs import get_poll, get_user_votes, record_vote
from views.delete import ConfirmDeleteModal


class PollView(View):
    def __init__(self, poll_id: int, user_id: int, is_admin: bool = False):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        self.user_id = user_id
        self.is_admin = is_admin
        self.refresh_data()
        user_votes = get_user_votes(poll_id, user_id)
        for option_id, option, _ in self.options:
            style = (
                discord.ButtonStyle.success
                if option_id in user_votes
                else discord.ButtonStyle.primary
            )
            label = f"{option} {'✔️' if option_id in user_votes else ''}"
            button = Button(label=label, style=style)  # type: ignore
            button.callback = self.create_callback(option_id)  # type: ignore
            self.add_item(button)  # type: ignore
        if is_admin:
            delete_button = Button(  # type: ignore
                label="Delete Poll", style=discord.ButtonStyle.danger
            )
            delete_button.callback = self.confirm_delete  # type: ignore
            self.add_item(delete_button)  # type: ignore

    def refresh_data(self):
        question, options = get_poll(self.poll_id)
        self.question = question
        self.options = options
        self.votes = {option_id: votes for option_id, _, votes in options}

    def create_callback(self, option_id: int):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            record_vote(self.poll_id, user_id, option_id)
            self.refresh_data()
            await interaction.response.edit_message(
                content=self.format_poll(),
                view=PollView(self.poll_id, user_id, self.is_admin),
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
