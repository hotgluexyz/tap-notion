from typing import List

from hotglue_singer_sdk import Stream, Tap
from hotglue_singer_sdk import typing as th

from tap_notion.auth import NotionAuthenticator, token_endpoint_for
from tap_notion.streams import BlocksSteam, SearchPagesStream

STREAM_TYPES = [SearchPagesStream, BlocksSteam]


class TapNotion(Tap):

    name = "tap-notion"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "use_oauth",
            th.BooleanType,
            default=False,
            required=False,
            description="If true, use OAuth (client_id, client_secret, refresh_token). "
            "If false, use internal integration access_token only.",
        ),
        th.Property(
            "access_token",
            th.StringType,
            required=False,
            description="Internal integration token (Bearer). Required when use_oauth is false.",
        ),
        th.Property(
            "client_id",
            th.StringType,
            required=False,
            description="Public integration OAuth client id (required when use_oauth is true).",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=False,
            description="Public integration OAuth client secret (required when use_oauth is true).",
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            required=False,
            description="OAuth refresh token from Notion (required when use_oauth is true).",
        ),
        th.Property(
            "use_mcp",
            th.BooleanType,
            default=False,
            required=False,
            description="If true, refresh tokens against the Notion MCP token endpoint. If false, refresh tokens against the Notion OAuth token endpoint.",

        ),
        th.Property(
            "expires_in",
            th.IntegerType,
            required=False,
            description="Access token expiry, written back by the tap after a refresh.",
        ),
    ).to_dict()

    @classmethod
    def access_token_support(cls, connector=None):
        config = connector.config if connector is not None else {}
        return NotionAuthenticator, token_endpoint_for(config)

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapNotion.cli()