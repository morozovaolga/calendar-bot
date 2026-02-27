from __future__ import annotations

import logging
from typing import Dict, List

from telegram import Bot

from bot.formatting import get_age_word

logger = logging.getLogger(__name__)


class JubileeService:
    def __init__(self, bot: Bot):
        self._bot = bot

    async def send_jubilees_for_year(self, chat_id: str, year: int, jubilees: List[Dict]):
        try:
            if not jubilees:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=f"🎉 Юбиляров в {year} году не найдено.",
                    parse_mode="HTML",
                )
                return

            months = [
                "январь",
                "февраль",
                "март",
                "апрель",
                "май",
                "июнь",
                "июль",
                "август",
                "сентябрь",
                "октябрь",
                "ноябрь",
                "декабрь",
            ]

            jubilees_by_month: dict[int, list[Dict]] = {}
            for ev in jubilees:
                event_date = ev.get("event_date", "")
                if event_date:
                    try:
                        month_str, _day_str = event_date.split("-")
                        month = int(month_str)
                        if 1 <= month <= 12:
                            jubilees_by_month.setdefault(month, []).append(ev)
                            continue
                    except (ValueError, AttributeError):
                        pass
                jubilees_by_month.setdefault(0, []).append(ev)

            parts = [f"🎉 <b>Юбиляры — {year} год</b>\n"]

            for month_num in range(1, 13):
                if month_num not in jubilees_by_month:
                    continue
                month_name = months[month_num - 1]
                parts.append(f"\n📅 <b>{month_name.capitalize()}</b>")

                month_jubilees = jubilees_by_month[month_num]
                month_jubilees.sort(
                    key=lambda e: (
                        int(e.get("event_date", "00-00").split("-")[1])
                        if e.get("event_date") and "-" in e.get("event_date", "")
                        else 999,
                        -e.get("age", 0),
                    )
                )

                for ev in month_jubilees:
                    age = ev.get("age")
                    title = ev.get("title", "Без названия")

                    refs = ev.get("references", []) or []
                    ref_parts: list[str] = []
                    for r in refs:
                        rtype = r.get("reference_type")
                        rname = r.get("reference_name") or ""
                        ruuid = r.get("reference_uuid")
                        rslug = r.get("reference_slug")
                        if rtype == "author" and ruuid:
                            author_identifier = rslug if rslug else ruuid
                            url = f"https://example.com/authors/{author_identifier}"
                            ref_parts.append(f"<a href='{url}'>{rname}</a>")
                        elif rtype == "book" and rslug:
                            url = f"https://example.com/catalog/{rslug}"
                            ref_parts.append(f"<a href='{url}'>{rname}</a>")
                        else:
                            if rname:
                                ref_parts.append(rname)

                    refs_text = (" — " + ", ".join(ref_parts)) if ref_parts else ""
                    age_word = get_age_word(int(age)) if age is not None else "лет"
                    parts.append(f"• <b>{age} {age_word}</b> — {title}{refs_text}")

            if 0 in jubilees_by_month:
                parts.append("\n📅 <b>Без указания месяца</b>")
                for ev in jubilees_by_month[0]:
                    age = ev.get("age")
                    title = ev.get("title", "Без названия")

                    refs = ev.get("references", []) or []
                    ref_parts: list[str] = []
                    for r in refs:
                        rtype = r.get("reference_type")
                        rname = r.get("reference_name") or ""
                        ruuid = r.get("reference_uuid")
                        rslug = r.get("reference_slug")
                        if rtype == "author" and ruuid:
                            author_identifier = rslug if rslug else ruuid
                            url = f"https://example.com/authors/{author_identifier}"
                            ref_parts.append(f"<a href='{url}'>{rname}</a>")
                        elif rtype == "book" and rslug:
                            url = f"https://example.com/catalog/{rslug}"
                            ref_parts.append(f"<a href='{url}'>{rname}</a>")
                        else:
                            if rname:
                                ref_parts.append(rname)

                    refs_text = (" — " + ", ".join(ref_parts)) if ref_parts else ""
                    age_word = get_age_word(int(age)) if age is not None else "лет"
                    parts.append(f"• <b>{age} {age_word}</b> — {title}{refs_text}")

            message = "\n".join(parts)
            await self._bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        except Exception as e:
            logger.error("Ошибка при отправке юбиляров для %s: %s", year, e, exc_info=True)
            await self._bot.send_message(
                chat_id=chat_id,
                text="❌ Произошла ошибка при получении юбиляров. Попробуйте позже.",
                parse_mode="HTML",
            )

