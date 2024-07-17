import discord
from helpers.db_funcs import delete_poll
from helpers.discord_funcs import get_server_id
from discord.ui import Modal, TextInput


class ConfirmDeleteModal(Modal):
    def __init__(self, poll_id: int, message: discord.Message):
        super().__init__(title="Confirm Delete Poll")
        self.poll_id = poll_id
        self.poll_message = message
        self.add_item(TextInput(label="Type 'DELETE' to confirm"))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.children[0].value.upper().strip() == "DELETE":  # type: ignore

            try:
                discord_server_id = get_server_id(interaction)
            except ValueError:
                await interaction.response.send_message(
                    "This command must be used in a server.", ephemeral=True
                )
                return

            try:
                await delete_poll(self.poll_id, discord_server_id)
            except ValueError:
                await interaction.response.send_message(
                    "Unable to Delete Poll: Poll not found.", ephemeral=True
                )
                return

            await self.poll_message.delete()
            await interaction.response.send_message(
                content=f"Poll {self.poll_id} has been deleted.",
                ephemeral=True,
            )

        else:
            await interaction.response.send_message(
                "Deletion canceled.", ephemeral=True
            )
