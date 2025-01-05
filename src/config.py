import os

import meilisearch
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY == "":
    raise Exception("SECRET_KEY environment variable is not set")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL") or ""
if DATABASE_URL == "":
    raise Exception("DATABASE_URL environment variable is not set")

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"

MEILI_BASE_URL = os.getenv("MEILI_BASE_URL")
if MEILI_BASE_URL == "":
    raise Exception("MEILI_BASE_URL environment variable is not set")

MEILI_MASTER_KEY = os.getenv("MEILI_MASTER_KEY")
if MEILI_MASTER_KEY == "":
    raise Exception("MEILI_MASTER_KEY environment variable is not set")

meilisearch_client = meilisearch.Client(str(MEILI_BASE_URL), MEILI_MASTER_KEY)
meilisearch_index_chats = meilisearch_client.index("chats")
