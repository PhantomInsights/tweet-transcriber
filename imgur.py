"""
Mirrors a Twitter image to Imgur.
"""

import requests

import config


def upload_image(image_url):
    """Uploads an image to Imgur and returns the permanent link url.

    Parameters
    ----------
    image_url : str
        The url of the original image.

    Returns
    -------
    str
        The url generated from the Imgur API.

    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0"}

    with requests.get(image_url, headers=headers) as image_response:

        # We extract the file extension from the url.
        file_extension = image_url.split(".")[-1].split(":")[0]
        file_name = "./temp." + file_extension

        # We store the file in the current folder.
        with open(file_name, "wb") as temp_file:
            temp_file.write(image_response.content)

    # We start the upload process to Imgur.
    api_url = "https://api.imgur.com/3/image"
    headers = {"Authorization": "Client-ID " + config.IMGUR_CLIENT_ID}
    files = {"image": open(file_name, "rb")}

    with requests.post(api_url, headers=headers, files=files) as response:

        # We extract the new link from the response and return it.
        return response.json()["data"]["link"]
