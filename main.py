import praw
import requests
import re
import json

# pattern looks for the text beween [[double brackets]]
# above would match with 'double brackets'
regexPattern = "\[\[([^]]+)\]\]"
subredditsToStream = ["rzrkyb","bowdenco"]

replyText = """{}

---

This action was performed automatically | [Source](https://github.com/bowdens/flagbot)"""

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
                if len(matches) > 1:
                    # no point searching further...
                    break

    if len(matches) == 1:
        return matches.pop()
    elif len(matches) > 1:
        print("we got multiple matches for {}: {}".format(name, ", ".join(["{} - {}".format(match[0], match[1]) for match in matches])))
        return None
    else:
        return None

def countries_to_tuples(countries):
    # generate the list of codes from the match_country_to_code function
    # filter out the None results
    return set(filter(None, [match_country_to_code(c) for c in countries]))

def submit_reply(me, parentComment, body, debug=True):
    if debug is True:
        print("####replying to comment id {}, body:{} (debug!)####".format(parentComment, body))
    else:
        # first we must check to see if we've already replied to this comment
        parentComment.reply_sort = "old" # assumption here: we have replied early enought to be in the first 10 comments
        parentComment.reply_limit = 10
        parentComment.refresh() # have to do this to get a list of replies
        for comment in parentComment.replies:
            if comment.author.id == me.id:
                print("####was going to reply to comment id {} but i've already replied####".format(parentComment.permalink))
                return False

        print("####\nreplying to comment id {}\nbody:{}\n####".format(parentComment.permalink, body))

        try:
            newComment = parentComment.reply(body)
            print("   made comment with link = {}".format(newComment.permalink))
            return True
        except praw.exceptions.APIException as e:
            print("   failed to make comment: {}".format(e))
            return False

def create_reply(comment, codeCountryTuples):
    replyStrings = []
    for code, country in codeCountryTuples:
        replyStrings.append(flagText.format(country, code))
    replyBody = replyText.format("  \n".join(replyStrings))
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
            submit_reply(reddit.user.me(), comment, create_reply(comment, countryCodeTuples), debug=True)

def main_loop(reddit, subreddits):
    for comment in subreddits.stream.comments():
        countryCodeTuples = countries_to_tuples(matches(comment.body))
        if len(countryCodeTuples) > 0:
            submit_reply(reddit.user.me(), comment, create_reply(comment, countryCodeTuples), debug=False)

def main(debug=True):
    print("---initialising praw---")
    reddit = praw.Reddit("flagbot")
    print("---generating subreddits---")
    subreddits = reddit.subreddit("+".join(subredditsToStream))
    print("   subreddits are: {}".format(", ".join(subredditsToStream)))
    if debug is True:
        print("---starting debug loop---")
        debug_main_loop(reddit, subreddits)
    else:
        print("---starting main loop---")
        main_loop(reddit, subreddits)

if __name__ == "__main__":
    main(debug=False)
