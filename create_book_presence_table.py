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

print(f"Создание таблицы наличия книг на вкладках\n")
print(f"Найдено листов: {len(sheet_names)}\n")

# Словарь для хранения информации о наличии книг
# book_id -> {sheet_name: True/False}
books_presence = {}

# Обрабатываем каждую вкладку
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
    
    # Обрабатываем каждую строку
    for idx in df.index:
        author = str(df.at[idx, author_col]) if pd.notna(df.at[idx, author_col]) else ''
        title = str(df.at[idx, title_col]) if pd.notna(df.at[idx, title_col]) else ''
        
        if author and author != 'nan' and title and title != 'nan':
            # Получаем book_id из файла или создаем новый
            book_id = None
            if book_id_col:
                book_id = str(df.at[idx, book_id_col]) if pd.notna(df.at[idx, book_id_col]) else None
                if book_id == 'nan':
                    book_id = None
            
            # Если book_id нет в файле, создаем его
            if not book_id:
                book_id = create_book_id(author, title)
            
            if book_id:
                if book_id not in books_presence:
                    books_presence[book_id] = {}
                books_presence[book_id][sheet_name] = True
    
    print(f"  Обработано строк: {len(df)}\n")

# Создаем DataFrame для новой таблицы
print("Создание итоговой таблицы...")

# Подготавливаем данные
table_data = []
for book_id, presence in books_presence.items():
    row = {
        'book_id': book_id,
        sheet_names[0]: 'Да' if sheet_names[0] in presence else 'Нет',
        sheet_names[1]: 'Да' if sheet_names[1] in presence else 'Нет',
        sheet_names[2]: 'Да' if sheet_names[2] in presence else 'Нет'
    }
    table_data.append(row)

# Создаем DataFrame
result_df = pd.DataFrame(table_data)

# Сортируем по book_id
result_df = result_df.sort_values('book_id').reset_index(drop=True)

# Сохраняем в новый файл
output_file = r'd:\svet\таблица_наличия_книг.xlsx'
result_df.to_excel(output_file, index=False, sheet_name='Наличие книг')

print(f"\nТаблица сохранена в файл: {output_file}")
print(f"Всего уникальных book_id: {len(result_df)}")
print(f"\nПервые 10 строк таблицы:")
print(result_df.head(10).to_string(index=False))

# Статистика
print(f"\nСтатистика:")
for sheet_name in sheet_names:
    count = result_df[sheet_name].value_counts().get('Да', 0)
    print(f"  {sheet_name}: {count} книг")

