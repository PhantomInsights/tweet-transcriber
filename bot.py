"""
This bot checks both new posts and comments from the given subreddits.

If it finds tweet links it replies to them with a transcribed tweet.
"""

import praw
from bs4 import BeautifulSoup

import config
from twitter import transcribe_tweet

COMMENTS_LOG = "./processed_comments.txt"
POSTS_LOG = "./processed_posts.txt"
ERROR_LOG = "./error.log"

# Don't forget to use the template for your language.
MESSAGE_TEMPLATE = open("./templates/es.txt", "r", encoding="utf-8").read()


def init_bot():
    """Inits the bot and checks for new posts and comments."""

    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    check_posts(reddit)
    check_comments(reddit)


def check_posts(reddit):
    """Checks the latest posts from a given subreddit.

    Parameters
    ----------
    reddit : praw.Reddit
        A Reddit instance.

    """

    processed_posts = load_log(POSTS_LOG)

    # We iterate over all our desired subreddits.
    for subreddit in config.SUBREDDITS:

        # Then we iterate over all the new posts.
        for submission in reddit.subreddit(subreddit).new(limit=100):

            if "twitter.com" in submission.url and "status" in submission.url and submission.id not in processed_posts:

                try:
                    reddit.submission(submission.id).reply(transcribe_tweet(
                        submission.url.replace("mobile.", ""), MESSAGE_TEMPLATE))

                    update_log(POSTS_LOG, submission.id)
                    print("Replied:", submission.id)

                except Exception as e:
                    update_log(POSTS_LOG, submission.id)
                    log_error("{}:{}".format(submission.url, e))
                    print("Failed:", submission.id)


def check_comments(reddit):
    """Checks the latest comments from a given subreddit.

    Parameters
    ----------
    reddit : praw.Reddit
        A Reddit instance.

    """

    processed_comments = load_log(COMMENTS_LOG)

    # We iterate over all our desired subreddits.
    for subreddit in config.SUBREDDITS:

        # Then we iterate over all the new comments.
        for comment in reddit.subreddit(subreddit).comments(limit=100):

            # Only take into account new comments with a valid twitter link and not being made by this bot.
            if "twitter.com" in comment.body_html and "/status/" in comment.body_html and comment.author != config.REDDIT_USERNAME and comment.id not in processed_comments:

                try:
                    # Sometimes a comment may contain several links, we look for all of them.
                    comment_text = list()

                    # Get all tweet links.
                    soup = BeautifulSoup(comment.body_html, "html.parser")

                    for link in soup.find_all("a"):

                        if "twitter.com" in link["href"] and "/status/" in link["href"]:

                            comment_text.append(transcribe_tweet(
                                link["href"].replace("mobile.", ""), MESSAGE_TEMPLATE))

                    reddit.comment(comment.id).reply(
                        "\n\n*****\n\n".join(comment_text))

                    update_log(COMMENTS_LOG, comment.id)
                    print("Replied:", comment.id)

                except Exception as e:
                    update_log(COMMENTS_LOG, comment.id)
                    log_error("{}:{}".format(comment.id, e))
                    print("Faiied:", comment.id)


def load_log(log_file):
    """Reads the processed comments/posts log file and creates it if it doesn't exist.

    Returns
    -------
    list
        A list of Reddit comments/posts ids.

   """

    try:
        with open(log_file, "r", encoding="utf-8") as temp_file:
            return temp_file.read().splitlines()

    except FileNotFoundError:
        with open(log_file, "a", encoding="utf-8") as temp_file:
            return []


def update_log(log_file, item_id):
    """Updates the processed comments/posts log with the given comment/post id.

    Parameters
    ----------
    item_id : str
        A Reddit comment/post id.

    """

    with open(log_file, "a", encoding="utf-8") as temp_file:
        temp_file.write("{}\n".format(item_id))


def log_error(error_message):
    """Updates the error log.

    Parameters
    ----------
    error_message : str
        A string containing the faulty url and the exception message.

    """

    with open(ERROR_LOG, "a", encoding="utf-8") as log_file:
        log_file.write("{}\n".format(error_message))


if __name__ == "__main__":

    init_bot()
