import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
options = Options()
options.add_argument("user-data-dir=/home/espacio/.config/chromium/Profile 1")
driver = webdriver.Chrome(options=options)

# Load or initialize the results JSON file
output_file = "href_data.json"
try:
    with open(output_file, "r") as json_file:
        all_categories = json.load(json_file)
except FileNotFoundError:
    all_categories = {}

try:
    # Open Amazon.in
    driver.get("https://www.amazon.in")

    # Wait for the search bar to be visible
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
    )

    # Find the search bar and input the product name
    search_bar = driver.find_element(By.ID, "twotabsearchtextbox")
    search_bar.send_keys("men's clothing")
    search_bar.send_keys(Keys.RETURN)

    # Wait for the categories to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@id, 'p_n_feature_seven_browse-bin')]"))
    )

    # Extract all category names and links
    category_elements = driver.find_elements(By.XPATH, "//li[contains(@id, 'p_n_feature_seven_browse-bin')]")
    categories = []
    for category_element in category_elements:
        category_name = category_element.text.strip()
        if not category_name:
            continue
        category_link = category_element.find_element(By.TAG_NAME, "a").get_attribute("href")
        categories.append((category_name, category_link))

    # Process each category
    for category_name, category_link in categories:
        if category_name in all_categories:
            print(f"Skipping already processed category: {category_name}")
            continue

        driver.get(category_link)

        # Wait for products to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@class='a-link-normal s-no-outline']"))
        )

        product_links = []

        # Pagination: Visit up to 10 pages or until no next page
        for _ in range(20):
            # Grab product links on the current page
            products = driver.find_elements(By.XPATH, "//a[@class='a-link-normal s-no-outline']")
            for product in products:
                href = product.get_attribute("href")
                if href:
                    product_links.append(href)

            # Try to go to the next page, if available
            try:
                next_page = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 's-pagination-next')]"))
                )
                next_page.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[@class='a-link-normal s-no-outline']"))
                )
            except Exception as e:
                print(e)
                break  # Exit pagination if no next page

        # Store the product links under the category name
        all_categories[category_name] = product_links

        # Save the results to the JSON file
        with open(output_file, "w") as json_file:
            json.dump(all_categories, json_file, indent=4)

        print(f"Saved products for category: {category_name}")

finally:
    # Close the WebDriver
    driver.quit()
