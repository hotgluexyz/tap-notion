"""REST client handling, including NotionStream base class."""

from typing import Any, Optional, Union

import requests
from memoization import cached
from hotglue_singer_sdk.authenticators import BearerTokenAuthenticator

from tap_notion.auth import NotionAuthenticator
from hotglue_singer_sdk.helpers.jsonpath import extract_jsonpath
from hotglue_singer_sdk.streams import RESTStream


class NotionStream(RESTStream):
    """Notion stream class."""

    url_base = "https://api.notion.com/v1"

    records_jsonpath = "$.results[*]" 
    next_page_token_jsonpath = "$.next_cursor" 

    @property
    @cached
    def authenticator(self) -> Union[BearerTokenAuthenticator, NotionAuthenticator]:
        if self.config.get("use_oauth", False) or self.config.get("use_mcp", False):
            return NotionAuthenticator.create_for_stream(self)
        return BearerTokenAuthenticator.create_for_stream(
            self, self.config.get("access_token")
        )

    @property
    def http_headers(self) -> dict:
        headers = {}
        headers["Notion-Version"] = "2022-06-28"
        return headers

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:

        all_matches = extract_jsonpath(self.next_page_token_jsonpath, response.json())
        first_match = next(iter(all_matches), None)
        next_page_token = first_match

        return next_page_token
