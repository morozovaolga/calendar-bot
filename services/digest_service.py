from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List, Tuple

from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError

from bot.formatting import extract_image_url_from_metadata, format_event_message
from clients.graphql_client import GraphQLClient

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)


class DigestService:
    def __init__(self, bot: Bot, gql: GraphQLClient, timezone: str):
        self._bot = bot
        self._gql = gql
        self._timezone = timezone

    async def collect_books_and_links(self, event: Dict) -> Tuple[List[Dict], List[Dict]]:
        books: List[Dict] = []
        other_links: List[Dict] = []
        max_books = 6

        event_title = event.get("title", "Без названия")
        logger.info("🔍 [collect_books_and_links] Начинаем сбор книг для события: '%s'", event_title)

        # 1. Добавляем книги из book_references БД (если есть)
        for book_ref in event.get("book_references", []):
            if len(books) >= max_books:
                break

            book_uuid = book_ref["uuid"]
            book_metadata = book_ref.get("metadata", {}) or {}

            has_cover = False
            if book_metadata:
                image_url = extract_image_url_from_metadata(book_metadata)
                has_cover = bool(image_url)

            if not has_cover and book_uuid:
                logger.info(
                    "🔄 [collect_books_and_links] Обложка не найдена в БД для книги '%s', запрашиваем через API...",
                    book_ref.get("name"),
                )
                api_book = await self._gql.get_book_by_uuid(book_uuid)
                if api_book:
                    book_image = api_book.get("image", {}) or {}
                    if book_image.get("url"):
                        book_metadata = {"image": book_image}
                        logger.info(
                            "✅ [collect_books_and_links] Обложка получена через API для книги '%s'",
                            book_ref.get("name"),
                        )
                    else:
                        logger.warning(
                            "⚠️ [collect_books_and_links] API не вернул обложку для книги '%s'",
                            book_ref.get("name"),
                        )
                else:
                    logger.warning(
                        "⚠️ [collect_books_and_links] Не удалось получить информацию о книге '%s' через API",
                        book_ref.get("name"),
                    )

            books.append(
                {
                    "uuid": book_uuid,
                    "name": book_ref["name"],
                    "slug": book_ref["slug"],
                    "metadata": book_metadata,
                    "source": "database",
                }
            )

        # 2. Книги по авторам + ссылки на авторов
        for author_ref in event.get("author_refs", []):
            if len(books) >= max_books:
                break

            au_uuid = author_ref.get("uuid")
            au_name = author_ref.get("name") or ""
            au_slug = author_ref.get("slug", "")

            author_identifier = au_slug if au_slug else au_uuid
            if author_identifier:
                author_url = f"https://example.com/authors/{author_identifier}"
                other_links.append({"type": "author", "name": au_name or "Автор", "url": author_url})

            if au_uuid:
                author_books = await self._gql.get_books_by_author(au_uuid)
                for book in author_books:
                    if len(books) >= max_books:
                        break
                    if not any(b.get("uuid") == book.get("uuid") for b in books):
                        book_image = book.get("image", {}) or {}
                        books.append(
                            {
                                "uuid": book.get("uuid"),
                                "name": book.get("name", "Без названия"),
                                "slug": book.get("slug", ""),
                                "metadata": {"image": book_image},
                                "source": "author_api",
                            }
                        )

        # 3. Книги по тегам + ссылки
        for tag_ref in event.get("tag_refs", []):
            if len(books) >= max_books:
                break
            tag_uuid = tag_ref.get("uuid")
            tag_name = tag_ref.get("name") or ""
            if tag_uuid:
                tag_url = f"https://example.com/catalog?tags={tag_uuid}"
                other_links.append({"type": "tag", "name": tag_name or "Тег", "url": tag_url})
                tag_books = await self._gql.get_books_by_tag(tag_uuid)
                for book in tag_books:
                    if len(books) >= max_books:
                        break
                    if not any(b.get("uuid") == book.get("uuid") for b in books):
                        books.append(
                            {
                                "uuid": book.get("uuid"),
                                "name": book.get("name", "Без названия"),
                                "slug": book.get("slug", ""),
                                "metadata": {"image": book.get("image", {})} if book.get("image") else {},
                                "source": "tag_api",
                            }
                        )

        # 4. Книги по категориям + ссылки
        for cat_ref in event.get("category_refs", []):
            if len(books) >= max_books:
                break
            cat_uuid = cat_ref.get("uuid")
            cat_name = cat_ref.get("name") or ""
            if cat_uuid:
                cat_url = f"https://example.com/catalog?categories={cat_uuid}"
                other_links.append(
                    {"type": "category", "name": cat_name or "Категория", "url": cat_url}
                )
                cat_books = await self._gql.get_books_by_category(cat_uuid)
                for book in cat_books:
                    if len(books) >= max_books:
                        break
                    if not any(b.get("uuid") == book.get("uuid") for b in books):
                        books.append(
                            {
                                "uuid": book.get("uuid"),
                                "name": book.get("name", "Без названия"),
                                "slug": book.get("slug", ""),
                                "metadata": {"image": book.get("image", {})} if book.get("image") else {},
                                "source": "category_api",
                            }
                        )

        return books, other_links

    async def send_event_with_media(self, chat_id: str, event: Dict):
        try:
            books, other_links = await self.collect_books_and_links(event)

            media_items: List[InputMediaPhoto] = []
            for book in books:
                if len(media_items) >= 6:
                    break
                metadata = book.get("metadata", {}) or {}
                image_url = extract_image_url_from_metadata(metadata)
                if not image_url:
                    continue
                caption = book.get("name", "")
                try:
                    media_items.append(InputMediaPhoto(media=image_url, caption=caption))
                except Exception:
                    continue

            if media_items:
                try:
                    full_message = format_event_message(
                        event=event,
                        timezone=self._timezone,
                        books=books,
                        include_image_urls=False,
                        other_links=other_links,
                    )

                    max_caption = 1024
                    if len(full_message) > max_caption:
                        open_tag_stack: List[str] = []
                        tag_pattern = re.compile(r"<(/?)([a-z]+)[^>]*>", re.IGNORECASE)
                        safe_cut_pos = max_caption - 20

                        for match in tag_pattern.finditer(full_message[:safe_cut_pos]):
                            is_closing = match.group(1) == "/"
                            tag_name = match.group(2).lower()
                            if is_closing:
                                if open_tag_stack and open_tag_stack[-1] == tag_name:
                                    open_tag_stack.pop()
                            else:
                                if tag_name in ["a", "b", "i", "u", "strong", "em"]:
                                    open_tag_stack.append(tag_name)

                        if open_tag_stack:
                            last_close_pos = -1
                            for tag in ["a", "b", "i", "u", "strong", "em"]:
                                pos = full_message[:safe_cut_pos].rfind(f"</{tag}>")
                                if pos > last_close_pos:
                                    last_close_pos = pos + len(f"</{tag}>")

                            if last_close_pos > 100:
                                truncated = full_message[:last_close_pos]
                            else:
                                last_space = full_message[:safe_cut_pos].rfind(" ")
                                truncated = full_message[:last_space] if last_space > 100 else full_message[:safe_cut_pos]

                            for tag in reversed(open_tag_stack):
                                truncated += f"</{tag}>"
                        else:
                            truncated = full_message[:safe_cut_pos]

                        full_message = truncated + "..."

                    if HAS_BS4:
                        try:
                            soup = BeautifulSoup(full_message, "html.parser")
                            full_message = str(soup)
                            if full_message.startswith("<html>"):
                                full_message = full_message[6:]
                            if full_message.startswith("<body>"):
                                full_message = full_message[6:]
                            if full_message.endswith("</body></html>"):
                                full_message = full_message[:-14]
                            elif full_message.endswith("</html>"):
                                full_message = full_message[:-7]
                            elif full_message.endswith("</body>"):
                                full_message = full_message[:-7]
                        except Exception:
                            pass

                    if len(media_items) == 1:
                        await self._bot.send_photo(
                            chat_id=chat_id,
                            photo=media_items[0].media,
                            caption=full_message,
                            parse_mode="HTML",
                        )
                        await asyncio.sleep(0.5)
                        return

                    media_to_send: List[InputMediaPhoto] = []
                    for idx, m in enumerate(media_items[:6]):
                        if idx == 0:
                            media_to_send.append(
                                InputMediaPhoto(media=m.media, caption=full_message, parse_mode="HTML")
                            )
                        else:
                            media_to_send.append(InputMediaPhoto(media=m.media))

                    await self._bot.send_media_group(chat_id=chat_id, media=media_to_send)
                    await asyncio.sleep(0.5)
                    return
                except TelegramError as e:
                    logger.warning("Не удалось отправить медиа: %s", e)
                    message = format_event_message(
                        event=event,
                        timezone=self._timezone,
                        books=books,
                        include_image_urls=True,
                        other_links=other_links,
                    )
                    for send_attempt in range(3):
                        try:
                            await self._bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
                            await asyncio.sleep(1)
                            return
                        except TelegramError as e2:
                            if send_attempt < 2:
                                await asyncio.sleep(2)
                            else:
                                logger.error("❌ Не удалось отправить сообщение (fallback): %s", e2)
                                return

            # no media
            message = format_event_message(
                event=event,
                timezone=self._timezone,
                books=books,
                include_image_urls=True,
                other_links=other_links,
            )
            for send_attempt in range(3):
                try:
                    await self._bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
                    await asyncio.sleep(1)
                    return
                except TelegramError as e:
                    if send_attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        logger.error("❌ Не удалось отправить сообщение: %s", e)
                        return
        except Exception as e:
            logger.error("Ошибка обработки события '%s': %s", event.get("title"), e, exc_info=True)

