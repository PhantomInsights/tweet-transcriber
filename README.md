# Tweet Transcriber

This project implements a custom algorithm that extracts the most important values from a given tweet url, converts it into a `Markdown`  formatted text and mirrors any images into `Imgur`.

The formatted message and images are then posted to `Reddit` with a simple bot framework.

The code has been organized in a way that you will only require to call one function with a tweet JSON source and you will get all the important values in a dictionary. This way you can integrate it into your data pipelines with very low effort.

It was fully developed in `Python` and it is inspired by similar projects seen on `Reddit` that appear to be defunct.

The 2 most important files are:

* `twitter.py` : This script includes 2 functions, one extracts all important values from a tweet JSON source and the other creates a `Markdown` text and mirrors twitter images to Imgur.

* `bot_sidewide.py` : A Reddit bot that checks all posts from the domain twitter.com and replies to them with a transcribed tweet.

## Requirements

This project uses the following Python libraries

* `PRAW` : Makes the use of the Reddit API very easy.
* `Requests` : To perform HTTP requests to twitter.com.
* `BeautifulSoup` : To extract twitter urls from the Reddit comments

## Reddit Bots

This project includes 2 bots, `bot_sitewide.py` and `bot.py`. They share most of the code but have a small difference:

* `bot.py` - This bot will look for tweets in subreddits posts and comments and reply to them with transcribed tweets.

* `bot_sitewide.py` - This bot will only look for posts from the twitter.com domain and reply to them with a transcribed tweet.

Both bots keep a log of which comments and posts they have processed, this is to avoid making duplicate comments.

When they request the new posts they first check that the post is not already processed and that the post contains in the url the strings `twitter.com` and `/status/`. This will ensure the link is indeed a tweet and not other Twitter url.

```python
processed_posts = load_log(POSTS_LOG)

# We iterate over all new twitter.com posts.
for submission in reddit.domain("twitter.com").new(limit=100):

    if "twitter.com" in submission.url and "status" in submission.url and submission.id not in processed_posts:
```

After that the script removes the `mobile.` part of the tweet url, I found out that the HTML source varies a lot between mobile and not mobile tweet urls.

With the proper url at hand we send it to the `transcribe_tweet()` function from the `twitter.py` file.

```python
reddit.submission(submission.id).reply(transcribe_tweetsubmission.url.replace("mobile.", ""), MESSAGE_TEMPLATE))
```

This function will return us a `Markdown` formatted text that will then be used to reply to the original post. This function takes 2 parameters, a tweet url and a string template, you can find them in the templates folder.

If all this process was successful we update our processed posts log and move to the next post. If it fails we log the error for later verification.

```python
update_log(POSTS_LOG, submission.id)
print("Replied:", submission.id)
```

The process is a bit similar for tweet links inside a comment, all links are extracted from the comment and those that match our criteria are transcribed and added into a list.

```python
# Sometimes a comment may contain several links, we look for all of them.
comment_text = list()

# Get all tweet links.
soup = BeautifulSoup(comment.body_html, "html.parser")

for link in soup.find_all("a"):

    if "twitter.com" in link["href"] and "/status/" in link["href"]:
        comment_text.append(transcribe_tweet(link["href"].replace("mobile.", ""), MESSAGE_TEMPLATE))
```

This list is then joined into a string and this string is then used to reply to the comment.

```python
reddit.comment(comment.id).reply("\n\n*****\n\n".join(comment_text))
```

## Tweet Scraper

To extract the values from the tweet JSON source I used the same technique as other Twitter content downloaders.

You must first request a `guest_token` to the Twitter API sneding a harcoded `Bearer Token`.

Once you get the `guest_token` you can sign with it some of the Twitter read-only endpoints, cush as `statuses/show.json` which is used in this project.

You will receive almost the same JSON as with the regular API.

## Conclusion

I'm currently using these bots only on the subreddits I manage as an extra enhancement to the user experience. As of lately when celebrities and politicians publish highly controversial tweets they often delete them after a few minutes and I despise that behaviour.

One of the purposes of this project is to have a backup mechanism for said tweets. It can also be used to keep a local copy of the tweets and perform analysis on them in an easier to parse format (Python dictionary).

If you have any questions you are always welcome to open an issue.

[![Become a Patron!](https://c5.patreon.com/external/logo/become_a_patron_button.png)](https://www.patreon.com/bePatron?u=20521425)
