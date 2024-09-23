from leetscrape import GetQuestionsList

ls = GetQuestionsList()
ls.scrape() # Scrape the list of questions
ls.questions.head() # Get the list of questions
ls.to_csv(directory="/home/beretests/github-projects/Useful-python-scripts/getql.py")