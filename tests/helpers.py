import os
from dotenv import load_dotenv

from thingsboard_api_tools.TbApi import TbApi


load_dotenv()


def get_tbapi_from_env() -> TbApi:
    """
    Create a TbApi instance using environment variables for configuration.

    Expects MOTHERSHIP_URL, THINGSBOARD_USERNAME, and THINGSBOARD_PASSWORD to be set or be included
    in a .env file.
    """

    mothership_url = os.getenv("MOTHERSHIP_URL")
    thingsboard_username = os.getenv("THINGSBOARD_USERNAME")
    thingsboard_password = os.getenv("THINGSBOARD_PASSWORD")

    msg = "MOTHERSHIP_URL, THINGSBOARD_USERNAME, and THINGSBOARD_PASSWORD environment variables must be set to run these tests -- put them in a .env file in the repo root for convenience."
    assert mothership_url and thingsboard_username and thingsboard_password, msg

    return TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)
