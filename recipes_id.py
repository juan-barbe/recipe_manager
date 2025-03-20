from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd

# Set up Chrome in headless mode
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # Newer headless mode (harder to detect)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass detection
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# Install and start ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

recetas = []
for i in range(1,20):
    url = f"https://cookidoo.es/search/es-ES?context=recipes&sortby=relevance&accessories=includingFriend,includingBladeCoverWithPeeler,includingCutter&languages=es&ratings=5,4&tmv=TM6&countries=es&difficulty=advanced&page=3&page={i}"  # Replace with your target URL
    driver.get(url)
    driver.implicitly_wait(3)
    recipe_elements = driver.find_elements(By.CLASS_NAME, "core-tile--expanded")
    global recipe_id
    for element in recipe_elements:
        recipe_id = element.get_attribute("id")
        recetas.append(recipe_id)
    if recipe_id is None:
        break

    print(f"Scraped Page {i} - Found {len(recetas)} recipes.")



# Close the browser
driver.quit()
df = pd.DataFrame(recetas, columns=["RecipeID"])
df.drop_duplicates(inplace=True)
print(df.RecipeID.nunique())
df.to_csv('pruebas_recetas_9.csv',index=False)