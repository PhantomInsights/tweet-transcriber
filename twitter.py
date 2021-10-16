"""
This script has 2 functions, one is used to extract the values we need from
a Tweet HTML source.

The other one creates a Markdown text with the previous generated values and
mirrors the tweet's images to Imgur.
"""

import json
from datetime import datetime

import requests

from imgur import upload_image


HEADERS = {
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAAPYXBAAAAAAACLXUNDekMxqa8h%2F40K4moUkGsoc%3DTYfbDKbT3jJPCEVnMYqilB28NHfOPqkca3qaAxGfsyKCs0wRbw"
}

BASE_URL = "https://api.twitter.com/1.1/"


URL_SHORTENERS = [
    "bit.ly",
    "ow.ly",
    "tinyurl"
]


def transcribe_tweet(tweet_url, template):
    """Generates a Markdown message by filling the values into the message template.

    PArameters
    ----------
    tweet_url : str
        The tweet url.

    template : str
        The message string template. See the template folder for details.

    Returns
    -------
    str
        The post template filled with the tweet data values.

    """

    request_token()

    tweet_id = tweet_url.split("/status/")[-1].split("?")[0]
    final_url = BASE_URL + \
        f"statuses/show.json?id={tweet_id}&tweet_mode=extended"

    # We make a GET requeswt to the tweet url.
    with requests.get(final_url, headers=HEADERS) as tweet_response:

        # We send the HTML source of the tweet to the scrape_Tweet function.
        tweet_data = scrape_tweet(tweet_response.text)

        # We start taking the values from the returned dictionary and applying transformations.
        tweet_date = datetime.fromtimestamp(tweet_data["timestamp"])

        # By default we assume we have image links and initialize the inner links template.
        image_links_text = "*****\n\n**Imágenes:**\n\n"

        if len(tweet_data["images"]) > 0:

            # For each link we have we will mirror it to Imgur and update our inner links template.
            for index, link in enumerate(tweet_data["images"], 1):

                # We upload the image to Imgur and get the new url.
                imgur_url = upload_image(link)

                # We update our inner template with both links (original and Imgur).
                image_links_text += "[Imagen {}]({}) - [Mirror]({})\n\n".format(
                    index, link, imgur_url)

        else:
            # If we have no images we set the image_links_text to an empty string.
            image_links_text = ""

        # By default we assume we have video links and initialize the inner links template.
        video_links_text = "*****\n\n**Video(s):**\n\n"

        if len(tweet_data["videos"]) > 0:

            # For each link we have we will update our inner links template.
            for index, link in enumerate(tweet_data["videos"], 1):

                # We update our inner template with the links.
                video_links_text += "[Video {}]({})\n\n".format(index, link)

        else:
            # If we have no videos we set the video_links_text to an empty string.
            video_links_text = ""

        # By default we assume we have url links and initialize the inner links template.
        url_links_text = "*****\n\n**Link(s):**\n\n"

        if len(tweet_data["links"]) > 0:

            # For each link we have we will update our inner links template.
            for index, link in enumerate(tweet_data["links"], 1):

                # We update our inner template with the links.
                url_links_text += "[Link {}]({})\n\n".format(index, link)

        else:
            # If we have no links we set the video_links_text to an empty string.
            url_links_text = ""

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
            url_links_text,
            tweet_data["retweets"],
            tweet_data["favorites"]
        )

        return post_text


def scrape_tweet(data):
    """Extracts data from the tweet JSON file.

    Parameters
    ----------
    data : str
        The tweet JSON string.

    Returns
    -------
    dict
        A dictionary Containing several important values.

    """

    tweet = json.loads(data)

    timestamp = datetime.strptime(
        tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y").timestamp()

    tweet_id = tweet["id"]
    fullname = tweet["user"]["name"]
    username = tweet["user"]["screen_name"]
    permalink = f"https://twitter.com/{username}/status/{tweet_id}"

    favorites = tweet["favorite_count"]
    retweets = tweet["retweet_count"]

    # We extract all the images and video links.
    image_links = list()
    video_links = list()

    if "extended_entities" in tweet:

        for item in tweet["extended_entities"]["media"]:

            if item["type"] == "photo":
                image_links.append(
                    item["media_url_https"] + "?format=jpg&name=4096x4096")
            elif item["type"] == "video":
                video_links.append(item["video_info"]["variants"][0]["url"])

    url_links = list()

    # We look for all the links in the tweet and unshorten them.
    for item in tweet["entities"]["urls"]:
        
        link = item["expanded_url"]
        
        for shortener in URL_SHORTENERS:
            if shortener in link:
                link = resolve_shortener(link)
                break

        url_links.append(link)

    # We add a little padding for the other links inside the tweet message.
    tweet_text = tweet["full_text"].split(
        "https://t.co")[0].split("http://t.co")[0].strip()

    return {
        "permalink": permalink,
        "timestamp": int(timestamp),
        "fullname": fullname,
        "username": username,
        "favorites": favorites,
        "retweets": retweets,
        "images": image_links,
        "videos": video_links,
        "links": url_links,
        "text": tweet_text
    }


def request_token():
    """Gets a Guest Token from the API."""

    with requests.post(BASE_URL + "guest/activate.json", headers=HEADERS) as response:
        guest_token = response.json()["guest_token"]
        HEADERS["x-guest-token"] = guest_token


def resolve_shortener(url):
    """Gets the real url from the url-shortener service.

    Parameters
    ----------    
    url : str
        A shortened url.

    Returns
    -------
    str
        The real url.

    """

    with requests.head(url) as response:
        return response.headers["location"]
