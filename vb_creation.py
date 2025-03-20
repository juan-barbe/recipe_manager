import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

df = pd.read_csv('base_recetas_final.csv')

df['content'] = df.apply(
    lambda row: f"{row.Receta}. Score: {row.Score}. Dificultad: {row.Dificultad}. Ingredientes: {row.Ingredientes}. Nutrición: {row.Nutrición}", axis=1
)

client = chromadb.PersistentClient()

# Using sentence-transformers embedding
model_name = 'all-MiniLM-L6-v2'
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

collection = client.create_collection(name="thermomix_recipes_2", embedding_function=embedding_function)

collection.add(
    documents=df['content'].tolist(),
    ids=[str(i) for i in df.index])