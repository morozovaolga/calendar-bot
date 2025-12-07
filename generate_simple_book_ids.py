import pandas as pd
import re
from collections import defaultdict
from openpyxl import load_workbook

# Загружаем файл Excel
file_path = r'd:\svet\nebsvet 14.11.2025.xlsx'

def create_book_id(author, title):
    """Создает book_id из фамилии автора и первого слова названия"""
    if not author or author == 'nan' or not title or title == 'nan':
        return None
    
    # Извлекаем фамилию (первое слово из строки автора)
    author_parts = str(author).strip().split()
    if not author_parts:
        return None
    
    surname = author_parts[0]  # Фамилия - первое слово
    
    # Извлекаем первое слово из названия
    title_parts = str(title).strip().split()
    if not title_parts:
        return None
    first_word_title = title_parts[0]  # Первое слово названия
    
    # Очищаем от лишних символов (оставляем только буквы, цифры, дефисы)
    surname_clean = re.sub(r'[^\w-]', '', surname).strip()
    title_word_clean = re.sub(r'[^\w-]', '', first_word_title).strip()
    
    # Объединяем: фамилия_первое_слово_названия
    book_id_parts = [surname_clean, title_word_clean]
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

# Фильтруем только рабочие листы (без "Соответствие")
work_sheets = [s for s in sheet_names if s != 'Соответствие']

print(f"Генерация book_id (фамилия_первое_слово_названия)\n")
print(f"Найдено листов: {len(work_sheets)}\n")

# Собираем все книги из всех вкладок
all_books = []  # Список словарей с информацией о книгах

for sheet_name in work_sheets:
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

# Создаем book_id для всех книг
print("Создание book_id...\n")

book_id_mapping = {}  # индекс книги -> book_id

for i, book in enumerate(all_books):
    book_id = create_book_id(book['author'], book['title'])
    if book_id:
        book_id_mapping[i] = book_id

print(f"Создано book_id: {len(book_id_mapping)}\n")

# Обновляем book_id в исходном файле
print("Обновление book_id в исходном файле...\n")

wb_openpyxl = load_workbook(file_path)
dataframes = {}

for sheet_name in work_sheets:
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
            # Находим соответствующую строку в DataFrame
            for row_idx in df.index:
                author_val = str(df.at[row_idx, author_col]) if pd.notna(df.at[row_idx, author_col]) else ''
                title_val = str(df.at[row_idx, title_col]) if pd.notna(df.at[row_idx, title_col]) else ''
                if author_val == book['author'] and title_val == book['title']:
                    if i in book_id_mapping:
                        df.at[row_idx, book_id_col] = book_id_mapping[i]
                        updated_count += 1
                    break
    
    print(f"  Обновлено строк: {updated_count}")
    dataframes[sheet_name] = df

# Сохраняем обновленный файл
print("\nСохранение обновленного файла...")
try:
    # Пробуем режим append с заменой листов
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        for sheet_name in work_sheets:
            if sheet_name in dataframes:
                df = dataframes[sheet_name]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  Сохранен лист: {sheet_name}")
except Exception as e:
    print(f"  Ошибка при сохранении (возможно файл открыт): {e}")
    print("  Пожалуйста, закройте файл Excel и запустите скрипт снова")

# Создаем сводную таблицу наличия книг
print("\nСоздание сводной таблицы наличия книг...")

# Группируем по book_id
books_by_book_id = defaultdict(lambda: {sheet: False for sheet in work_sheets})
for i, book in enumerate(all_books):
    if i in book_id_mapping:
        book_id = book_id_mapping[i]
        books_by_book_id[book_id][book['sheet_name']] = True

# Создаем DataFrame для сводной таблицы
table_data = []
for book_id, presence in sorted(books_by_book_id.items()):
    row = {
        'book_id': book_id,
        work_sheets[0]: 'Да' if presence.get(work_sheets[0], False) else 'Нет',
        work_sheets[1]: 'Да' if presence.get(work_sheets[1], False) else 'Нет',
        work_sheets[2]: 'Да' if presence.get(work_sheets[2], False) else 'Нет'
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
for sheet_name in work_sheets:
    if sheet_name in result_df.columns:
        count = result_df[sheet_name].value_counts().get('Да', 0)
        print(f"  {sheet_name}: {count} книг")

print("\nГотово!")

