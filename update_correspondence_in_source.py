import pandas as pd
from collections import defaultdict

# Загружаем файл Excel
file_path = r'd:\svet\nebsvet 14.11.2025.xlsx'

# Загружаем workbook
wb = pd.ExcelFile(file_path)
sheet_names = wb.sheet_names

# Фильтруем только рабочие листы (без "Соответствие")
work_sheets = [s for s in sheet_names if s != 'Соответствие']

print(f"Обновление вкладки 'Соответствие' в файле {file_path}\n")
print(f"Найдено листов: {len(work_sheets)}\n")

# Собираем информацию о наличии книг по book_id
books_by_book_id = defaultdict(lambda: {sheet: False for sheet in work_sheets})

for sheet_name in work_sheets:
    print(f"Обработка листа: {sheet_name}")
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Ищем колонку book_id
    book_id_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if 'book_id' in col_lower or 'bookid' in col_lower:
            book_id_col = col
            break
    
    if not book_id_col:
        print(f"  Пропущен (нет колонки book_id)")
        continue
    
    print(f"  Колонка book_id: {book_id_col}")
    
    # Обрабатываем каждую строку
    count = 0
    for idx in df.index:
        book_id = str(df.at[idx, book_id_col]) if pd.notna(df.at[idx, book_id_col]) else ''
        
        if book_id and book_id != 'nan' and book_id.strip():
            books_by_book_id[book_id.strip()][sheet_name] = True
            count += 1
    
    print(f"  Обработано строк с book_id: {count}\n")

# Создаем DataFrame для сводной таблицы
print("Создание сводной таблицы...")

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

# Сохраняем в исходный файл с вкладкой "Соответствие"
print(f"\nСохранение сводной таблицы в файл: {file_path}")

try:
    # Пробуем режим append с заменой листов
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        result_df.to_excel(writer, sheet_name='Соответствие', index=False)
        print(f"  Обновлена вкладка: Соответствие")
except Exception as e:
    print(f"  Ошибка при сохранении (возможно файл открыт): {e}")
    print("  Пожалуйста, закройте файл Excel и запустите скрипт снова")

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

