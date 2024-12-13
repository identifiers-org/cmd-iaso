import asyncio
import random

from collections import defaultdict

import httpx

HTTPX_TIMEOUT = 60.0
INITIAL_BACKOFF = 0.25
RANKING_LIMIT = 10


class WikiDataClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(HTTPX_TIMEOUT, read=80.0),
        )

        self.waiting = defaultdict(int)  # Number of waiting requests
        self.running = defaultdict(int)  # Number of running requests
        self.queue = defaultdict(list)  # Requests not yet scheduled
        self.backoff = dict()  # Exponential backoff times

    async def request(self, namespace, *args, **kwargs):
        while True:
            self.waiting[namespace] += 1

            # Only enqueue and wait if there are already ongoing requests
            if self.waiting[namespace] > 1:
                schedule = asyncio.Future()

                self.queue[namespace].append(schedule)

                await schedule
            else:
                self.running[namespace] += 1

            backoff = self.backoff.get(namespace, INITIAL_BACKOFF)

            # Schedule the next request using the current backoff
            if len(self.queue[namespace]) > 0:
                next_scheduled = self.queue[namespace].pop(0)

                self.running[namespace] += 1

                asyncio.get_event_loop().call_later(
                    backoff, next_scheduled.set_result, None
                )

            response = await self.client.get(*args, **kwargs)

            # Adjust the exponential backoff times
            if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
                self.backoff[namespace] = max(
                    INITIAL_BACKOFF,
                    min(
                        self.backoff.get(namespace, INITIAL_BACKOFF),
                        backoff - INITIAL_BACKOFF,
                    ),
                )
            else:
                self.backoff[namespace] = max(
                    self.backoff.get(namespace, INITIAL_BACKOFF), backoff * 2
                )

            self.waiting[namespace] -= 1
            self.running[namespace] -= 1

            # Schedule the next request iff we are the only one left who can
            if len(self.queue[namespace]) > 0 and self.running[namespace] < 1:
                next_scheduled = self.queue[namespace].pop(0)

                self.running[namespace] += 1

                next_scheduled.set_result(None)

            # Return iff successful, retry iff backoff required
            if response.status_code != httpx.codes.TOO_MANY_REQUESTS:
                return response

    async def search(self, terms, strict=False):
        response = await self.request(
            "search",
            (
                "https://www.wikidata.org/w/api.php?action=query&list=search"
                + f"&srsearch={terms.lower() if strict else terms.lower().replace(' ', ' OR ')}"
                + f"&srlimit={RANKING_LIMIT}&srprop=&format=json"
            ),
        )

        return response.json()

    async def query(self, query):
        response = await self.request(
            "query",
            "https://query.wikidata.org/sparql",
            params={"format": "json", "query": query},
        )

        return response.json()
