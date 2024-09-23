import json

# File path to the JSON data
input_file_path = "questions_data.json"
output_file_path = "filtered_questions.json"

# Set filtering parameters
min_ac_rate = 50.0  # Only include questions with acRate greater than or equal to 50%
exclude_paid_only = True  # Exclude paid-only questions

# Step 1: Open and load the JSON data from the file
with open(input_file_path, 'r') as file:
    data = json.load(file)

# Step 2: Filter out questions based on difficulty, paidOnly, and acRate
filtered_questions = [
    question for question in data["data"]["problemsetQuestionList"]["questions"]
    if question["difficulty"] == "Easy"  # Include "Easy" difficulty only
    and (not question["paidOnly"] if exclude_paid_only else True)  # Exclude paid-only if enabled
]

# Step 3: Update the original structure with filtered questions
data["data"]["problemsetQuestionList"]["questions"] = filtered_questions

# Step 4: Save the filtered data to a new JSON file
with open(output_file_path, 'w') as outfile:
    json.dump(data, outfile, indent=4)

print(f"Filtered questions saved to {output_file_path}")
