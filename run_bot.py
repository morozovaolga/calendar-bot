"""
Скрипт для запуска бота литературного календаря
С поддержкой команд и выбора даты через календарь
"""

import asyncio
import logging
import os
from datetime import datetime

from literary_calendar_bot import LiteraryCalendarBot
from telegram_calendar import TelegramCalendar
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotWithCommands:
    def __init__(self, bot_token: str, calendar_url: str, graphql_endpoint: str, timezone: str = "Europe/Moscow", send_hour: int = 9):
        self.literary_bot = LiteraryCalendarBot(
            bot_token=bot_token,
            calendar_url=calendar_url,
            graphql_endpoint=graphql_endpoint,
            timezone=timezone,
            send_hour=send_hour
        )
        self.app = Application.builder().token(bot_token).build()
        self.calendar_picker = TelegramCalendar()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "📚 Привет! Я бот литературного календаря сервиса «Свет».\n\n"
            "📌 Доступные команды:\n"
            "/send_events_for_today - События на сегодня\n"
            "/choose_date - Выбрать дату из календаря\n"
            "/help - Помощь"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
    📚 <b>Бот литературного календаря</b>

    <b>Команды:</b>
    /send_events_for_today — Получить события на сегодня
    /choose_date — Выбрать дату из календаря
    /help — Показать эту справку

    <b>Как использовать:</b>
    1. Отправьте /send_events_for_today для событий на сегодня
    2. Отправьте /choose_date для выбора любой даты
    3. Выберите дату в календаре — получите события

    <b>О боте:</b>
    Бот показывает литературные события: дни рождения писателей, даты публикаций знаменитых книг и другие памятные даты.
    Для каждого события предоставляются ссылки на книги в приложении «Свет».
    Вопросы и предложения: svet@rsl.ru
        """
        await update.message.reply_text(help_text, parse_mode='HTML')

    async def send_events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /send_events_for_today - отправляет события на сегодня"""
        chat_id = update.effective_chat.id
        
        await update.message.reply_text("🔍 Ищу события на сегодня...")
        await self.literary_bot.send_daily_digest(chat_id=str(chat_id))
        
        logger.info(f"Команда send_events_for_today выполнена для чата {chat_id}")

    async def choose_date_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /choose_date - показывает календарь"""
        calendar_keyboard = self.calendar_picker.create_calendar()
        
        await update.message.reply_text(
            "📅 Выберите дату:",
            reply_markup=calendar_keyboard
        )
        
        logger.info(f"Календарь показан для чата {update.effective_chat.id}")

    async def calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки календаря"""
        query = update.callback_query
        await query.answer()
        
        # Обрабатываем выбор
        selected, date, new_keyboard = self.calendar_picker.process_selection(query.data)
        
        if selected:
            # Дата выбрана - отправляем события
            chat_id = update.effective_chat.id
            
            # Удаляем календарь
            await query.edit_message_text(
                f"✅ Выбрана дата: {date.strftime('%d.%m.%Y')}\n"
                f"🔍 Ищу события..."
            )
            
            # Временно сохраняем выбранную дату в контексте бота
            # и получаем события на эту дату
            await self.send_events_for_date(chat_id, date)
            
        elif new_keyboard:
            # Обновляем календарь (переход между месяцами/годами)
            await query.edit_message_reply_markup(reply_markup=new_keyboard)

    async def send_events_for_date(self, chat_id: int, date: datetime):
        """
        Отправляет события на выбранную дату (из календаря)
        Использует обновлённую логику send_daily_digest из literary_calendar_bot
        
        Args:
            chat_id: ID чата
            date: Выбранная дата
        """
        try:
            # Получаем события на выбранную дату
            events = await self.literary_bot.get_events_by_date(date)
            
            if not events:
                date_str = date.strftime('%d %B %Y')
                await self.literary_bot.bot.send_message(
                    chat_id=chat_id,
                    text=f"📅 <b>{date_str}</b>\n\n"
                         f"На сегодня в календаре пока что нет событий.",
                    parse_mode='HTML'
                )
                return
            
            # Отправляем каждое событие отдельным сообщением (вариант А)
            for event in events:
                # Используем новую логику из send_daily_digest
                await self._send_event_with_media(chat_id, event)
                
        except Exception as e:
            logger.error(f"Ошибка отправки событий на дату {date}: {e}", exc_info=True)
            await self.literary_bot.bot.send_message(
                chat_id=chat_id,
                text="❌ Произошла ошибка при получении событий. Попробуйте позже.",
                parse_mode='HTML'
            )

    async def _send_event_with_media(self, chat_id: int, event: dict):
        """
        Отправляет одно событие с обложками (media_group) + текст
        (Логика из send_daily_digest в literary_calendar_bot)
        """
        books = []
        other_links = []
        
        # 1. Сначала добавляем книги из references БД (они уже есть)
        for book_ref in event.get('book_references', []):
            books.append({
                'uuid': book_ref['uuid'],
                'name': book_ref['name'],
                'slug': book_ref['slug'],
                'metadata': book_ref.get('metadata', {}),
                'source': 'database'
            })
            logger.debug(f"Добавлена книга из БД: {book_ref['name']}")
        
        # 2. Ищем книги по названию и автору из заголовка
        book_info = self.literary_bot.extract_book_info_from_title(event['title'])
        if book_info['book_title']:
            found_books = await self.literary_bot.search_books_by_title(
                book_info['book_title'], 
                book_info['author']
            )
            for book in found_books:
                # Избегаем дубликатов
                if not any(b.get('uuid') == book.get('uuid') for b in books):
                    books.append({
                        'uuid': book.get('uuid'),
                        'name': book.get('name', 'Без названия'),
                        'slug': book.get('slug', ''),
                        'metadata': {'image': book.get('image', {})},
                        'source': 'api_search'
                    })
                    logger.debug(f"Найдена книга по запросу: {book.get('name')}")
        
        # 3. Получаем книги по UUID авторов (и формируем ссылку на автора)
        for author_ref in event.get('author_refs', []):
            au_uuid = author_ref.get('uuid')
            au_name = author_ref.get('name') or ''
            # ссылка на поиск по автору на сайте
            author_url = f"https://example.com/catalog?authors={au_uuid}&page=1"
            other_links.append({'type': 'author', 'name': au_name or 'Автор', 'url': author_url})
            # получаем книги автора (для обложек)
            author_books = await self.literary_bot.get_books_by_author(au_uuid)
            for book in author_books:
                if not any(b.get('uuid') == book.get('uuid') for b in books):
                    books.append({
                        'uuid': book.get('uuid'),
                        'name': book.get('name', 'Без названия'),
                        'slug': book.get('slug', ''),
                        'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                        'source': 'author_api'
                    })
                    logger.debug(f"Найдена книга по автору: {book.get('name')}")
        
        # 4. Получаем книги по тегам (и формируем ссылки на теги)
        for tag_ref in event.get('tag_refs', []):
            tag_uuid = tag_ref.get('uuid')
            tag_name = tag_ref.get('name') or ''
            tag_url = f"https://example.com/catalog?tags={tag_uuid}&page=1"
            other_links.append({'type': 'tag', 'name': tag_name or 'Тег', 'url': tag_url})
            tag_books = await self.literary_bot.get_books_by_tag(tag_uuid)
            for book in tag_books:
                if not any(b.get('uuid') == book.get('uuid') for b in books):
                    books.append({
                        'uuid': book.get('uuid'),
                        'name': book.get('name', 'Без названия'),
                        'slug': book.get('slug', ''),
                        'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                        'source': 'tag_api'
                    })
                    logger.debug(f"Найдена книга по тегу: {book.get('name')}")
        
        # 5. Получаем книги по категориям
        for cat_ref in event.get('category_refs', []):
            cat_uuid = cat_ref.get('uuid')
            cat_name = cat_ref.get('name') or ''
            cat_url = f"https://example.com/catalog?categories={cat_uuid}&page=1"
            other_links.append({'type': 'category', 'name': cat_name or 'Категория', 'url': cat_url})
            cat_books = await self.literary_bot.get_books_by_category(cat_uuid)
            for book in cat_books:
                if not any(b.get('uuid') == book.get('uuid') for b in books):
                    books.append({
                        'uuid': book.get('uuid'),
                        'name': book.get('name', 'Без названия'),
                        'slug': book.get('slug', ''),
                        'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                        'source': 'category_api'
                    })
                    logger.debug(f"Найдена книга по категории: {book.get('name')}")
        
        # 5. Если нет ни одной ссылки - генерируем поиск по названию события
        if not other_links and not books:
            # Генерируем URL для поиска по названию события
            event_title_clean = event['title'].strip()
            search_url = f"https://example.com/catalog?search={event_title_clean.replace(' ', '+')}&page=1"
            other_links.append({'type': 'search', 'name': event_title_clean, 'url': search_url})
            logger.debug(f"Сгенерирована ссылка поиска для события: {event_title_clean}")
            
            # Пытаемся найти книги по названию события через API
            search_books = await self.literary_bot.search_books_by_title(event_title_clean)
            for book in search_books[:10]:  # берём до 10 книг
                if not any(b.get('uuid') == book.get('uuid') for b in books):
                    books.append({
                        'uuid': book.get('uuid'),
                        'name': book.get('name', 'Без названия'),
                        'slug': book.get('slug', ''),
                        'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                        'source': 'auto_search'
                    })
                    logger.debug(f"Найдена книга по названию события: {book.get('name')}")
        
        # Формируем и отправляем медиа (обложки) + текст
        # Сначала собираем доступные обложки — но не больше 6
        media_items = []
        logger.info(f"Событие '{event['title']}': найдено {len(books)} книг")
        for idx, book in enumerate(books):
            if len(media_items) >= 6:
                logger.debug(f"Лимит обложек достигнут (6), остановка")
                break
            metadata = book.get('metadata', {}) or {}
            logger.debug(f"  Книга {idx+1}: {book.get('name')} (metadata={bool(metadata)})")
            image_data = metadata.get('image', {}) or {}
            image_url = ''
            if isinstance(image_data, dict):
                image_url = image_data.get('url', '')
            elif isinstance(image_data, str):
                image_url = image_data

            logger.debug(f"    image_data type: {type(image_data)}, url={image_url[:50] if image_url else 'нет'}")
            if image_url:
                # Ссылка на карточку книги (если есть slug)
                book_slug = book.get('slug', '')
                if book_slug:
                    book_url = f"https://example.com/catalog/{book_slug}"
                else:
                    book_url = ''

                # подпись под изображением — название (ссылка если есть)
                caption = book.get('name', '')
                if book_url:
                    caption = f"<a href='{book_url}'>{caption}</a>"

                try:
                    media_items.append(InputMediaPhoto(media=image_url, caption=caption))
                except Exception as e:
                    logger.debug(f"Невозможно создать InputMediaPhoto для {image_url}: {e}")

        # Если есть медиа — отправляем группу
        if media_items:
            try:
                # Telegram принимает до 10 медиа в группе, мы посылаем не больше 6
                await self.literary_bot.bot.send_media_group(chat_id=chat_id, media=media_items[:6])
                await asyncio.sleep(0.5)
            except TelegramError as e:
                logger.warning(f"Не удалось отправить media_group: {e}")

            # После отправки картинок отправляем текст без явных URL обложек и без предпросмотра
            message = self.literary_bot.format_event_message(event, books, include_image_urls=False, other_links=other_links)
            disable_preview = True
        else:
            # Если обложек нет — отправляем обычное текстовое сообщение (с URL обложек если они есть в metadata)
            message = self.literary_bot.format_event_message(event, books, include_image_urls=True, other_links=other_links)
            disable_preview = False

        try:
            await self.literary_bot.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=disable_preview
            )
            logger.info(f"Отправлено событие: {event['title']} (книг: {len(books)})")
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    async def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("send_events_for_today", self.send_events_command))
        self.app.add_handler(CommandHandler("choose_date", self.choose_date_command))
        
        # Обработчик для календаря
        self.app.add_handler(CallbackQueryHandler(self.calendar_callback, pattern='^cal_'))

    async def run_polling(self):
        """Запуск бота в режиме polling с корректной работой с python-telegram-bot v20"""
        await self.setup_handlers()
        print("🤖 Бот запущен в режиме polling")
        print("📚 Доступные команды:")
        print("   /start - Начать работу")
        print("   /send_events_for_today - События на сегодня")
        print("   /choose_date - Выбрать дату")
        print("   /help - Помощь")
        
        # Инициализируем приложение
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        try:
            # Держим бота запущенным
            await asyncio.Event().wait()
        finally:
            # Корректное завершение
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()


