import os
from dotenv import load_dotenv
from typing import Any
import json

from thingsboard_api_tools.TbApi import TbApi

load_dotenv()


def get_tbapi_from_env(verbose: bool = False) -> TbApi:
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

    tbapi = TbApi(url=mothership_url, username=thingsboard_username, password=thingsboard_password)

    if verbose:
        tbapi.verbose = True

    return tbapi


def mock_get_paged_customers(self: TbApi, params: str, msg: str) -> list[dict[str, Any]]:
    """
    Mock function to simulate TbApi.get_paged for customers with fixed data from file.  Much faster than the real deal.
    """
    with open("tests/data/customers_unsorted.json", "r", encoding="utf-8") as filex:
        data = json.load(filex)
        return data
