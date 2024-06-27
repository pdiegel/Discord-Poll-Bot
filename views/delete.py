import discord
from helpers.db_funcs import delete_poll
from discord.ui import Modal, TextInput


class ConfirmDeleteModal(Modal):
    def __init__(self, poll_id: int, message_id: int | None):
        super().__init__(title="Confirm Delete Poll")
        self.poll_id = poll_id
        self.message_id = message_id
        self.add_item(TextInput(label="Type 'DELETE' to confirm"))

    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value == "DELETE":  # type: ignore
            delete_poll(self.poll_id)
            await interaction.response.edit_message(
                content="Poll has been deleted.",
                view=None,
            )
        else:
            await interaction.response.send_message(
                "Deletion canceled.", ephemeral=True
            )
