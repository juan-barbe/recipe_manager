import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome in headless mode with options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Example: list of Recipe IDs from a CSV
df = pd.read_csv('df_final.csv')

# Initialize lists to store scraped data
receta_list   = []
score_list    = []
score_qty_list = []
info_list     = []
info_2_list   = []
info_3_list   = []
info_4_list   = []
ing_list      = []
nutri_list    = []

# Function to save current progress to CSV
def save_progress():
    df_recetas = pd.DataFrame({
        'Receta': receta_list,
        'Score': score_list,
        'Quantity Score': score_qty_list,
        'Dificultad': info_list,
        'Tiempo Preparación': info_2_list,
        'Tiempo Total': info_3_list,
        'Cantidades': info_4_list,
        'Ingredientes': ing_list,
        'Nutrición': nutri_list
    })
    backup_filename = 'base_recetas_backup.csv'
    df_recetas.to_csv(backup_filename, index=False, encoding="utf-8")
    print(f"Backup saved: {len(receta_list)} recipes processed (saved to '{backup_filename}').")

# Loop through each RecipeID from the CSV
for count, recipe_id in enumerate(df.RecipeID, start=1):
    url = f"https://cookidoo.es/recipes/recipe/es-ES/{recipe_id}"
    try:
        driver.get(url)
        driver.implicitly_wait(1)  # Briefly wait for elements to load
    except Exception as e:
        print(f"Error loading URL {url}: {e}")
        # Append default values if page fails to load
        receta_list.append("")
        score_list.append("")
        score_qty_list.append("")
        info_list.append("")
        info_2_list.append("")
        info_3_list.append("")
        info_4_list.append("")
        ing_list.append([])
        nutri_list.append([])
        continue

    # Extract the recipe title
    try:
        receta = driver.find_element(By.CLASS_NAME, "recipe-card__title").text
    except Exception as e:
        receta = ""
        print(f"Error extracting recipe title for {recipe_id}: {e}")
    receta_list.append(receta)

    # Extract the score
    try:
        score = driver.find_element(By.CLASS_NAME, 'core-rating__counter').text
    except Exception as e:
        score = ""
        print(f"Error extracting score for {recipe_id}: {e}")
    score_list.append(score)

    # Extract the score quantity
    try:
        score_qty = driver.find_element(By.CLASS_NAME, 'core-rating__label').text
    except Exception as e:
        score_qty = ""
        print(f"Error extracting score quantity for {recipe_id}: {e}")
    score_qty_list.append(score_qty)

    # Extract difficulty information
    try:
        info = driver.find_element(By.ID, "rc-icon-difficulty-text").text
    except Exception as e:
        info = ""
        print(f"Error extracting difficulty info for {recipe_id}: {e}")
    info_list.append(info)

    # Extract active time (preparation time)
    try:
        info_2 = driver.find_element(By.ID, "rc-icon-active-time-text").text
    except Exception as e:
        info_2 = ""
        print(f"Error extracting active time for {recipe_id}: {e}")
    info_2_list.append(info_2)

    # Extract total time
    try:
        info_3 = driver.find_element(By.ID, "rc-icon-total-time-text").text
    except Exception as e:
        info_3 = ""
        print(f"Error extracting total time for {recipe_id}: {e}")
    info_3_list.append(info_3)

    # Extract quantity info
    try:
        info_4 = driver.find_element(By.ID, "rc-icon-quantity-icon-text").text
    except Exception as e:
        info_4 = ""
        print(f"Error extracting quantity info for {recipe_id}: {e}")
    info_4_list.append(info_4)

    # Extract ingredients
    try:
        container = driver.find_element(By.ID, "ingredients")
        li_elements = container.find_elements(By.TAG_NAME, "li")
        ing = [li.text for li in li_elements]
    except Exception as e:
        ing = []
        print(f"Error extracting ingredients for {recipe_id}: {e}")
    ing_list.append(ing)

    # Extract nutrition information
    try:
        con2 = driver.find_element(By.CLASS_NAME, "nutritions")
        dt_elements = con2.find_elements(By.TAG_NAME, "dt")
        dd_elements = con2.find_elements(By.TAG_NAME, "dd")
        scraped_list = [(dt.text.strip(), dd.text.strip()) for dt, dd in zip(dt_elements, dd_elements)]
    except Exception as e:
        scraped_list = []
        print(f"Error extracting nutrition info for {recipe_id}: {e}")
    nutri_list.append(scraped_list)

    # Optionally, print progress every 10 recipes
    if count % 10 == 0:
        print(f"Processed {count} recipes.")

    # Save progress every time 200 recipes are processed
    if count % 100 == 0:
        save_progress()

# Final backup save after loop ends
save_progress()

# Close the browser
driver.quit()
print("Scraping completed!")
