# Tweet Transcriber

This project implements a custom algorithm that extracts the most important values from a given tweet url, converts it into a `MArkdown`  formatted text and mirrors any images into `Imgur`.

The formatted message and images are then posted to `Reddit` with a simple bot framework.

The code has been organized in a way that you will only require to call one function with a tweet HTML source and you will get all the important values in a dictionary. This way you can integrate it into your data pipelines with very low effort.

It was fully developed in `Python` and it is inspired by similar projects seen on `Reddit` that appear to be defunct.

The 2 most important files are:

* `twitter.py` : This script includes 2 functions, one extracts all important values from a tweet HTML source and the other creates a `Markdown` text and mirrors twitter images to Imgur.

* `bot_sidewide.py` : A Reddit bot that checks all posts from the domain twitter.com and replies to them with a transcribed tweet.

This project uses the following Python libraries

* `PRAW` : Makes the use of the Reddit API very easy.
* `Requests` : To perform HTTP `get` requests to twitter.com.
* `BeautifulSoup` : Used for extracting tweet data.

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

IF all this process was successful we update our processed posts log and move to the next post. If it fails we log the error for later verification.

```python
update_log(POSTS_LOG, submission.id)
print("Replied:", submission.id)
```

The process is a bit simila for tweet links inside a comment, all links are extracted from the comment and those that match our criteria are transcribed and added into a list.

```python
# Sometimes a comment may contain several links, we look for all of them.
comment_text = list()

for link in comment.body.split():
    if "twitter.com" in link and "/status/" in link:
        comment_text.append(transcribe_tweet(link.replace("mobile.", ""), MESSAGE_TEMPLATE))
```

This list is then joined into a string and this string is then used to reply to the comment.

```python
reddit.comment(comment.id).reply("\n\n*****".join(comment_text))
```

## Web Scraper

To extract the values from the tweet HTML source I used `BeautifulSoup` and studied where I could reliably find the values I needed, such as the number of likes, retweets, replies and the timestamp.

It is very important to look for the tweet that has `jumbo` in its class name since it is the linked tweet.

```python
soup = BeautifulSoup(html, "html.parser")

tweet = soup.find("p", "TweetTextSize--jumbo")

permalink = soup.find("link", {"rel": "canonical"})["href"]
timestamp = int(soup.find("span", "_timestamp")["data-time"])
fullname = soup.find("a", "fullname").text.strip()
username = soup.find("div", "ProfileCardMini-screenname").text.strip()

favorites = int(tweet.find_next(
    "span", "ProfileTweet-action--favorite").find("span")["data-tweet-stat-count"])

retweets = int(tweet.find_next(
    "span", "ProfileTweet-action--retweet").find("span")["data-tweet-stat-count"])

replies = int(tweet.find_next(
    "span", "ProfileTweet-action--reply").find("span")["data-tweet-stat-count"])
```

In the HTML of the tweet body we can find several anchor tags, each tag represents a link the user typed in. But something very important is that a tag pointing to `pic.twitter.com` means that the tweet contains one or more images.

We check for that and if the link does exist we remove it from the tweet body and begin looking for the embedded images urls.

```python
has_twitter_pics = False

for tag in tweet.find_all("a"):

    # If the pic.twitter.com domain is found we delete the tag and break the loop.
    if "pic.twitter.com" in tag.text:
        has_twitter_pics = True
        tag.extract()
        break
```

Something very interesting is that when a tweet has images you can find their direct urls in the `link` tags near the top of the document.

```python
image_links = [tag["content"] for tag in soup.find_all("meta", {"property": "og:image"})]
```

After we got all the values mapped to variables we pack them in a dictionary and return it.

This dictionary can then be easily saved to CSV or JSON files using the built in libraries.

## Conclusion

I'm currently using these bots only on the subreddits I manage as an extra enhancement to the user experience. As of lately when celebrities and politicians publish highly controversial tweets they often delete them after a few minutes and I despise that behaviour.

One of the purposes of this project is to have a backup mechanism for said tweets. It can also be used to keep a local copy of the tweets and perform analysis on them in an easier to parse format (Python dictionary).

If you have any questions you are always welcome to open an issue.

[![Become a Patron!](https://c5.patreon.com/external/logo/become_a_patron_button.png)](https://www.patreon.com/bePatron?u=20521425)