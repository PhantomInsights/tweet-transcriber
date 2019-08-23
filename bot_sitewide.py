"""
This bot searches for all Reddit posts that are from the reddit.com
domain and replies to them with a transcribed tweet.
"""

import praw

import config
from twitter import transcribe_tweet

POSTS_LOG = "./processed_posts.txt"
ERROR_LOG = "./error.log"

MESSAGE_TEMPLATE = open("./templates/en.txt", "r", encoding="utf-8").read()


def init_bot():
    """Inits the bot and checks for new posts."""

    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    check_posts(reddit)


def check_posts(reddit):
    """Checks the latest posts from the twiter.com domain.

    Parameters
    ----------
    reddit : praw.Reddit
        A Reddit instance.

    """

    processed_posts = load_log(POSTS_LOG)

    # We iterate over all new twitter.com posts.
    for submission in reddit.domain("twitter.com").new(limit=100):

        if "twitter.com" in submission.url and "status" in submission.url and submission.id not in processed_posts:

            try:
                reddit.submission(submission.id).reply(
                    transcribe_tweet(submission.url.replace("mobile.", ""), MESSAGE_TEMPLATE))

                update_log(POSTS_LOG, submission.id)
                print("Replied:", submission.id)

            except Exception as e:
                update_log(POSTS_LOG, submission.id)
                log_error("{}:{}".format(submission.url, e))
                print("Failed:", submission.id)


def load_log(log_file):
    """Reads the processed posts log file and creates it if it doesn't exist.

    Returns
    -------
    list
        A list of Reddit posts ids.

   """

    try:
        with open(log_file, "r", encoding="utf-8") as temp_file:
            return temp_file.read().splitlines()

    except FileNotFoundError:
        with open(log_file, "a", encoding="utf-8") as temp_file:
            return []


def update_log(log_file, item_id):
    """Updates the processed posts log with the given post id.

    Parameters
    ----------
    comment_id : str
        A Reddit post id.

    """

    with open(log_file, "a", encoding="utf-8") as temp_file:
        return temp_file.write("{}\n".format(item_id))


def log_error(error_message):
    """Updates the error log.

    Parameters
    ----------
    error_message : str
        A string containing the faulty url and the exception message.

    """

    with open(ERROR_LOG, "a", encoding="utf-8") as log_file:
        return log_file.write("{}\n".format(error_message))


if __name__ == "__main__":

    init_bot()
