import json
from typing import Optional, Tuple

import requests
from hotglue_etl_exceptions import InvalidCredentialsError
from hotglue_singer_sdk.authenticators import OAuthAuthenticator, SingletonMeta
from hotglue_singer_sdk.helpers._util import utc_now


from hotglue_singer_sdk.streams import Stream as RESTStreamBase


class NotionAuthenticator(OAuthAuthenticator, metaclass=SingletonMeta):
    @classmethod
    def create_for_stream(cls, stream: RESTStreamBase) -> "NotionAuthenticator":
        return cls(
            stream=stream,
            auth_endpoint="https://api.notion.com/v1/oauth/token",
            oauth_scopes=None,
        )

    @property
    def oauth_request_body(self) -> dict:
        refresh = self.config.get("refresh_token")
        if not refresh:
            raise InvalidCredentialsError("OAuth mode requires refresh_token")
        return {
            "grant_type": "refresh_token",
            "refresh_token": str(refresh).strip(),
        }

    def request_auth(self) -> Optional[Tuple[str, str]]:
        cid = self.config.get("client_id")
        sec = self.config.get("client_secret")
        if not cid or not sec:
            raise InvalidCredentialsError(
                "OAuth mode requires client_id and client_secret "
                "(Notion token endpoint uses HTTP Basic authentication)."
            )
        return (str(cid).strip(), str(sec).strip())

    def update_access_token_locally(self) -> None:
        request_time = utc_now()
        token_response = requests.post(
            self.auth_endpoint,
            json=self.oauth_request_body,
            auth=self.request_auth(),
            headers={
                "Accept": "application/json",
                "Notion-Version": "2026-03-11",
            },
            timeout=60,
        )
        try:
            token_response.raise_for_status()
            self.logger.info("OAuth authorization attempt was successful.")
        except Exception as ex:
            raise InvalidCredentialsError(
                f"Failed OAuth login, response was '{token_response.text}'. {ex}"
            )
        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        expires_in = token_json.get("expires_in", self._default_expiration)
        if expires_in is None:
            self.logger.debug(
                "No expires_in receied in OAuth response and no "
                "default_expiration set. Token will be treated as if it never "
                "expires."
            )
            self.expires_in = None
        else:
            self.expires_in = int(expires_in) + int(request_time.timestamp())

        self.last_refreshed = request_time
        self._tap._config["access_token"] = token_json["access_token"]
        self._tap._config["expires_in"] = self.expires_in
        if token_json.get("refresh_token"):
            self._tap.logger.info(
                f"Latest refresh token: {token_json.get('refresh_token')}"
            )
            self._tap._config["refresh_token"] = token_json["refresh_token"]

        if self._tap.config_file is not None:
            with open(self._tap.config_file, "w") as outfile:
                json.dump(self._tap._config, outfile, indent=4)
