# recipe_manager
Recipe App Project from Stanford LLM's Course

**Context and Motivation**
Current Thermomix app (https://www.thermomix.com/) lacks the ability for users to interact naturally and intelligently with their recipes. They have no AI features in their app (cookidoo) 
The idea is to create an AI App that enhances Thermomix cooking by integrating AI assistance with a household ingredient inventory management capability. Using LLM's, users can interact naturally, asking recipe-related questions and receiving personalized suggestions based on actual available Thermomix recipes. The app tracks available ingredients in your houshold and generates automatic grocery lists for missing Ingredients, simplifying meal planning, reducing food waste and making smarter and healthier decisions. 
I would like to search the Spanish Recipes Database with queries like: "Show me recipes with a nutritional value between 10 and 30 grams of Protein with Fish and Onions as Ingredients"


**Solution**
The implementation implied Multiple different Parts
For the Thermomix Recipe Query I had to:
1) Spanish Recipe Web Scraping from Cookidoo Website: As there are no official Cookidoo API's or datasets with recipes I needed to do a Webscrapping using Selenium Webdriver
2) Generate a Vector Base for searching with RAG: After the Dataset with Recipes was gathered, I created a local Vector Base with ChromaDB
3) Generate a UI with Streamlit to query the VB vía RAG. For this I used OpenAI API

For the Inventory Management I created a Flash Script that generated a json file and let the user:
1) Add new Items to the inventory
2) Edit Items in the inventory
3) Register consumption, so as to reduce stock in the inventory
4) Delete items
5) And a "show inventory" function


Finally, I used CrewAI agents to:
1) Identify which are the missing ingredients in the inventory to make the Searched Thermomix Recipe
2) Search the internet and provide Links for this ingredientes from a Supermarket, in order to Buy them
[This last part is requiring more work to make sure the links are correct. Ideally there would be a public API of a Supermarket to let me create a Cart. But I havent find something like that for Uruguay)
