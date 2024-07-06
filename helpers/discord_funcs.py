import discord


def get_server_id(interaction: discord.Interaction) -> int:
    discord_server = interaction.guild  # type: ignore
    if discord_server is None:
        raise ValueError("This command must be used in a server.")
    return discord_server.id  # type: ignore
