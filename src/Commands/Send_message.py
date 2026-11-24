from src.imports import *
from src.globals import *

async def send_long_message(channel, message):
    max_length = 2000
    chunks = []
    current_chunk = ""

    for paragraph in message.split("\n"):
        # If an individual paragraph exceeds the limit
        while len(paragraph) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.append(paragraph[:max_length])
            paragraph = paragraph[max_length:]

        # Check whether adding this paragraph exceeds the limit
        if len(current_chunk) + len(paragraph) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n" + paragraph
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await channel.send(chunk)


@bot.tree.command(name="send_message", description="Send a message to a specified channel")
async def send_message(interaction: discord.Interaction, channel: discord.TextChannel, message: str):3
    await send_long_message(channel, message)
    await interaction.response.send_message(f"Message sent to {channel.mention}", ephemeral=True)