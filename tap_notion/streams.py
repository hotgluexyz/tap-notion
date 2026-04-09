from typing import Any, Dict, Optional, TypeVar, Union

from hotglue_singer_sdk import typing as th

from tap_notion.client import NotionStream

_TToken = TypeVar("_TToken")

class SearchPagesStream(NotionStream):
    name = "search_pages"
    path = "/search"
    primary_keys = ["id"]
    replication_key = "last_edited_time"
    rest_method = "POST"
    schema = th.PropertiesList(
        th.Property("object", th.StringType),
        th.Property("id", th.StringType),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_edited_time", th.DateTimeType),
        th.Property(
            "created_by",
            th.ObjectType(
                th.Property("object", th.StringType),
                th.Property("id", th.StringType),
            ),
        ),
        th.Property(
            "last_edited_by",
            th.ObjectType(
                th.Property("object", th.StringType),
                th.Property("id", th.StringType),
            ),
        ),
        th.Property("cover", th.CustomType({"type": ["object", "string"]})),
        th.Property(
            "icon",
            th.ObjectType(
                th.Property("type", th.StringType),
                th.Property("emoji", th.StringType),
            ),
        ),
        th.Property(
            "parent",
            th.ObjectType(
                th.Property("type", th.StringType),
                th.Property("page_id", th.StringType),
            ),
        ),
        th.Property("archived", th.BooleanType),
        th.Property("properties", th.CustomType({"type": ["object", "string"]})),
        th.Property("url", th.StringType),
    ).to_dict()

    def prepare_request_payload(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Optional[dict]:

        payload = {
            "filter": {"value": "page", "property": "object"},
            "sort": {"direction": "ascending", "timestamp": "last_edited_time"},
            "page_size": 100,
        }

        if next_page_token:
            payload.update({"start_cursor": next_page_token})

        return payload

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        return {"block_id": record["id"]}


class BlocksSteam(NotionStream):
    name = "blocks"
    path = "/blocks/{block_id}/children"
    primary_keys = ["id"]
    replication_key = "last_edited_time"
    rest_method = "GET"
    parent_stream_type = SearchPagesStream

    def _get_state_partition_context(self, context: Optional[dict]):
        return None


    schema = th.PropertiesList(
        th.Property("object", th.StringType),
        th.Property("id", th.StringType),
        th.Property(
            "parent",
            th.ObjectType(
                th.Property("type", th.StringType),
                th.Property("page_id", th.StringType),
            ),
        ),
        th.Property("created_time", th.DateTimeType),
        th.Property("last_edited_time", th.DateTimeType),
        th.Property(
            "created_by",
            th.ObjectType(
                th.Property("object", th.StringType), th.Property("id", th.StringType)
            ),
        ),
        th.Property(
            "last_edited_by",
            th.ObjectType(
                th.Property("object", th.StringType), th.Property("id", th.StringType)
            ),
        ),
        th.Property("has_children", th.BooleanType),
        th.Property("archived", th.BooleanType),
        th.Property("type", th.StringType),
        th.Property(
            "child_database", th.ObjectType(th.Property("title", th.StringType))
        ),
        th.Property("child_page", th.ObjectType(th.Property("title", th.StringType))),
        th.Property("heading_3", th.CustomType({"type": ["object", "string"]})),
        th.Property("heading_2", th.CustomType({"type": ["object", "string"]})),
        th.Property("heading_1", th.CustomType({"type": ["object", "string"]})),
        th.Property("to_do", th.CustomType({"type": ["object", "string"]})),
        th.Property("paragraph", th.CustomType({"type": ["object", "string"]})),
        th.Property(
            "bulleted_list_item", th.CustomType({"type": ["object", "string"]})
        ),
        th.Property(
            "numbered_list_item", th.CustomType({"type": ["object", "string"]})
        ),
        th.Property("toggle", th.CustomType({"type": ["object", "string"]})),
        th.Property("child_page", th.CustomType({"type": ["object", "string"]})),
        th.Property("child_database", th.CustomType({"type": ["object", "string"]})),
        th.Property("embed", th.CustomType({"type": ["object", "string"]})),
        th.Property("image", th.CustomType({"type": ["object", "string"]})),
        th.Property("video", th.CustomType({"type": ["object", "string"]})),
        th.Property("file", th.CustomType({"type": ["object", "string"]})),
        th.Property("pdf", th.CustomType({"type": ["object", "string"]})),
        th.Property("bookmark", th.CustomType({"type": ["object", "string"]})),
        th.Property("callout", th.CustomType({"type": ["object", "string"]})),
        th.Property("quote", th.CustomType({"type": ["object", "string"]})),
        th.Property("equation", th.CustomType({"type": ["object", "string"]})),
        th.Property("divider", th.CustomType({"type": ["object", "string"]})),
        th.Property("table_of_contents", th.CustomType({"type": ["object", "string"]})),
        th.Property("column", th.CustomType({"type": ["object", "string"]})),
        th.Property("column_list", th.CustomType({"type": ["object", "string"]})),
        th.Property("link_preview", th.CustomType({"type": ["object", "string"]})),
        th.Property("synced_block", th.CustomType({"type": ["object", "string"]})),
        th.Property("template", th.CustomType({"type": ["object", "string"]})),
        th.Property("link_to_page", th.CustomType({"type": ["object", "string"]})),
        th.Property("table", th.CustomType({"type": ["object", "string"]})),
        th.Property("table_row", th.CustomType({"type": ["object", "string"]})),
        th.Property("unsupported", th.CustomType({"type": ["object", "string"]})),
    ).to_dict()

    def get_url_params(
        self, context: Union[dict, None], next_page_token: Union[_TToken, None]
    ) -> Dict[str, Any]:

        params = {"page_size": 100}

        if next_page_token:
            params.update({"start_cursor": next_page_token})

        return params
