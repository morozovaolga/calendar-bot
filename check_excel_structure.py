import pandas as pd

df = pd.read_excel("Для тегов.xlsx")
print("Столбцы в файле:")
print(list(df.columns))
print(f"\nКоличество строк: {len(df)}")
print(f"\nПервые несколько строк:")
print(df.head())



