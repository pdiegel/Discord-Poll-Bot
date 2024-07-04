import discord
from discord.ui import Modal, TextInput


class VoteWarningModal(Modal):
    MAX_MESSAGE_CHARACTERS = 45

    def __init__(self, option: str, poll_id: int):
        super().__init__(title="Vote Warning")

        self.label = f"You have already voted for: {option}"
        if len(self.label) > self.MAX_MESSAGE_CHARACTERS:
            self.label = self.label[: self.MAX_MESSAGE_CHARACTERS - 3] + "..."

        self.add_item(
            TextInput(
                label=self.label,
                default="Please choose a different option.",
                required=False,
            )
        )
        self.option = option
        self.poll_id = poll_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Warning: Your vote for '{self.option}' in Poll ID \
'{self.poll_id}' has already been recorded.",
            ephemeral=True,
        )
