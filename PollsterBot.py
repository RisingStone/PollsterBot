__author__ = 'm.stanford'
import praw
import requests
import json
import os
from Daemon import Daemon
import sys
import time
import datetime
from dateutil import parser
import random
import logging


class PollsterBot(Daemon):

    def __init__(self, pid):
        Daemon.__init__(self, pid)

        # Reddit https://praw.readthedocs.io/en/stable/pages/comment_parsing.html
        self.reddit = {}
        self.default_subs = 'pollster_bot'
        self.bot_name = 'pollster_bot'
        self.version = '0.3b'
        self.touched_comment_ids = []

        # create logger
        self.logger = logging.getLogger('Pollster_Bot')
        self.logger.setLevel(logging.INFO)
        # File handler set to DEBUG
        fh = logging.FileHandler(filename=os.path.join(os.path.dirname(__file__), 'PollsterBotLog.txt'))
        fh.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # add formatter to ch
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add ch, fh to logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

        self.logger.info('Starting Pollster Bot ver. ' + self.version)

        # Huffington post http://elections.huffingtonpost.com/pollster/api
        self.uri = 'http://elections.huffingtonpost.com/pollster/api/charts.json'

        # Set states
        self.states = {}
        self.states = self.load_json_file('data/states.json')

        # phrases
        phrases = self.load_json_file('data/phrases.json')
        self.greetings = phrases['greeting']
        self.winning = phrases['winning']
        self.losing = phrases['losing']

        # keywords to call the pollster bot
        self.keywords = self.load_json_file('data/keywords.json')['keywords']

        # subs
        subs = self.load_json_file('data/subs.json')['subs']
        for sub in subs:
            self.default_subs += '+' + sub

        self.log_in_credentials = self.load_json_file('data/login_credentials.json')

    def login(self):
        self.logger.info('Login started Pollster Bot ver. ' + self.version)
        login_name = self.log_in_credentials['user']
        login_password = self.log_in_credentials['password']
        self.reddit = praw.Reddit(user_agent='Pollster')
        self.reddit.login(login_name, login_password, disable_warning=False)
        self.logger.info('Login Completed Pollster Bot ver. ' + self.version)

    # Returns a dictionary of states.
    def load_json_file(self, filename):
        self.logger.info('Read {} Pollster Bot ver. {}'.format(filename, self.version))
        fn = os.path.join(os.path.dirname(__file__), filename)
        with open(fn) as data_file:
            return json.load(data_file)

    def get_greeting(self):
        return random.choice(self.greetings)

    def get_winning(self, winner, points):
        return random.choice(self.winning).format(winner, points)

    def get_losing(self, loser, points):
        return random.choice(self.losing).format(loser, points)

    # Gets all submissions in the subreddit as a generator.
    def get_submissions(self, subreddit, submission_limit=25):
        donald_submissions = self.reddit.get_subreddit(subreddit).get_hot(limit=submission_limit)
        return donald_submissions

    @staticmethod
    def get_comments(submission, comment_limit=25):
        submission.replace_more_comments(limit=comment_limit, threshold=0)
        return submission.comments

    def get_flat_comments(self, submission, comment_limit=25):
        try:
            submission.replace_more_comments(limit=comment_limit, threshold=0)
        except requests.exceptions.ConnectionError:
            self.logger.error('Error fetching comments!')
            return None
        return praw.helpers.flatten_tree(submission.comments)

    def get_recent_comments(self, subreddit):
        comments = self.reddit.get_comments(subreddit)
        return praw.helpers.flatten_tree(comments)

    def get_comments_with_helper(self, subreddit):
        comments = praw.helpers.comment_stream(self.reddit, subreddit)
        return praw.helpers.flatten_tree(comments)

    # Gets polls from state, defaults to 2016-president race
    def get_poll_huffington(self, state, page=1, topic='2016-president'):
        poll_params = {'page': page, 'state': state, 'topic': topic}
        my_response = requests.get(self.uri, params=poll_params)
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
    @staticmethod
    def check_comment_for_dictionary_keys_and_values(comment, dictionary):
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

    @staticmethod
    def check_word_in_list_in_string(list, string):
        """
        Returns not None if a word in the list is contained in the string
        :param list:
        :param string:
        :return: None if list has no elements contained in string
        """
        stuff = [string for word in list if(word in string)]
        return stuff

    def header_huffington(self):
        """
        Builds a header for the huffington post output
        :return:
        """
        head = '\n ^^Polls ^^fetched ^^from ^^[http://elections.huffingtonpost.com/](http://elections.huffingtonpost.com/).\n\n'
        head += '***{}***\n\n'.format(self.get_greeting())
        head += '.\n\n'
        head += '.\n\n'
        return head

    def footer(self):
        """
        Builds bot header
        :return:
        """
        foot = '^^Pollster ^^bot ^^ver. ^^{}'.format(self.version)
        foot += '\n\nSummon pollster bot by typing in Pollster_Bot and then any state or states.\n\nEx. Pollster Bot CA Texas Maine RI'
        foot += "\n\n***If you have any feedback on this bot then [Click Here](http://i.imgur.com/YFIri5g.jpg).***"
        return foot

    @staticmethod
    def format_estimates(estimates):
        reply = ''
        reply += '\nChoice | Percentage | Party\n'
        reply += '------|----------|-----\n'
        for estimate in estimates:
            if not estimate['party']:
                estimate['party'] = ''
            reply += '{} | {} | {} \n'.format(estimate['choice'], str(estimate['value']), estimate['party'])
        return reply + '\n\n'

    def format_poll(self, poll):
        state = ''
        for name, abb in self.states.items():
            if poll['state'] == abb:
                state = name
        reply = ''
        reply += '\n\n***' + state + ' Poll:' + '***\n\n'
        reply += self.format_estimates(poll['estimates'])
        datetime_string = poll['last_updated']
        dt = parser.parse(datetime_string)
        datetime_string = dt.strftime('%b %d %Y %I:%M%p')
        reply += 'Date of poll: {} \n\n'.format(datetime_string)
        reply += r'^^Link ^^to ^^poll ^^' + str(poll['url'] + '\n\n')
        return reply

    def check_condition(self, comment):
        """
        Checks if we have a keyword in the comment, then if we have a list of states also.
        :param comment:
        :return: if we should act on the comment or not
        """
        if comment.id in self.touched_comment_ids:
            return False, None
        # First check for keywords in comment, for now we don't care about formatting after the keyword
        has_keyword = self.check_word_in_list_in_string(self.keywords, comment.body)
        if not has_keyword:
            return False, None
        # Next we check if we have states or abbreviations
        abbrevs = self.check_comment_for_dictionary_keys_and_values(comment, self.states)
        if len(abbrevs) < 1:
            return False, None
        if str(comment.author) == self.bot_name:
            return False, None
        for reply in comment.replies:
            if str(reply.author) == self.bot_name:
                return False, None
        return True, abbrevs

    def bot_action(self, comment, abbrevs):
        response = self.header_huffington()
        done_reqs = []
        for abbrev in abbrevs:
            if abbrev not in done_reqs:
                done_reqs.append(abbrev)
                polls = self.get_poll_huffington(abbrev)
                for poll in polls:
                    response += self.format_poll(poll)

        response += self.footer()

        try:
            comment.reply(response)
            self.touched_comment_ids.append(comment.id)
            # log
            log_out = ''
            log_out += 'Time: {} \nAuthor: {} \nBody: {}\n States: {} \nResponse: {} \n'.format((datetime.timedelta(milliseconds=(time.time()))), comment.author, comment.body, abbrevs, response)
            self.logger.info(log_out)
        except praw.errors.RateLimitExceeded:
            self.logger.warn("RateLimitExceeded!!! Response not posted!!!")

    def slow_loop(self):
        submissions = self.get_submissions(self.default_subs, submission_limit=100)
        for submission in submissions:
            self.logger.info(u'Crawling Submission ' + submission.title)
            time_start = time.time()
            comments = self.get_recent_comments(submission)
            for comment in comments:
                check, abbrevs = self.check_condition(comment)
                if check:
                    self.bot_action(comment, abbrevs)
            time_end = time.time()
            crawl_time = int(time_end) - int(time_start)
            crawl_string = 'Crawl time: ' + str(crawl_time) + ' seconds'
            self.logger.info(crawl_string)

    def main_loop(self):
        for comment in self.get_recent_comments(self.default_subs):
            check, abbrevs = self.check_condition(comment)
            if check:
                self.bot_action(comment, abbrevs)

    def run_forever(self):
        self.logger.info('Forever Loop started Pollster Bot ver. ' + self.version)
        self.login()
        while 1 < 2:
            self.main_loop()

    def run(self):
        self.logger.info('Running Pollster Bot ver. ' + self.version)
        self.run_forever()


if __name__ == "__main__":
    daemon = PollsterBot('/tmp/pollsterBot.pid')
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
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
