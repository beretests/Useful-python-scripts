import csv
import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')

def filter_and_format_csv_for_dynamodb(input_csv):
    result = []
    
    with open(input_csv, mode='r') as file:
        csv_reader = csv.DictReader(file)
        
        for row in csv_reader:
            # Filter based on difficulty and paidOnly fields
            if row['difficulty'] == 'Easy' and row['paidOnly'] == 'False':
                # Prepare the formatted data for DynamoDB
                item = {
                    'QID': {'N': str(row['QID'])},  # QID is a number, so use 'N' type for DynamoDB
                    'titleSlug': {'S': row['titleSlug']},  # String type for titleSlug
                    'topicTags': {'S': row['topicTags']},  # Storing topicTags as a single string
                    'categorySlug': {'S': row['categorySlug']},  # String type for categorySlug
                    'posted': {'BOOL': False}  # New attribute 'posted' set to False
                }
                result.append(item)
    
    return result

def upload_to_dynamodb(items, table_name):
    table = dynamodb.Table(table_name)
    
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item={
                    'QID': int(item['QID']['N']),  # Convert QID back to int for DynamoDB
                    'titleSlug': item['titleSlug']['S'],
                    'topicTags': item['topicTags']['S'],
                    'categorySlug': item['categorySlug']['S'],
                    'posted': item['posted']['BOOL']
                })
        print(f"Data uploaded successfully to {table_name}")
    
    except (BotoCoreError, ClientError) as error:
        print(f"Error uploading data to DynamoDB: {error}")

def create_table():
    try:
        table = dynamodb.create_table(
            TableName='leetcode-easy-qs',
            KeySchema=[
                {
                    'AttributeName': 'QID',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'QID',
                    'AttributeType': 'N'  # Number type
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait until the table exists
        table.meta.client.get_waiter('table_exists').wait(TableName='leetcode-easy-qs')
        print(f"Table {table.table_name} created successfully!")
    
    except Exception as e:
        print(f"Error creating table: {e}")

# Call function to create the table
create_table()

# Example usage
input_csv = 'getql.pyquestions.csv'  # Your input CSV file
table_name = 'leetcode-easy-qs'      # DynamoDB table name

# Step 1: Filter and format the CSV data
questions = filter_and_format_csv_for_dynamodb(input_csv)

# Step 2: Upload data to DynamoDB
upload_to_dynamodb(questions, table_name)
