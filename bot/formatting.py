from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from literary_calendar_database import LiteraryCalendarDatabase
from time_utils import now_tz


def normalize_image_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    url = url.lstrip("/")
    return f"https://example.com/{url}"


def extract_image_url_from_metadata(metadata) -> str:
    if not metadata:
        return ""

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            return metadata if metadata.startswith("http") else ""

    if not isinstance(metadata, dict):
        return ""

    image_data = metadata.get("image", {}) or {}
    if isinstance(image_data, dict):
        url = image_data.get("url") or image_data.get("original") or image_data.get("preview")
        if url:
            return normalize_image_url(url)
    elif isinstance(image_data, str):
        return normalize_image_url(image_data)

    for key in ("cover_url", "image_url", "cover"):
        url = metadata.get(key)
        if url:
            return normalize_image_url(url)

    return ""


def get_age_word(age: int) -> str:
    last_digit = age % 10
    last_two_digits = age % 100
    if 11 <= last_two_digits <= 14:
        return "лет"
    if last_digit == 1:
        return "год"
    if last_digit in (2, 3, 4):
        return "года"
    return "лет"


def format_event_message(
    event: Dict,
    timezone: str,
    books: Optional[List[Dict]] = None,
    include_image_urls: bool = True,
    other_links: Optional[List[Dict]] = None,
) -> str:
    message_parts: List[str] = []

    message_parts.append(f"📚 <b>{event['title']}</b>")

    if event.get("start_date"):
        months = [
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        ]
        date_obj = event["start_date"]
        month_name = months[date_obj.month - 1]
        date_str = f"{date_obj.day} {month_name} {date_obj.year}"
        message_parts.append(f"📅 {date_str}")

    if event.get("event_type") == "день рождения":
        birth_year = None
        year_match = re.search(r"\b(1[0-9]{3}|2[0-2][0-9]{2})\b", event.get("title", ""))
        if year_match:
            birth_year = int(year_match.group(1))

        if not birth_year and event.get("year"):
            reference_date = LiteraryCalendarDatabase.parse_reference_date(event.get("year"))
            if reference_date and 1400 <= reference_date.year <= now_tz(timezone).year:
                birth_year = reference_date.year

        if birth_year:
            current_date = event.get("start_date", now_tz(timezone))
            age = current_date.year - birth_year
            if age > 0:
                is_jubilee = age % 10 == 0 or age % 10 == 5
                age_word = get_age_word(age)
                if is_jubilee:
                    message_parts.append(f"🎂 <u><b>🎉 {age} {age_word} со дня рождения 🎉</b></u>")
                else:
                    message_parts.append(f"🎂 {age} {age_word} со дня рождения")

    if event.get("description"):
        message_parts.append(f"\n{event['description']}")

    if other_links:
        message_parts.append("\n🔗 <b>Ссылки:</b>")
        for l in other_links:
            name = l.get("name") or ""
            url = l.get("url") or ""
            if url:
                message_parts.append(f"\n• <a href='{url}'>{name}</a>")
            else:
                message_parts.append(f"\n• {name}")

    if books:
        message_parts.append("\n📖 <b>Книги:</b>")
        for book in books[:6]:
            book_name = book.get("name", "Без названия")
            book_slug = book.get("slug", "")
            metadata = book.get("metadata", {}) or {}

            book_url = f"https://example.com/catalog/{book_slug}" if book_slug else ""
            if book_url:
                message_parts.append(f"• <a href='{book_url}'>{book_name}</a>")
            else:
                message_parts.append(f"• {book_name}")

            image_data = metadata.get("image", {}) or {}
            if include_image_urls and isinstance(image_data, dict):
                image_url = image_data.get("url", "")
                if image_url:
                    message_parts.append(f"  <i>Обложка: {image_url}</i>")

            annotation = metadata.get("annotation", "")
            if annotation:
                message_parts.append(f"  <i>{annotation[:100]}</i>")
    else:
        message_parts.append("\n<i>Читайте и слушайте книги в «Свете»!</i>")

    return "\n".join(message_parts)

