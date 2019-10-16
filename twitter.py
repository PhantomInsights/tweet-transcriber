"""
This script has 2 functions, one is used to extract the values we need from
a Tweet HTML source.

The other one creates a Markdown text with the previous generated values and
mirrors the tweet's images to Imgur.
"""

from datetime import datetime

import requests
from bs4 import BeautifulSoup

from imgur import upload_image


URL_SHORTENERS = [
    "bit.ly",
    "ow.ly",
    "tinyurl"
]


def transcribe_tweet(tweet_url, template):
    """Generates a Markdown message by Filling the values into the message template.

    PArameters
    ----------
    tweet_url : string
        The tweet url.

    template : string
        The message string template. See the template folder for details.

    Returns
    -------
    string
        The post template filled with the tweet data values.

    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0"}

    # We make a GET requeswt to the tweet url.
    with requests.get(tweet_url, headers=headers) as tweet_response:

        # We send the HTML source of the tweet to the scrape_Tweet function.
        tweet_data = scrape_tweet(tweet_response.text)

        # We start taking the values from the returned dictionary and applying transformations.
        tweet_date = datetime.fromtimestamp(tweet_data["timestamp"])

        # By default we assume we have image links and initialize the inner links template.
        image_links_text = "*****\n\n**Image(s):**\n\n"

        if len(tweet_data["images"]) > 0:

            # For each link we have we will mirror it to Imgur and update our inner links template.
            for index, link in enumerate(tweet_data["images"]):

                # We upload the image to Imgur and get the new url.
                imgur_url = upload_image(link)

                # We update our inner template with both links (original and Imgur).
                image_links_text += "[Image {}]({}) - [Mirror]({})\n\n".format(
                    index + 1, link, imgur_url)

        else:
            # If we have no images we set the image_links_text to an empty string.
            image_links_text = ""

        # By default we assume we have video links and initialize the inner links template.
        video_links_text = "*****\n\n**Video(s):**\n\n"

        if len(tweet_data["videos"]) > 0:

            # For each link we have we will update our inner links template.
            for index, link in enumerate(tweet_data["videos"]):

                # We update our inner template with both links (original and Imgur).
                video_links_text += "[Video {}]({})\n\n".format(
                    index + 1, link)

        else:
            # If we have no videos we set the video_links_text to an empty string.
            video_links_text = ""

        text_lines = list()

        # We split the tweet text by the new line character.
        for line in tweet_data["text"].split("\n"):

            # If the list element is not empty we apply a custom formatting.
            if len(line) > 0:

                # We will add a backlash when a line starts with a hashtag to avoid making a Markdown header.
                if line[0] == "#":
                    text_lines.append("\#" + line[1:])
                else:
                    text_lines.append(line)
            else:
                text_lines.append("\n")

        # We join together the tweet text to its original form but with our cleaned formatting.
        # The templates can be found in the templates folder.
        tweet_text = "\n".join(text_lines)

        # We fill in the message template with our variables.
        post_text = template.format(
            tweet_data["fullname"],
            tweet_data["username"],
            tweet_date,
            tweet_date,
            tweet_data["permalink"],
            tweet_text,
            image_links_text,
            video_links_text,
            tweet_data["retweets"],
            tweet_data["favorites"],
            tweet_data["replies"]
        )

        return post_text


def scrape_tweet(html):
    """Extracts data from the tweet HTML source.

    Parameters
    ----------
    html : string
        The HTML source of the tweet.

    Returns
    -------
    dict
        A dictionary Containing several important values.

    """

    # We init the BeautifulSoup object and begin extracting values.
    soup = BeautifulSoup(html, "html.parser")

    tweet = soup.find("p", "TweetTextSize--jumbo")

    permalink = soup.find("link", {"rel": "canonical"})["href"]
    timestamp = int(tweet.find_previous("span", "_timestamp")["data-time"])
    fullname = soup.find("a", "fullname").text.strip()
    username = soup.find("div", "ProfileCardMini-screenname").text.strip()

    favorites = int(tweet.find_next(
        "span", "ProfileTweet-action--favorite").find("span")["data-tweet-stat-count"])

    retweets = int(tweet.find_next(
        "span", "ProfileTweet-action--retweet").find("span")["data-tweet-stat-count"])

    replies = int(tweet.find_next(
        "span", "ProfileTweet-action--reply").find("span")["data-tweet-stat-count"])

    # Fix for emojis so they appear in text and not as images.
    for tag in tweet.find_all("img"):

        if "Emoji" in tag["class"]:
            tag.string = tag["alt"]

    # We check if the tweet has embedded pictures.
    has_twitter_pics = False

    for tag in tweet.find_all("a"):

        # If the pic.twitter.com domain is found we delete the tag and break the loop.
        if "pic.twitter.com" in tag.text:
            has_twitter_pics = True
            tag.extract()

        # This will convert url shorteners to their real urls.
        for shortener in URL_SHORTENERS:

            if shortener in tag.text:
                tag.string = resolve_shortener(tag.text)
                break

        # Removes ellipsis from t.co links.
        if tag.get("data-expanded-url"):
            tag.string = tag["data-expanded-url"]

    # We extract all the images links.
    image_links = list()

    if has_twitter_pics:

        for tag in soup.find_all("meta", {"property": "og:image"}):

            tag_content_url = tag["content"]

            if "video_thumb" not in tag_content_url:
                image_links.append(tag_content_url)

    # We get the video links.
    video_links = list()

    for tag in soup.find_all("meta", {"property": "og:video:url"}):
        video_links.append(tag["content"])

    # We add a little padding for the other links inside the tweet message.
    tweet_text = tweet.text.replace("http", " http").strip()

    return {
        "permalink": permalink,
        "timestamp": timestamp,
        "fullname": fullname,
        "username": username,
        "favorites": favorites,
        "retweets": retweets,
        "replies": replies,
        "images": image_links,
        "videos": video_links,
        "text": tweet_text
    }


def resolve_shortener(url):
    """Gets the real url from the url-shortener service.

    Parameters
    ----------    
    url : string
        A bit.ly url.

    Returns
    -------
    string
        The real url.

    """

    with requests.head(url) as response:
        return response.headers["location"]