async def main():
    """Главная функция запуска бота"""
    
    # Загрузка конфигурации
    bot_token = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    graphql_endpoint = os.getenv('GRAPHQL_ENDPOINT', 'https://example.com/graphql')
    calendar_url = os.getenv('CALENDAR_URL', 'https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90')
    timezone = os.getenv('TIMEZONE', 'Europe/Moscow')
    send_hour = int(os.getenv('SEND_HOUR', '9'))

    # Если параметры - placeholder, пробуем загрузить из конфига
    if "YOUR_BOT_TOKEN_HERE" in bot_token:
        try:
            import literary_calendar_bot_config as config
            bot_token = getattr(config, 'BOT_TOKEN', bot_token)
            graphql_endpoint = getattr(config, 'GRAPHQL_ENDPOINT', graphql_endpoint)
            calendar_url = getattr(config, 'CALENDAR_URL', calendar_url)
            timezone = getattr(config, 'TIMEZONE', timezone)
            send_hour = getattr(config, 'SEND_HOUR', send_hour)
        except ImportError:
            pass

    # Проверяем конфигурацию
    if not bot_token or "YOUR_BOT_TOKEN_HERE" in bot_token:
        print("⚠️  Предупреждение: BOT_TOKEN не настроен!")
        print("   Получите токен у @BotFather в Telegram")
        print("   Установите переменную окружения: export BOT_TOKEN='ваш_токен'")
        return
    
    if not graphql_endpoint:
        print("⚠️  Предупреждение: GRAPHQL_ENDPOINT не настроен!")
        print("   Установите переменную окружения: export GRAPHQL_ENDPOINT='ваш_api_url'")
        return
    
    # Создаем бота с поддержкой команд
    bot_with_commands = BotWithCommands(
        bot_token=bot_token,
        calendar_url=calendar_url,
        graphql_endpoint=graphql_endpoint,
        timezone=timezone,
        send_hour=send_hour
    )
    
    print("✅ Бот инициализирован")
    print(f"🔗 API: {graphql_endpoint}")
    print("\n" + "="*50)
    print("🚀 Запуск бота с поддержкой команд и календаря")
    print("="*50)
    
    await bot_with_commands.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте логи выше для деталей")