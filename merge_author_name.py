import pandas as pd

# Загружаем файл Excel
file_path = r'd:\svet\Для дозагрузки в список.xlsx'

print(f"Обработка файла: {file_path}\n")

# Читаем файл
df = pd.read_excel(file_path)

print(f"Колонки в файле: {list(df.columns)}\n")

# Ищем столбцы Author и Name
author_col = None
name_col = None

for col in df.columns:
    col_lower = str(col).lower()
    if col_lower == 'author' or 'автор' in col_lower:
        author_col = col
    if col_lower == 'name' or 'название' in col_lower or 'name' in col_lower:
        name_col = col

if not author_col:
    print("Ошибка: не найден столбец Author")
    exit(1)

if not name_col:
    print("Ошибка: не найден столбец Name")
    exit(1)

print(f"Найден столбец Author: {author_col}")
print(f"Найден столбец Name: {name_col}\n")

# Создаем новый столбец Author.Name
df['Author.Name'] = df[author_col].astype(str) + '.' + df[name_col].astype(str)

# Заменяем 'nan.nan' на пустую строку
df['Author.Name'] = df['Author.Name'].replace('nan.nan', '')

print(f"Создан новый столбец 'Author.Name'")
print(f"Количество строк: {len(df)}\n")

# Показываем первые несколько строк для проверки
print("Первые 5 строк нового столбца:")
print(df[['Author.Name']].head().to_string(index=False))

# Сохраняем файл
print(f"\nСохранение файла...")
try:
    df.to_excel(file_path, index=False)
    print(f"Файл сохранен: {file_path}")
except Exception as e:
    print(f"Ошибка при сохранении (возможно файл открыт): {e}")
    print("Пожалуйста, закройте файл Excel и запустите скрипт снова")

print("\nГотово!")

