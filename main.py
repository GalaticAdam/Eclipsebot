from src.imports import *

print("--------System Info Fetched--------")
try:
    # Run screenfetch and filter out ASCII art
    result = subprocess.run("screenfetch -p", shell=True, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():  # If screenfetch fails, fallback to neofetch
        print("screenfetch failed, trying neofetch")
        raise Exception("screenfetch failed")
except:  # If screenfetch fails, run neofetch
    print("running neofetch")
    result = subprocess.run("neofetch", shell=True, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():  # If neofetch also fails
        print("Failed to fetch system info.")

# Print the output with color codes preserved
print(result.stdout, end="")

print("--------Importing Commands--------")
from src.CommandImports import *


print("--------Starting--------")

load_dotenv("data/config/config.env")

TOKEN = os.getenv("TOKEN")
try:
    print("loaded token: " + TOKEN)
except Exception as e:
    print("token is invalid, please check and try again")
    exit()

if TOKEN == None:
    print("token is invalid, please check and try again")
    exit()
    
@bot.event
async def on_ready():
    print("Bot name set to: " + bot.user.name)
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        #logger.error(f"Error in on_ready(): {e}")
        print(e)
 
    print("--------Started Bot--------")


@bot.event
async def on_member_join(member):
    print(f"New member joined: {member.name}")
    channel = bot.get_channel(1562246278794973194)
    if channel:
        await channel.send(f"Welcome {member.mention} to the server!")



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



@bot.event
async def on_member_remove(member):
    print(f"Member left: {member.name}")
    channel = bot.get_channel(1572829812974813254)
    if channel:
        ranint = random.randint(1, 3)
        if ranint == 1:
            await channel.send(f"{member.mention} Has FUCKING left the GOD DAMN SERVER.")
        elif ranint == 2:
            await channel.send(f"{member.mention} Has quietly left the server.")
        elif ranint == 3:
            ranint = random.randint(1, 3)
            if ranint == 1:
                message = leave_message.format(
                    member=member,
                    name=member.name,
                    mention=member.mention                                                          
                )

                await send_long_message(channel, message)
            elif ranint == 2:
                await channel.send(f"{member.mention} Has dramatically left the server.")
            elif ranint == 3:
                await channel.send(f"{member.mention} Has vanished without a trace.")
        else:
            await channel.send(f"{member.mention} Has left the server.")
@bot.event
async def on_message(message):
    # Keep the ticket create channel clean, but never delete the bot's panel message
    if not message.author.bot:
        raw = os.getenv("Ticket_channel")
        if raw and str(raw).strip():
            try:
                if message.channel.id == int(raw):
                    await message.delete()
            except (ValueError, discord.HTTPException):
                pass
    await bot.process_commands(message)



if __name__ == "__main__":
    bot.run(TOKEN)