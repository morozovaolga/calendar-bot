import pandas as pd
import re
from collections import defaultdict
from openpyxl import load_workbook

# Загружаем файл Excel
file_path = r'd:\svet\nebsvet 14.11.2025.xlsx'

def clean_word(word):
    """Очищает слово от лишних символов"""
    return re.sub(r'[^\w-]', '', word).strip()

def create_base_book_id(author, title, max_words=1):
    """Создает базовый book_id из фамилии автора и первых max_words слов названия"""
    if not author or author == 'nan' or not title or title == 'nan':
        return None
    
    # Извлекаем фамилию (первое слово из строки автора)
    author_parts = str(author).strip().split()
    if not author_parts:
        return None
    
    surname = author_parts[0]  # Фамилия - первое слово
    surname_clean = clean_word(surname)
    
    # Извлекаем слова из названия
    title_parts = str(title).strip().split()
    if not title_parts:
        return None
    
    # Берем первые max_words слов из названия
    title_words = []
    for i in range(min(max_words, len(title_parts))):
        word_clean = clean_word(title_parts[i])
        if word_clean:
            title_words.append(word_clean)
    
    if not title_words:
        return None
    
    # Объединяем: фамилия_слова_названия
    book_id_parts = [surname_clean] + title_words
    book_id_parts = [p for p in book_id_parts if p]  # Убираем пустые части
    
    if not book_id_parts:
        return None
    
    book_id = '_'.join(book_id_parts)
    # Приводим к нижнему регистру и заменяем ё на е
    book_id = book_id.lower().replace('ё', 'е')
    return book_id

# Загружаем workbook
wb = pd.ExcelFile(file_path)
sheet_names = wb.sheet_names

print(f"Генерация book_id с обработкой дубликатов\n")
print(f"Найдено листов: {len(sheet_names)}\n")

# Собираем все книги из всех вкладок
all_books = []  # Список словарей с информацией о книгах

for sheet_name in sheet_names:
    print(f"Обработка листа: {sheet_name}")
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Ищем колонки
    author_col = None
    title_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'автор' in col_lower or 'author' in col_lower:
            author_col = col
        if 'название' in col_lower or 'title' in col_lower or 'назв' in col_lower or col_lower == 'name':
            title_col = col
    
    if not author_col or not title_col:
        print(f"  Пропущен (нет нужных колонок)")
        continue
    
    print(f"  Колонка автора: {author_col}")
    print(f"  Колонка названия: {title_col}")
    
    # Обрабатываем каждую строку
    for idx in df.index:
        author = str(df.at[idx, author_col]) if pd.notna(df.at[idx, author_col]) else ''
        title = str(df.at[idx, title_col]) if pd.notna(df.at[idx, title_col]) else ''
        
        if author and author != 'nan' and title and title != 'nan':
            all_books.append({
                'sheet_name': sheet_name,
                'row_idx': idx,
                'author': author,
                'title': title,
                'author_col': author_col,
                'title_col': title_col
            })
    
    print(f"  Обработано строк: {len(df)}\n")

print(f"Всего собрано книг: {len(all_books)}\n")

# Определяем максимальное количество слов в названиях
max_title_words = 0
for book in all_books:
    title_parts = str(book['title']).strip().split()
    max_title_words = max(max_title_words, len(title_parts))

print(f"Максимальное количество слов в названиях: {max_title_words}\n")

# Группируем книги по базовому ключу (автор + название)
books_by_key = defaultdict(list)
for i, book in enumerate(all_books):
    key = (book['author'].strip().lower(), book['title'].strip().lower())
    books_by_key[key].append((i, book))

print(f"Уникальных пар автор+название: {len(books_by_key)}\n")

# Создаем book_id с обработкой дубликатов
print("Создание book_id с обработкой дубликатов...\n")

# Словарь для отслеживания использованных book_id
used_book_ids = defaultdict(int)  # book_id -> количество использований
final_book_ids = {}  # индекс книги -> финальный book_id

