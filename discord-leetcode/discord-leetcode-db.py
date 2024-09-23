import os
import discord
import boto3
from leetscrape import GetQuestion
from discord.ext import tasks
from dotenv import load_dotenv
import re

# Load the .env file containing the Discord bot token
load_dotenv()

# Discord bot token
TOKEN = os.getenv('DISCORD_TOKEN')

# Set the intents for the bot
intents = discord.Intents.default()
intents.message_content = True # Ensure the bot can read messages

# Initialize the bot
bot = discord.Client(intents=intents)
# DynamoDB setup
dynamodb = boto3.client('dynamodb')

# Your DynamoDB table name
TABLE_NAME = 'leetcode-easy-qs'

# Channel ID where the bot should post
CHANNEL_ID = 1267163856359129177  # Replace with the actual channel ID

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
AUTO_ARCHIVE_DURATION = 2880

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
@tasks.loop(minutes=2)  # Set the interval as needed, 1440
async def scheduled_task():
    channel = bot.get_channel(CHANNEL_ID)
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

        # Create a thread to post the long message
        thread = await channel.create_thread(
            name=first_line, 
            type=discord.ChannelType.public_thread
        )
        
        # Send each part of the message in the thread
        for part in parts:
            await thread.send(part)

        # Mark the item as posted in DynamoDB
        mark_as_posted(qid)
    else:
        print("No unposted items found.")


# Start the task when the bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    scheduled_task.start()

@bot.event
async def on_thread_create(thread):
    await thread.send("\nYour challenge starts here! Good Luck!")

# Run the bot
bot.run(TOKEN)
