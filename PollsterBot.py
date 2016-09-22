__author__ = 'm.stanford'
import praw
import requests
import json
import os
from Daemon import Daemon
import sys, time
import random

# Reddit https://praw.readthedocs.io/en/stable/pages/comment_parsing.html
reddit = praw.Reddit(user_agent='Pollster')
reddit.login('pollster_bot', '1QA2WS3ed', disable_warning=True)
default_sub = 'Pollster_Bot'
bot_name = 'pollster_bot'
version = '0.3b'

# Huffington post http://elections.huffingtonpost.com/pollster/api
uri = 'http://elections.huffingtonpost.com/pollster/api/charts.json'


# Returns a dictionary of states.
def load_json_file(filename):
    fn = os.path.join(os.path.dirname(__file__), filename)
    with open(fn) as data_file:
        return json.load(data_file)


# Set states
states = {}
states = load_json_file('data/states.json')

# phrases
phrases = load_json_file('data/phrases.json')
greetings = phrases['greeting']
winning = phrases['winning']
losing = phrases['losing']

# keywords to call the pollster bot
keywords = load_json_file('data/keywords.json')['keywords']


def get_greeting():
    return random.choice(greetings)


def get_winning(winner, points):
    return random.choice(winning).format(winner, points)


def get_losing(loser, points):
    return random.choice(losing).format(loser, points)


# Gets all submissions in the subreddit as a generator.
def get_submissions(subreddit=default_sub, submission_limit=25):
    donald_submissions = reddit.get_subreddit(subreddit).get_hot(limit=submission_limit)
    return donald_submissions


def get_comments(submission, comment_limit=25):
    submission.replace_more_comments(limit=comment_limit, threshold=0)
    return submission.comments


def get_flat_comments(submission, comment_limit=25):
    submission.replace_more_comments(limit=comment_limit, threshold=0)
    return praw.helpers.flatten_tree(submission.comments)


# Gets polls from state, defaults to 2016-president race
def get_poll_huffington(state, page=1, topic='2016-president'):
    poll_params = {'page': page, 'state': state, 'topic': topic}
    my_response = requests.get(uri, params=poll_params)
    if my_response.ok:
        polling_data = []
        entry_data = {}
        json_response = my_response.json()
        for entry in json_response:
            entry_data['title'] = entry['title']
            entry_data['state'] = entry['state']
            entry_data['url'] = entry['url']
            entry_data['last_updated'] = entry['last_updated']
            entry_data['estimates'] = []
            for estimate in entry['estimates']:
                estimate_data = {}
                estimate_data['choice'] = estimate['choice']
                estimate_data['value'] = estimate['value']
                estimate_data['party'] = estimate['party']
                entry_data['estimates'].append(estimate_data)
            polling_data.append(entry_data)
    return polling_data


# Returns a list of states abbreviations.
def check_comment_for_dictionary_keys_and_values(comment, dictionary=states):
    comment_string = comment.body
    matches = []
    abbrevs = []
    # Check full names
    for x in dictionary.keys():
        if x in comment_string and x not in matches:
            matches.append(x)

    for x in dictionary.values():
        if x in comment_string and x not in matches:
            matches.append(x)

    # Return Abbrevs
    for match in matches:
        if match in dictionary.values():
            abbrevs.append(match)
        else:
            for key in dictionary.keys():
                if key is match:
                    abbrevs.append(dictionary[key])
    return abbrevs


def check_word_in_list_in_string(list, string):
    '''
    Returns not None if a word in the list is contained in the string
    :param list:
    :param string:
    :return: None if list has no elements contained in string
    '''
    stuff = [string for word in list if(word in string)]
    return stuff

def header_huffington():
    '''
    Builds a header for the huffington post output
    :return:
    '''
    head = '\n ^^Polls ^^fetched ^^from ^^[http://elections.huffingtonpost.com/](http://elections.huffingtonpost.com/).\n\n'
    head += '***{}***\n\n'.format(get_greeting())
    head += '.\n\n'
    head += '.\n\n'
    return head


def footer():
    '''
    Builds bot header
    :return:
    '''
    foot = '^^Pollster ^^bot ^^ver. ^^{}'.format(version)
    foot += '\n\nSummon pollster bot by typing in Pollster_Bot and then any state or states.\n\nEx. Pollster Bot CA Texas Maine RI'
    foot += "\n\n***If you have any feedback on this bot then [Click Here](http://i.imgur.com/YFIri5g.jpg).***"
    return foot


def format_estimates(estimates):
    reply = ''
    reply += '\nChoice | Percentage | Party\n'
    reply += '------|----------|-----\n'
    for estimate in estimates:
        if not estimate['party']:
            estimate['party'] = ''
        reply += '{} | {} | {} \n'.format(estimate['choice'], str(estimate['value']), estimate['party'])
    return reply + '\n\n'


def format_poll(poll):
    state = ''
    for name, abb in states.items():
        if poll['state'] == abb:
            state = name
    reply = ''
    reply += '\n\n***' + state + ' Poll:' + '***\n\n'
    reply += format_estimates(poll['estimates'])
    reply += r'^^Link ^^to ^^poll ^^' + str(poll['url'] + '\n\n')

    return reply


def check_condition(comment):
    '''
    Checks if we have a keyword in the comment, then if we have a list of states also.
    :param comment:
    :return: if we should act on the comment or not
    '''
    boolean_return = True
    # First check for keywords in comment, for now we don't care about formatting after the keyword
    hasKeyword = check_word_in_list_in_string(keywords, comment.body)
    if not hasKeyword:
        boolean_return = False
    #Next we check if we have states or abbreviations
    abbrevs = check_comment_for_dictionary_keys_and_values(comment, states)
    if len(abbrevs) < 1:
        boolean_return = False
    if str(comment.author) == bot_name:
        boolean_return = False
    for reply in comment.replies:
        if str(reply.author) == bot_name:
            boolean_return = False
    return boolean_return, abbrevs


def bot_action(comment, abbrevs):
    response = header_huffington()
    done_reqs = []
    for abbrev in abbrevs:
        if abbrev not in done_reqs:
            done_reqs.append(abbrev)
            polls = get_poll_huffington(abbrev)
            for poll in polls:
                response += format_poll(poll)

    response += footer()
    comment.reply(response)

    #log
    print comment.author
    print comment.body
    print abbrevs
    print response


def mainLoop():
    submissions = get_submissions(default_sub, submission_limit=None)
    for submission in submissions:
        comments = get_flat_comments(submission, comment_limit=None)
        for comment in comments:
            check, abbrevs = check_condition(comment)
            if check:
                bot_action(comment, abbrevs)


class MyDaemon(Daemon):
    def run(self):
        while True:
            mainLoop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/daemon-example.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        #mainLoop()
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
