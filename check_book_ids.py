import pandas as pd
import re

# Загружаем файл Excel
file_path = r'd:\svet\nebsvet 14.11.2025.xlsx'

# Функция для создания book_id из автора и названия
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

print(f"Проверка согласованности book_id на всех вкладках\n")
print(f"Найдено листов: {len(sheet_names)}\n")

# Собираем все пары автор+название и их book_id
all_books = {}  # (author, title) -> {sheet_name: book_id}

for sheet_name in sheet_names:
    print(f"Обработка листа: {sheet_name}")
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
    
    print(f"  Колонка автора: {author_col}")
    print(f"  Колонка названия: {title_col}")
    if book_id_col:
        print(f"  Колонка book_id: {book_id_col}")
    
    # Проверяем каждую строку
    for idx in df.index:
        author = str(df.at[idx, author_col]) if pd.notna(df.at[idx, author_col]) else ''
        title = str(df.at[idx, title_col]) if pd.notna(df.at[idx, title_col]) else ''
        
        if author and author != 'nan' and title and title != 'nan':
            # Создаем ключ для сравнения
            key = (author.strip(), title.strip())
            
            # Вычисляем ожидаемый book_id
            expected_id = create_book_id(author, title)
            
            # Получаем фактический book_id из файла
            actual_id = None
            if book_id_col:
                actual_id = str(df.at[idx, book_id_col]) if pd.notna(df.at[idx, book_id_col]) else None
                if actual_id == 'nan':
                    actual_id = None
            
            if key not in all_books:
                all_books[key] = {}
            
            all_books[key][sheet_name] = {
                'expected': expected_id,
                'actual': actual_id
            }
    
    print(f"  Обработано строк: {len(df)}\n")

# Проверяем согласованность
print("=" * 80)
print("АНАЛИЗ СОГЛАСОВАННОСТИ book_id\n")

inconsistent = []
consistent_count = 0

for (author, title), sheets_data in all_books.items():
    # Собираем все book_id для этой пары автор+название
    expected_ids = set()
    actual_ids = set()
    
    for sheet_name, data in sheets_data.items():
        if data['expected']:
            expected_ids.add(data['expected'])
        if data['actual']:
            actual_ids.add(data['actual'])
    
    # Проверяем, что все ожидаемые book_id одинаковые
    if len(expected_ids) == 1:
        expected_id = list(expected_ids)[0]
        
        # Проверяем, совпадают ли фактические book_id с ожидаемым
        if actual_ids:
            if len(actual_ids) == 1 and list(actual_ids)[0] == expected_id:
                consistent_count += 1
            else:
                inconsistent.append({
                    'author': author[:50],
                    'title': title[:50],
                    'expected': expected_id,
                    'actual': list(actual_ids),
                    'sheets': list(sheets_data.keys())
                })
        else:
            # book_id еще не создан
            consistent_count += 1
    else:
        # Разные ожидаемые book_id (не должно быть)
        inconsistent.append({
            'author': author[:50],
            'title': title[:50],
            'expected': list(expected_ids),
            'actual': list(actual_ids),
            'sheets': list(sheets_data.keys()),
            'note': 'РАЗНЫЕ ОЖИДАЕМЫЕ ID'
        })

print(f"Согласованных пар автор+название: {consistent_count}")
print(f"Несогласованных пар: {len(inconsistent)}\n")

if inconsistent:
    print("Примеры несогласованных записей (первые 10):")
    for i, item in enumerate(inconsistent[:10], 1):
        print(f"\n{i}. Автор: {item['author']}")
        print(f"   Название: {item['title']}")
        print(f"   Ожидаемый book_id: {item['expected']}")
        print(f"   Фактический book_id: {item['actual']}")
        print(f"   Вкладки: {', '.join(item['sheets'])}")
        if 'note' in item:
            print(f"   Примечание: {item['note']}")

print("\n" + "=" * 80)
print("\nВЫВОД:")
if len(inconsistent) == 0:
    print("OK: Все book_id согласованы! Одинаковые пары автор+название имеют одинаковый book_id на всех вкладках.")
else:
    print(f"ВНИМАНИЕ: Найдено {len(inconsistent)} несогласованных записей. Необходимо исправить.")

