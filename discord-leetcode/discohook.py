import os
import discord
import boto3
from leetscrape import GetQuestion
from discord.ext import commands
from dotenv import load_dotenv
import re
from datetime import date
import discohook

# Load the .env file containing the Discord bot token
load_dotenv()

today = date.today()
d2 = today.strftime("%B %d, %Y")

# Discord bot token
TOKEN = os.getenv('DISCORD_TOKEN')
PUBLIC_KEY = os.environ["PUBLIC_KEY"]
APPLICATION_ID = os.environ["APPLICATION_ID"]
APPLICATION_PASSWORD = os.environ["APPLICATION_PASSWORD"]

app = discohook.Client(
    application_id=APPLICATION_ID,
    public_key=PUBLIC_KEY,
    token=TOKEN,
    password=APPLICATION_PASSWORD,  # Must be provided if you want to use the dashboard.
    default_help_command=True,  # This will enable your bot to use  default help command (/help).
)

# Set the intents for the bot
intents = discord.Intents.default()
intents.message_content = True # Ensure the bot can read messages

# Initialize the bot
bot = commands.Bot(command_prefix='!', intents=intents)
# DynamoDB setup
dynamodb = boto3.client('dynamodb')

# Your DynamoDB table name
TABLE_NAME = 'leetcode-easy-qs'

# Function to get the first unposted item from DynamoDB
def get_unposted_item():
    response = dynamodb.scan(
        TableName=TABLE_NAME,
        FilterExpression='posted = :val',
        ExpressionAttributeValues={':val': {'BOOL': False}},
    )
    items = response.get('Items', [])
    if items:
        return items[0]
    return None

# Function to mark the item as posted in DynamoDB
def mark_as_posted(qid):
    dynamodb.update_item(
        TableName=TABLE_NAME,
        Key={'QID': {'N': str(qid)}},
        UpdateExpression='SET posted = :val',
        ExpressionAttributeValues={':val': {'BOOL': True}}
    )

MAX_MESSAGE_LENGTH = 2000
# AUTO_ARCHIVE_DURATION = 2880

def split_message(message, max_length):
    """Splits a message into chunks without cutting words or splitting in the middle of sentences."""
    parts = []
    while len(message) > max_length:
        # Find the last space or newline within the max_length boundary
        split_at = message.rfind(' ', 0, max_length)
        if split_at == -1:
            # If no space found, find the last newline within the boundary
            split_at = message.rfind('\n', 0, max_length)
        if split_at == -1:
            # If no space or newline found, forcefully split at the max_length boundary
            split_at = max_length
        
        # Add the part to the list
        parts.append(message[:split_at].strip())
        # Continue with the remaining text
        message = message[split_at:].strip()

    # Add any remaining message as the last part
    if message:
        parts.append(message)

    return parts

def clean_message(message):
    """Removes more than 2 consecutive newlines from the message."""
    first_line, _, remaining_message = message.partition('\n')
    return re.sub(r'\n{3,}', '\n', remaining_message)

def extract_first_line(message):
    """Extracts the first line from the message."""
    lines = message.splitlines()
    return lines[0] if lines else ""

# Task that runs on a schedule
@bot.command(name='post')
async def post_message(ctx):
    item = get_unposted_item()

    if item:
        title_slug = item['titleSlug']['S']
        qid = item['QID']['N']
        question = "%s" % (GetQuestion(titleSlug=title_slug).scrape())

        first_line = extract_first_line(question)

        # Clean the message to remove more than 2 consecutive newlines
        cleaned_question = clean_message(question)

        # Check if the message exceeds the 2000 character limit
        parts = split_message(cleaned_question, MAX_MESSAGE_LENGTH)

        message = await ctx.send(f"Leetcode Question of the Day - {d2}")

        # Create a thread to post the long message
        thread = await message.create_thread(
            name=first_line, 
        )
        
        # Send each part of the message in the thread
        for part in parts:
            await thread.send(part)

        await thread.send("Good Luck!!!")

        # Mark the item as posted in DynamoDB
        mark_as_posted(qid)
    else:
        print("No unposted items found.")

@app.load
@discohook.command.slash()
async def ping(i: discohook.Interaction):
    """Ping the bot."""
    await i.response.send("Pong!")

# Adding a error handler for all interactions
@app.on_interaction_error()
async def handler(i: discohook.Interaction, err: Exception):
    user_response = "Some error occurred! Please contact the developer."
    if i.responded:
        await i.response.followup(user_response, ephemeral=True)
    else:
        await i.response.send(user_response, ephemeral=True)

    await app.send("12345678910", f"Error: {err}")  # send error to a channel in development server


# Adding a error handler for any serverside exception
@app.on_error()
async def handler(_request, err: Exception):
    # request: starlette.requests.Request
    # err is the error object
    await app.send("12345678910", f"Error: {err}")  # send error to a channel in development server
    # If you don't have reference to `app` object, you can use `request.app` to get the app object.
# Start the task when the bot is ready

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# Run the bot
bot.run(TOKEN)
