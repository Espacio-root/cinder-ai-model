import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize WebDriver
options = Options()
options.add_argument("user-data-dir=/home/espacio/.config/chromium/Profile 1")
driver = webdriver.Chrome(options=options)

# Load href_data.json
href_file = "href_data.json"
output_file = "product_data.json"

def get_color():
    try:
        WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "variation_color_name"))
        )
        color_name = driver.find_element(By.XPATH, "//*[@id=\"variation_color_name\"]/div/span").text.strip()
    except:
        color_name = "unknown"
    print(color_name)

    # Extract images for this color
    images = []
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "imageThumbnail"))
    )
    thumbnails = driver.find_elements(By.CLASS_NAME, "imageThumbnail")
    for thumbnail in thumbnails:
        try: thumbnail.click()
        except: pass
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id=\"main-image-container\"]/ul"))
        )
        try:
            img_element = driver.find_element(By.XPATH, "//*[@id=\"main-image-container\"]/ul/li[1]/span/span/div/img")
        except:
            img_element = driver.find_element(By.XPATH, "//*[@id=\"main-image-container\"]/ul/li[4]/span/span/div/img")
        images.append({
            "href": img_element.get_attribute("src"),
            "alt": img_element.get_attribute("alt"),
        })

    # Extract affiliate link
    affiliate_href = ""
    try:
        for _ in range(2):
            affiliate_button = driver.find_element(By.ID, "amzn-ss-get-link-button")
            affiliate_button.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "amzn-ss-text-shortlink-textarea")))
            affiliate_href = driver.find_element(By.ID, "amzn-ss-text-shortlink-textarea").text.strip()
            st_time = time.time()
            while (affiliate_href == "" and time.time() - st_time < 10):
                affiliate_href = driver.find_element(By.ID, "amzn-ss-text-shortlink-textarea").text.strip()
            if (affiliate_href != ""): break
    except Exception as e:
        pass
    return color_name, {"images": images, "affiliate_href": affiliate_href}

def process_price(price):
    res = 0
    i = 0
    for p in price[::-1]:
        if (p.isnumeric()):
            res += (int(p)*(10**i))
            i += 1
    return res

try:
    with open(href_file, "r") as file:
        href_data = json.load(file)
except FileNotFoundError:
    print(f"{href_file} not found.")
    exit(1)

# Initialize or load product data
try:
    with open(output_file, "r") as file:
        product_data = json.load(file)
except FileNotFoundError:
    product_data = {}

try:
    for main_category, categories in href_data.items():
        if main_category not in product_data:
            product_data[main_category] = {}

        duplicate_list = []
        for category_name, href_list in categories.items():
            if category_name in product_data[main_category]:
                for item in product_data[main_category][category_name]:
                    duplicate_list.append(item["href"])
                present = True
            else:
                present = False
                product_data[main_category][category_name] = []

            for href in href_list:
                if (present and href in duplicate_list):
                    print(f"{href} found, continuing...")
                    continue
                try:
                    driver.get(href)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "productTitle"))
                    )

                    # Extract product details
                    title = driver.find_element(By.ID, "productTitle").text.strip()

                    try:
                        price = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.strip()
                        price = process_price(price)
                    except:
                        price = None

                    # Extract product information
                    product_information = []
                    try:
                        facts = driver.find_elements(By.CLASS_NAME, "product-facts-detail")
                        for fact in facts:
                            left = fact.find_element(By.CLASS_NAME, "a-col-left").text.strip()
                            right = fact.find_element(By.CLASS_NAME, "a-col-right").text.strip()
                            if (left != "" and right != ""):
                                product_information.append({left: right})
                    except:
                        pass

                    # Extract "About Item" details
                    about_item = []
                    try:
                        facts_expander = driver.find_element(By.ID, "productFactsDesktopExpander")
                        li_tags = facts_expander.find_elements(By.TAG_NAME, "li")
                        about_item = [li.text.strip() for li in li_tags]
                    except:
                        pass

                    # Extract colors and images
                    colors = {}
                    color_elements = []
                    try:
                        color_elements = driver.find_elements(By.XPATH, "//li[contains(@id, 'color_name_')]")
                    except:
                        pass

                    for i in range(max(1, len(color_elements))):
                        try:
                            if (len(color_elements)):
                                color_elements[i].click()
                            color_name, color_data = get_color()
                            colors[color_name] = color_data
                        except Exception as e:
                            print(e)
                            pass


                    # Add product details to category
                    product_data[main_category][category_name].append({
                        "href": href,
                        "title": title,
                        "price": price,
                        # "discounted_price": discounted_price,
                        "product_information": product_information,
                        "about_item": about_item,
                        "colors": colors,
                    })

                    # Save after processing each product
                    with open(output_file, "w") as file:
                        json.dump(product_data, file, indent=4)

                    print(f"Processed product: {title}")

                except Exception as e:
                    print(f"Error processing product at {href}: {e}")

finally:
    driver.quit()
