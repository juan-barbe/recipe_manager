import streamlit as st
import requests
import pandas as pd
import json
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool

import os
os.environ["OPENAI_API_KEY"] = '***'
os.environ["SERPER_API_KEY"] = '****'
# -----------------------------------------------------
# Groceries Inventory Manager (from base_front.py)
# -----------------------------------------------------
def groceries_inventory():
    st.title("Groceries Inventory Manager")
    BASE_URL = "http://localhost:5000"  # Adjust if needed

    operation = st.selectbox(
        "Select Operation",
        ["Add", "Update", "Delete", "Show Inventory", "Consumption"]
    )

    item_name = None
    quantity = None
    unit = None

    if operation == "Add":
        st.subheader("Add a New Item")
        item_name = st.text_input("New Item Name")
        quantity = st.number_input("Quantity", min_value=0, step=1, value=0)
        unit = st.selectbox("Unit Type", ["units", "grams"])
    elif operation == "Show Inventory":
        st.subheader("Show Current Inventory")
    else:
        st.subheader(f"{operation} an Existing Item")
        try:
            all_items = requests.get(f"{BASE_URL}/groceries").json()
        except Exception as e:
            st.error(f"Failed to fetch items from the server: {e}")
            st.stop()

        if not all_items:
            st.warning("No items found in the inventory.")
            st.stop()
        else:
            item_names = [g["item"] for g in all_items]
            item_name = st.selectbox("Select an existing item", item_names)

            if operation in ["Update", "Consumption"]:
                quantity = st.number_input("Quantity", min_value=0, step=1, value=0)

            if operation == "Update":
                unit = st.selectbox("Unit Type", ["units", "grams"])

    if st.button("Ok"):
        if operation == "Show Inventory":
            try:
                all_groceries = requests.get(f"{BASE_URL}/groceries").json()
                if not all_groceries:
                    st.info("No items in the inventory yet!")
                else:
                    df = pd.DataFrame(all_groceries)
                    st.table(df)
            except Exception as e:
                st.error(f"Failed to fetch inventory: {e}")

        elif operation == "Add":
            if not item_name:
                st.warning("Please enter an item name.")
            else:
                payload = {"item": item_name, "quantity": quantity, "unit": unit}
                try:
                    response = requests.post(f"{BASE_URL}/groceries", json=payload)
                    if response.status_code == 201:
                        st.success("Item added successfully!")
                    else:
                        st.error(f"Error adding item: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

        elif operation in ["Update", "Consumption", "Delete"]:
            matched_item = next((g for g in all_items if g["item"] == item_name), None)
            if not matched_item:
                st.warning(f"No item found with name '{item_name}'.")
                st.stop()
            grocery_id = matched_item["id"]

            if operation == "Update":
                payload = {"item": item_name, "quantity": quantity, "unit": unit}
                try:
                    response = requests.put(f"{BASE_URL}/groceries/{grocery_id}", json=payload)
                    if response.status_code == 200:
                        st.success("Item updated successfully!")
                    else:
                        st.error(f"Error updating item: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

            elif operation == "Consumption":
                current_quantity = matched_item["quantity"]
                new_quantity = current_quantity - quantity
                if new_quantity < 0:
                    new_quantity = 0  # Clamp to 0
                updated_payload = {
                    "item": matched_item["item"],
                    "quantity": new_quantity,
                    "unit": matched_item["unit"]
                }
                try:
                    response = requests.put(f"{BASE_URL}/groceries/{grocery_id}", json=updated_payload)
                    if response.status_code == 200:
                        st.success(f"Consumed {quantity} of '{item_name}'. New quantity = {new_quantity}")
                    else:
                        st.error(f"Error consuming item: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

            elif operation == "Delete":
                try:
                    response = requests.delete(f"{BASE_URL}/groceries/{grocery_id}")
                    if response.status_code == 200:
                        st.success("Item deleted successfully!")
                    else:
                        st.error(f"Error deleting item: {response.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")

# -----------------------------------------------------
# Thermomix Recipes Query (from recipe_query.py)
# -----------------------------------------------------
@st.cache_resource
def get_collection():
    OPENAI_API_KEY = ('sk-proj-k9HpVEJk7sQsSl1fVyxjMtx3Wnb-c_q8_GisuHi0p-9O2D7yxEjxg5YQopS-zVewLVqJRMbvllT3BlbkFJ3HLkUhU'
                      'wAxeNlnKnLNxAE9zyE_0sIVZ2VcGSqIjeRxMc3wUKAqNv5GcJy51dYQvE-VVW0NSZEA')  # Replace with your OpenAI API key
    client_openai = OpenAI(api_key=OPENAI_API_KEY)
    client_chroma = chromadb.PersistentClient()
    model_name = 'all-MiniLM-L6-v2'
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    collection_name = "thermomix_recipes_2"
    collection = client_chroma.get_collection(name=collection_name, embedding_function=embedding_function)
    return collection, client_openai

def retrieve_recipes(query, collection, top_k=5):
    results = collection.query(query_texts=[query], n_results=top_k)
    return results['documents'][0] if results.get('documents') else []

def ask_gpt(query, retrieved_docs, client_openai):
    context = "\n\n".join(retrieved_docs)
    prompt = f"""
Eres un experto dando información sobre recetas de Thermomix. Siempre al dar una receta debes dar la lista completa de ingredientes, la cantidad y también el valor nutricional.
Usa el siguiente contexto de recetas Thermomix para responder la pregunta del usuario brevemente. Si no tienes la respuesta dentro del Contexto
Responde que la receta "NO" es parte de la base de Thermomix. Debes siempre dejar eso claro si la receta no está en el contexto.
Usa siempre el siguiente formato:
Nombre de Receta

Ingredientes

Valor Nutricional

Contexto:
{context}

Pregunta del usuario:
"{query}"

Respuesta útil y breve:
    """
    response = client_openai.chat.completions.create(
        model="o3-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def rag_query(query, collection, client_openai):
    retrieved_docs = retrieve_recipes(query, collection, top_k=5)
    return ask_gpt(query, retrieved_docs, client_openai)

# -----------------------------------------------------
# CrewAI Agent for Comparing Ingredients
# -----------------------------------------------------
def analyze_missing_ingredients(recipe_answer):
    try:
        with open('groceries.json', 'r', encoding='utf-8') as file:
            groceries = json.load(file)
    except Exception as e:
        return f"Error loading groceries data: {e}"

    prompt = f"""
Dada la receta:
{recipe_answer}

y el siguiente inventario:
{json.dumps(groceries, ensure_ascii=False, indent=2)}

Analiza la receta y determina qué ingredientes faltan y en qué cantidades para poder hacerla. Devuelve la respuesta como una lista en bullet points, indicando el nombre del ingrediente y la cantidad faltante.
    """

    inventory_analyst = Agent(
        name="Inventory_Analyst",
        role="Analyst",
        goal="Analizar los ingredientes de la receta y compararlos con el inventario para determinar qué ingredientes faltan.",
        backstory="Experto en análisis de recetas y comparación de inventario.",
        verbose=True
    )
    inventory_analysis = Task(
        description=prompt,
        expected_output="Una lista en bullet points con los ingredientes y las cantidades faltantes.",
        agent=inventory_analyst,
        verbose=True
    )
    crew = Crew(
        agents=[inventory_analyst],
        tasks=[inventory_analysis],
        process=Process.sequential,
        verbose=True
    )
    result = crew.kickoff()
    return result.raw

# -----------------------------------------------------
# CrewAI Agent for Searching Supermarkets
# -----------------------------------------------------
def search_supermarkets(missing_ingredients):
    supermarket_agent = Agent(
        name="Supermarket_Searcher",
        role="Researcher",
        goal="Buscar en la web enlaces de supermercados para cada ingrediente faltante.",
        backstory="Experto en búsquedas web y comparación de precios en supermercados.",
        tools=[WebsiteSearchTool(),SerperDevTool()]
    )
    supermarket_task = Task(
        description=f"""
                    Dado el siguiente listado de ingredientes faltantes:
                    {missing_ingredients}

                    Busca los ingredientes en https://www.tiendainglesa.com.uy/. Si no encuentras el ingrendiente puntual faltante busca similares. 
                    En este casos debes dejar en claro que estás haciendo eso.
                    Devuelve una lista en bullet points en la que cada línea contenga el nombre del ingrediente y el enlace para comprarlo.""",
        expected_output="Una lista en bullet points con el nombre del ingrediente, la cantidad a comprar y el enlace de compra.",
        agent=supermarket_agent,
        tools=[WebsiteSearchTool(),SerperDevTool()]
    )
    crew = Crew(
        agents=[supermarket_agent],
        tasks=[supermarket_task],
        process=Process.sequential
    )
    result = crew.kickoff()
    return result.raw
# -----------------------------------------------------
# Unified App: Combining Both Tools
# -----------------------------------------------------
def recipe_query_app():
    st.title("Consulta de Recetas Thermomix")
    st.write("Haz una pregunta sobre la base de recetas y obtén una respuesta")

    collection, client_openai = get_collection()
    user_query = st.text_input("Ingresa tu pregunta sobre recetas:")

    if st.button("Consultar"):
        if not user_query.strip():
            st.warning("Por favor ingresa una pregunta válida.")
        else:
            with st.spinner("Recuperando información..."):
                recipe_answer = rag_query(user_query, collection, client_openai)
            st.markdown("**Respuesta de la Receta:**")
            st.write(recipe_answer)
            st.session_state.recipe_answer = recipe_answer

            try:
                with open('groceries.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                df = pd.DataFrame(data)
                st.markdown("**Ingredientes Disponibles (Inventario):**")
                st.write(df)
            except Exception as e:
                st.error("Error loading ingredients data.")

    if "recipe_answer" in st.session_state:
        with st.spinner("Analizando ingredientes..."):
            missing = analyze_missing_ingredients(st.session_state.recipe_answer)
            st.session_state.missing = missing

    if "missing" in st.session_state:
        st.markdown("**Ingredientes Faltantes:**")
        st.write(st.session_state.missing)

        if st.button("Buscar en Supermercados"):
            with st.spinner("Buscando enlaces en supermercados..."):
                links = search_supermarkets(st.session_state.missing)
                st.session_state.supermarket_links = links

    if "supermarket_links" in st.session_state:
        st.markdown("**Enlaces de Supermercados:**")
        st.write(st.session_state.supermarket_links)

# -----------------------------------------------------
# Main App with Sidebar Menu
# -----------------------------------------------------
def main():
    st.sidebar.title("Menu")
    app_mode = st.sidebar.selectbox(
        "Choose the App",
        ["Groceries Inventory Manager", "Thermomix Recipes"]
    )
    if app_mode == "Groceries Inventory Manager":
        groceries_inventory()
    elif app_mode == "Thermomix Recipes":
        recipe_query_app()

if __name__ == "__main__":
    main()
