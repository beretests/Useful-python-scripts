from leetscrape import GetQuestion

# Get the question body
question = "%s" % (GetQuestion(titleSlug="count-pairs-of-similar-strings").scrape())
# str = "%s" % (question)
print(question)