# Обрабатываем каждую группу книг
for key, books_list in books_by_key.items():
    author, title = key
    
    # Пробуем создать уникальные book_id для всех книг в группе
    if len(books_list) == 1:
        # Одна книга - просто создаем book_id
        idx, book = books_list[0]
        # Пробуем с разным количеством слов
        book_id = None
        for words_count in range(1, max_title_words + 1):
            book_id = create_base_book_id(book['author'], book['title'], words_count)
            if book_id and used_book_ids[book_id] == 0:
                break
        
        if not book_id:
            book_id = create_base_book_id(book['author'], book['title'], 1)
        
        if book_id:
            used_book_ids[book_id] += 1
            final_book_ids[idx] = book_id
    else:
        # Несколько книг с одинаковым автором и названием
        # Сначала пробуем создать разные book_id добавляя слова
        temp_book_ids = {}
        for idx, book in books_list:
            book_id = None
            for words_count in range(1, max_title_words + 1):
                book_id = create_base_book_id(book['author'], book['title'], words_count)
                if book_id and book_id not in temp_book_ids.values():
                    temp_book_ids[idx] = book_id
                    break
            
            if idx not in temp_book_ids:
                # Если не удалось создать уникальный, используем базовый
                book_id = create_base_book_id(book['author'], book['title'], 1)
                temp_book_ids[idx] = book_id
        
        # Проверяем, есть ли дубликаты среди созданных book_id
        book_id_counts = defaultdict(list)
        for idx, book_id in temp_book_ids.items():
            book_id_counts[book_id].append(idx)
        
        # Обрабатываем дубликаты - добавляем суффиксы _1, _2 и т.д.
        for book_id, indices in book_id_counts.items():
            if len(indices) == 1:
                # Уникальный book_id
                final_book_ids[indices[0]] = book_id
                used_book_ids[book_id] += 1
            else:
                # Есть дубликаты - добавляем суффиксы
                for i, idx in enumerate(indices, start=1):
                    final_book_id = f"{book_id}_{i}"
                    final_book_ids[idx] = final_book_id
                    used_book_ids[final_book_id] += 1

print(f"Создано уникальных book_id: {len(set(final_book_ids.values()))}\n")

# Обновляем book_id в исходном файле
print("Обновление book_id в исходном файле...\n")

wb_openpyxl = load_workbook(file_path)
dataframes = {}

for sheet_name in sheet_names:
    print(f"Обновление листа: {sheet_name}")
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Ищем колонки
    author_col = None
    title_col = None
    book_id_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'автор' in col_lower or 'author' in col_lower:
            author_col = col
        if 'название' in col_lower or 'title' in col_lower or 'назв' in col_lower or col_lower == 'name':
            title_col = col
        if 'book_id' in col_lower or 'bookid' in col_lower:
            book_id_col = col
    
    if not author_col or not title_col:
        print(f"  Пропущен (нет нужных колонок)")
        continue
    
    # Создаем или находим колонку book_id
    if book_id_col is None:
        book_id_col = 'book_id'
        df[book_id_col] = ''
    
    # Обновляем book_id для всех книг из этого листа
    updated_count = 0
    for i, book in enumerate(all_books):
        if book['sheet_name'] == sheet_name:
            idx = None
            for j, row_idx in enumerate(df.index):
                author_val = str(df.at[row_idx, author_col]) if pd.notna(df.at[row_idx, author_col]) else ''
                title_val = str(df.at[row_idx, title_col]) if pd.notna(df.at[row_idx, title_col]) else ''
                if author_val == book['author'] and title_val == book['title']:
                    idx = row_idx
                    break
            
            if idx is not None and i in final_book_ids:
                df.at[idx, book_id_col] = final_book_ids[i]
                updated_count += 1
    
    print(f"  Обновлено строк: {updated_count}")
    dataframes[sheet_name] = df

# Сохраняем обновленный файл
print("\nСохранение обновленного файла...")
with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
    for sheet_name, df in dataframes.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"  Сохранен лист: {sheet_name}")

# Создаем сводную таблицу наличия книг
print("\nСоздание сводной таблицы наличия книг...")

# Группируем по book_id
books_by_book_id = defaultdict(lambda: {sheet: False for sheet in sheet_names})
for i, book in enumerate(all_books):
    if i in final_book_ids:
        book_id = final_book_ids[i]
        books_by_book_id[book_id][book['sheet_name']] = True

# Создаем DataFrame для сводной таблицы
table_data = []
for book_id, presence in sorted(books_by_book_id.items()):
    row = {
        'book_id': book_id,
        sheet_names[0]: 'Да' if presence.get(sheet_names[0], False) else 'Нет',
        sheet_names[1]: 'Да' if presence.get(sheet_names[1], False) else 'Нет',
        sheet_names[2]: 'Да' if presence.get(sheet_names[2], False) else 'Нет'
    }
    table_data.append(row)

result_df = pd.DataFrame(table_data)

# Сохраняем в файл с вкладкой "Соответствие"
output_file = r'd:\svet\таблица_наличия_книг.xlsx'
print(f"\nСохранение сводной таблицы в файл: {output_file}")

# Загружаем существующий файл или создаем новый
try:
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        result_df.to_excel(writer, sheet_name='Соответствие', index=False)
except:
    # Если файла нет или ошибка, создаем новый
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='w') as writer:
        result_df.to_excel(writer, sheet_name='Соответствие', index=False)

print(f"  Сохранена вкладка: Соответствие")
print(f"\nВсего уникальных book_id: {len(result_df)}")
print(f"\nПервые 10 строк таблицы:")
print(result_df.head(10).to_string(index=False))

# Статистика
print(f"\nСтатистика:")
# Используем только первые 3 листа (без "Соответствие")
for sheet_name in sheet_names[:3]:
    if sheet_name in result_df.columns:
        count = result_df[sheet_name].value_counts().get('Да', 0)
        print(f"  {sheet_name}: {count} книг")

print("\nГотово!")

