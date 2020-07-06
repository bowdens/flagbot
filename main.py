import praw
import requests
import re
import json

# pattern looks for the text beween [[double brackets]]
# above would match with 'double brackets'
regexPattern = "\[\[([^]]+)\]\]"
subredditsToStream = ["vexillology"]

replyText = """
    {}

    ---

    This action was performed automatically | [Source](https://github.com/bowdens/flagbot)
"""
flagText = "[Flag of {}](https://www.example.com/flag/{}.png)"

with open("countries.json") as f:
    flagData = json.load(f)

def match_country_to_code(name):
    matches = set()
    for countryData in flagData:
        code = countryData["cca2"]
        if code.upper() == name.upper():
            # clear the list and add this name, break out of the loop
            matches = [(code, countryData["name"]["common"])]
            break

        # if it doesn't match exactly the code, we'll compile a list of potential names from the json
        potentialNames = [countryData["name"]["common"], countryData["name"]["official"]]
        for language in countryData["name"]["native"]:
            potentialNames.append(countryData["name"]["native"][language]["official"])
            potentialNames.append(countryData["name"]["native"][language]["common"])
        for language in countryData["translations"]:
            potentialNames.append(countryData["translations"][language]["official"])
            potentialNames.append(countryData["translations"][language]["common"])

        # we have a list of potential names, we'll check through them
        for potentialName in potentialNames:
            if potentialName.lower().startswith(name.lower()):
                matches.add((code, countryData["name"]["common"]))

    if len(matches) == 1:
        return matches.pop()
    else:
        print("we got multiple matches for {}:".format(name))
        for match in matches:
            print("  {} - {}".format(match[0], match[1]))
        return None

def countries_to_tuples(countries):
    # generate the list of codes from the match_country_to_code function
    # filter out the None results
    return set(filter(None, [match_country_to_code(c) for c in countries]))

def submit_reply(parentComment, body, debug=True):
    if debug is True:
        print("####\nreplying to comment id {}\nbody:{}\n####".format(parentComment, body))
    else:
        raise Exception("production comments not implemented yet!")

def create_reply(comment, codeCountryTuples):
    replyStrings = []
    for code, country in codeCountryTuples:
        replyStrings.append(flagText.format(country, code))
    replyBody = replyText.format("\n  ".join(replyStrings))
    return replyBody

def matches(text):
    return re.findall(regexPattern, text)

def debug_main_loop(reddit, subreddits):
    for comment in ["""
        [[country a]], [[United Kingdom]], [[australia]], [[aust]], [[NZ]]
    """, """
        hello there i want to see the flag for the [[uk]]
    """, """
        no flags here...
    """]:
        countryCodeTuples = countries_to_tuples(matches(comment))
        if len(countryCodeTuples) > 0:
            submit_reply(comment, create_reply(comment, countryCodeTuples), debug=True)

def main_loop(reddit, subreddits):
    for comment in subreddits.stream.comments():
        countryCodeTuples = countries_to_tuples(matches(comment.body))
        if len(countryCodeTuples) > 0:
            submit_reply(create_reply(comment, countryCodeTuples), debug=False)

def main(debug=True):
    reddit = praw.Reddit("flagbot")
    subreddits = reddit.subreddit("+".join(subredditsToStream))
    if debug is True:
        debug_main_loop(reddit, subreddits)
    else:
        main_loop(reddit, subreddits)

if __name__ == "__main__":
    main()
