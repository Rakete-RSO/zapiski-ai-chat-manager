# zapiski-ai-chat-manager

Microservice that manages chats in the zapiski AI platform.

It enables:

- search functionality over previous chats through the non-relational database meilisearch
- renaming the chat

## Development

### Locally

In this case, postgresql is deployed through docker-compose, and poetry packages are installed locally:

- In repo `zapiski-ai-dev-env`, start docker compose (to start postgresql).
- To setup python packages and start the server (prerequisite: `poetry`). NOTE: This is WIP and may not be 100% like this.
  - `poetry install`
  - `cp .example.env .env`
  - `poetry run uvicorn src.main:app --reload --port 8002`

## Provided requests

Are located in `zapiski-ai-dev-env` Postman collection.

## Additional comments

Tjaz: By default, I was running this on port 8002. If you're running multiple API servers (e.g., this and auth) at the same time
during local development, they have to be exposed over different ports. I just use various random defaults here.
