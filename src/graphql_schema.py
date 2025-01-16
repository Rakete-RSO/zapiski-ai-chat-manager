from typing import List

import strawberry
from fastapi import HTTPException
from strawberry.types import Info

# Suppose you have these imports available
from .auth import verify_access_token
from .config import meilisearch_index_chats  # Or wherever you import it from


@strawberry.type
class ChatType:
    id: str
    name: str


@strawberry.type
class Query:
    # Existing resolvers (like get_user) here...

    @strawberry.field
    def list_chats(self, info: Info, access_token: str) -> List[ChatType]:
        payload = verify_access_token(access_token)
        if not payload:
            # Return empty, None, or raise an exception as needed
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = payload["sub"]

        # Example: Updating filterable attributes if needed
        # meilisearch_index_chats.update_filterable_attributes(["user_id", "name", "id"])

        # Perform the Meilisearch query
        search_results = meilisearch_index_chats.search(
            "",
            {
                "filter": f"user_id = '{user_id}'",
                "limit": 1000,
            },
        )

        # Return as a list of ChatType
        return [
            ChatType(id=hit["id"], name=hit["name"]) for hit in search_results["hits"]
        ]


# @strawberry.type
# class Mutation:
#     # Existing mutations (like register_user) here...
#     pass


# Finally, build your schema
schema = strawberry.Schema(query=Query)
