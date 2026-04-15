import os
import pandas as pd

def load_documents(folder_path="documents"):

    texts = []

    for file in os.listdir(folder_path):

        path = os.path.join(folder_path, file)

        # TXT
        if file.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                texts.append(f.read())

        # CSV
        elif file.endswith(".csv"):
            df = pd.read_csv(path)
            grouped = df.groupby('product')
            for product, group in grouped:
                product_text = f"Product: {product}\n"
                for _, row in group.iterrows():
                    section = row['section']
                    content = row['content']
                    product_text += f"{section}: {content}\n"
                texts.append(product_text)

    return texts

def chunk_text(text, chunk_size=500, overlap=50):

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks