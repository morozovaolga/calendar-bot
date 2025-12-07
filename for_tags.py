import pandas as pd

df = pd.read_excel("Для тегов.xlsx")
tag_cols = [f"Тэг{i}" for i in range(1, 14)]  # Тэг1, Тэг2, ..., Тэг13

# Расплавить + убрать пустые
tags_flat = df.melt(
    id_vars=["№"], 
    value_vars=tag_cols, 
    value_name="Тэг"
)["Тэг"].dropna()

# Убрать "—", пустые строки
tags_flat = tags_flat[~tags_flat.isin(['—', '–', '-', ''])]

# Считаем частоту
freq = tags_flat.value_counts().reset_index()
freq.columns = ["Тэг", "Частота"]
freq.to_excel("теги_частота.xlsx", index=False)