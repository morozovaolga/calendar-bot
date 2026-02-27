from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GraphQLClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._api_sem = asyncio.Semaphore(5)
        self._http = httpx.AsyncClient(
            timeout=30.0,
            headers={"Content-Type": "application/json"},
        )

        self._cache_books_by_author: dict[str, List[Dict]] = {}
        self._cache_book_by_uuid: dict[str, Dict] = {}
        self._cache_books_by_tag: dict[str, List[Dict]] = {}
        self._cache_books_by_category: dict[str, List[Dict]] = {}

    async def aclose(self):
        await self._http.aclose()

    async def post(self, query: str, variables: dict) -> httpx.Response:
        async with self._api_sem:
            return await self._http.post(self.endpoint, json={"query": query, "variables": variables})

    async def get_books_by_author(self, author_uuid: str) -> List[Dict]:
        if author_uuid in self._cache_books_by_author:
            return self._cache_books_by_author[author_uuid]

        query = """
        query GetBooksByAuthor($authorUuid: String!) {
          books(body: {
            authors: [$authorUuid]
            isActive: true
            limit: 10
          }) {
            uuid
            name
            slug
            annotation
            image {
              url
            }
          }
        }
        """
        variables = {"authorUuid": author_uuid}

        max_retries = 4
        retry_delay = 3.0

        for attempt in range(max_retries):
            try:
                response = await self.post(query, variables)
                if response.status_code != 200:
                    logger.error(
                        "❌ [get_books_by_author] Ошибка API (code %s) для автора %s",
                        response.status_code,
                        author_uuid,
                    )
                    self._cache_books_by_author[author_uuid] = []
                    return []

                data = response.json()
                if "errors" in data:
                    logger.warning("⚠️ [get_books_by_author] GraphQL ошибки: %s", data["errors"])

                books = (((data or {}).get("data") or {}).get("books")) or []
                if books:
                    self._cache_books_by_author[author_uuid] = books
                    return books

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

                self._cache_books_by_author[author_uuid] = []
                return []
            except Exception as e:
                logger.error("Ошибка запроса к API (попытка %s): %s", attempt + 1, e, exc_info=True)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                self._cache_books_by_author[author_uuid] = []
                return []

        self._cache_books_by_author[author_uuid] = []
        return []

    async def get_books_by_author_slug(self, author_slug: str) -> List[Dict]:
        query = """
        query GetBooksByAuthorSlug($authorSlug: String!) {
          books(body: {
            authorsSlugs: [$authorSlug]
            isActive: true
            limit: 6
          }) {
            uuid
            name
            slug
            annotation
            image {
              url
            }
          }
        }
        """
        variables = {"authorSlug": author_slug}

        try:
            response = await self.post(query, variables)
            if response.status_code == 200:
                data = response.json()
                return (((data or {}).get("data") or {}).get("books")) or []
            logger.error("Ошибка API по author_slug: %s", response.status_code)
        except Exception as e:
            logger.error("Ошибка запроса к API по author_slug: %s", e)
        return []

    async def get_book_by_uuid(self, book_uuid: str) -> Optional[Dict]:
        if book_uuid in self._cache_book_by_uuid:
            return self._cache_book_by_uuid[book_uuid]

        query = """
        query GetBookByUuid($bookUuid: String!) {
          books(body: {
            uuids: [$bookUuid]
            isActive: true
            limit: 1
          }) {
            uuid
            name
            slug
            annotation
            image {
              url
            }
          }
        }
        """
        variables = {"bookUuid": book_uuid}

        try:
            response = await self.post(query, variables)
            if response.status_code != 200:
                logger.warning("⚠️ [get_book_by_uuid] Ошибка API (code %s) для книги %s", response.status_code, book_uuid)
                return None
            data = response.json()
            books = (((data or {}).get("data") or {}).get("books")) or []
            if books:
                self._cache_book_by_uuid[book_uuid] = books[0]
                return books[0]
        except Exception as e:
            logger.warning("⚠️ [get_book_by_uuid] Ошибка запроса к API для книги %s: %s", book_uuid, e)
        return None

    async def search_books_by_title(self, title: str, author_name: str | None = None) -> List[Dict]:
        clean_title = re.sub(r'[«»""„‟]', "", title).strip()

        query = """
        query SearchBooks($names: [String!]!) {
          books(body: {
            names: $names
            isActive: true
            limit: 6
          }) {
            uuid
            name
            slug
            annotation
            authors {
              uuid
            }
            image {
              url
            }
          }
        }
        """

        search_names = [clean_title]
        if author_name:
            search_names.append(f"{author_name} {clean_title}")
        variables = {"names": search_names}

        try:
            response = await self.post(query, variables)
            if response.status_code == 200:
                data = response.json()
                books = (((data or {}).get("data") or {}).get("books")) or []
                logger.info("Найдено книг по запросу '%s': %s", clean_title, len(books))
                return books
            logger.error("Ошибка API поиска книг (code %s): %s", response.status_code, response.text[:200])
        except Exception as e:
            logger.error("Ошибка запроса поиска книг: %s", e)
        return []

    async def get_books_by_tag(self, tag: str) -> List[Dict]:
        if tag in self._cache_books_by_tag:
            return self._cache_books_by_tag[tag]

        query = """
        query GetBooksByTag($tagSlug: String!) {
          tags(body: {
            slugs: [$tagSlug]
          }) {
            uuid
            name
            books(limit: 6) {
              uuid
              name
              slug
              image {
                url
              }
            }
          }
        }
        """
        variables = {"tagSlug": tag}

        try:
            response = await self.post(query, variables)
            if response.status_code == 200:
                data = response.json()
                tags = (((data or {}).get("data") or {}).get("tags")) or []
                books = (tags[0].get("books") if tags else None) or []
                self._cache_books_by_tag[tag] = books
                return books
        except Exception as e:
            logger.error("Ошибка запроса к API по тегу: %s", e)

        self._cache_books_by_tag[tag] = []
        return []

    async def get_books_by_category(self, category_uuid: str) -> List[Dict]:
        if category_uuid in self._cache_books_by_category:
            return self._cache_books_by_category[category_uuid]

        query = """
        query GetBooksByCategory($categoryUuid: String!) {
          category(body: { uuid: $categoryUuid }) {
            uuid
            name
            books(limit: 6) {
              uuid
              name
              slug
              image {
                url
              }
            }
          }
        }
        """
        variables = {"categoryUuid": category_uuid}

        try:
            response = await self.post(query, variables)
            if response.status_code == 200:
                data = response.json()
                category = ((data or {}).get("data") or {}).get("category") or {}
                books = category.get("books") or []
                self._cache_books_by_category[category_uuid] = books
                return books
        except Exception as e:
            logger.error("Ошибка запроса к API по категории: %s", e)

        self._cache_books_by_category[category_uuid] = []
        return []

