import discord
import json
import random
import boto3
from botocore.exceptions import ClientError
import requests
import os

# Discord bot token
# TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# LeetCode API URL
LEETCODE_API_URL = 'https://leetcode.com/api/problems/algorithms/'

# AWS DynamoDB table name
DYNAMODB_TABLE = 'PostedQuestions'

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

# Function to check if a question has already been posted
def is_question_posted(question_id):
    try:
        response = table.get_item(Key={'question_id': str(question_id)})
        return 'Item' in response  # True if item exists
    except ClientError as e:
        print(f"Error checking DynamoDB: {e}")
        return False

# Function to mark a question as posted
def mark_question_as_posted(question_id):
    try:
        table.put_item(Item={'question_id': str(question_id)})
    except ClientError as e:
        print(f"Error saving to DynamoDB: {e}")

# Fetch all LeetCode easy questions from the API
def fetch_easy_questions():
    response = requests.get(LEETCODE_API_URL)
    data = response.json()

    easy_questions = [
        question for question in data['stat_status_pairs']
        if question['difficulty']['level'] == 1  # Level 1 is "easy"
    ]

    return easy_questions

# Get a random LeetCode easy question that hasn't been posted
def get_random_unposted_question():
    easy_questions = fetch_easy_questions()

    unposted_questions = [
        question for question in easy_questions
        if not is_question_posted(question['stat']['frontend_question_id'])
    ]

    if not unposted_questions:
        # If all questions have been posted, reset or repost from the entire list
        return random.choice(easy_questions)

    return random.choice(unposted_questions)

# Post the LeetCode question to a specific Discord channel
async def post_question(channel):
    question = get_random_unposted_question()

    question_id = question['stat']['frontend_question_id']
    title = question['stat']['question__title']
    url = f"https://leetcode.com/problems/{question['stat']['question__title_slug']}/"

    # Mark question as posted in DynamoDB
    mark_question_as_posted(question_id)

    # Send the question to the Discord channel
    await channel.send(f"LeetCode Easy Question: {title}\n{url}")

# Initialize Discord client
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# Event handler for when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Command to post a LeetCode question
@client.event
async def on_message(message):
    if message.content.startswith('!leetcode'):
        await post_question(message.channel)

# Run the Discord bot
client.run(TOKEN)
