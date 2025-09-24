from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv
import undetected_chromedriver as uc
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random

# Load product URLs from CSV
df = pd.read_csv("products2.csv")
product_links = [
    url for url in df["URL"].dropna().tolist()
    if isinstance(url, str) and url.startswith("https://www.costco.com/")
]

print(f"✅ Loaded {len(product_links)} valid product URLs")

# Setup undetected Chrome
options = uc.ChromeOptions()
# options.add_argument("--headless")  # Set False to see the browser
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--profile-directory=Default")
options.add_argument("--incognito")
options.add_argument("--start-maximized")

print("🚀 Launching undetected Chrome...")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# Final data
data = []
missing_links = []

COSTCO_EMAIL = "enquiry.dotdevz@gmail.com"
COSTCO_PASS = "/F9Jib-gDRhk6*u"

def login_if_required(product_url):
    try:
        # Check if "Sign In to See Price" exists
        signin_button = driver.find_elements(By.CSS_SELECTOR, "li#sign-in-to-buy-v2 a")
        print(f"🔍 Sign-in button found: {len(signin_button)}")
        if signin_button:
            print("🔑 Sign in required. Clicking login...")
            signin_button[0].click()

            # Wait until redirected to login page
            wait.until(EC.presence_of_element_located((By.ID, "signInName")))

            # Enter email
            email_input = driver.find_element(By.ID, "signInName")
            email_input.clear()
            email_input.send_keys(COSTCO_EMAIL)

            # Enter password
            pass_input = driver.find_element(By.ID, "password")
            pass_input.clear()
            pass_input.send_keys(COSTCO_PASS)

            # Click Sign In
            signin_btn = driver.find_element(By.ID, "next")
            signin_btn.click()

            # Wait until redirected back to costco.com product page
            wait.until(lambda d: "costco.com" in d.current_url and "signin" not in d.current_url)

            print("✅ Login successful. Back on product page.")

            # Make sure we are back at the correct product
            if driver.current_url != product_url:
                driver.get(product_url)
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div#pull-right-price span.value")
                ))
            time.sleep(10) # Wait for JS to load*
        else:
            print("ℹ️ No login needed for this product.")

    except Exception as e:
        print(f"❌ Login failed for {product_url}: {e}")
        print("➡️ Revisiting product page without login...")
        try:
            driver.get(product_url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(10) # Wait for JS to load*
        except:
            print("⚠️ Even fallback reload failed.")

def scrape_product(link):
    for attempt in range(1, 4):
        try:
            driver.get(link)
            wait.until(lambda d: d.current_url.startswith("https://www.costco.com"))

            print("refreshing page to ensure full load...")
            time.sleep(10) # Wait for JS to load*
            # If price requires login → handle it
            login_if_required(link)
            driver.refresh()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(10) # Wait for JS to load*
            try:
                name = WebDriverWait(driver, 60).until(EC.presence_of_element_located(
                    (By.XPATH, "//span[@class='product-title' and @itemprop='name']")
                )).text.strip()
                print("name1:")
                print(name)
                if not name:
                    raise Exception("Empty name found")
            except:
                try:
                    name = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.XPATH, "//h1[@automation-id='productName' and @itemprop='name']")
                    )).text.strip()
                    print("name2:")
                    print(name)
                except:
                    name = ""

            try:
                item = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='product-body-item-number' and contains(@class,'item-number')]")
                )).text.replace("Item", "").strip()
                print("item1:")
                print(item)
                if not item:
                    raise Exception("Empty item found")
            except:
                try:
                    item = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.XPATH, "//span[@id='item-no' and contains(@class,'item-number')]")
                    )).text.replace("Item", "").strip()
                    print("item2:")
                    print(item)
                except:
                    item = ""

            try:
                # Case 1: div#pull-right-price > span.value
                price = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='pull-right-price']//span[@class='value' and @automation-id='productPriceOutput']")
                )).text.strip()
                print("price1:")
                print(price)
                if not price:
                    raise Exception("Empty price found")
            except:
                try:
                    # Case 2: direct span with automation-id=productPriceOutput
                    price = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.XPATH, "//span[@class='value' and @automation-id='productPriceOutput']")
                    )).text.strip()
                    print("price2:")
                    print(price)
                except:
                    price = ""

            try:
                # Case 1: high-res image (width=1200)
                img_url = WebDriverWait(driver, 20).until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='zoomImg_wrapper']//img[contains(@src, 'width=1200')]")
                )).get_attribute("src").strip()
                print("image1:")
                print(img_url)
                if not img_url:
                    raise Exception("Empty image src found")
            except:
                try:
                    # Case 2: fallback to lower-res (width=600)
                    img_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.XPATH, "//div[@id='zoomImg_wrapper']//img[contains(@src, 'width=600')]")
                    )).get_attribute("src").strip()
                    print("image2:")
                    print(img_url)
                except:
                    img_url = ""

            if not name:
                missing_links.append(link)
            else:
                data.append({
                    "Product Name": name,
                    "Item Number": item,
                    "Price ($)": price,
                    "Image URL": img_url,
                    "URL": link
                })

            print(f"✅ Scraped: {name if name else '[No Name]'}")
            break
        except Exception as e:
            print(f"❌ Error on product deatil {link}, attempt {attempt}: {e}")
            if attempt < 3:
                print("⏳ Waiting 5 minutes before retry...")
                time.sleep(random.uniform(290, 320))  # wait 5 min then retry
            else:
                print("⚠️ All 3 attempts failed, skipping to next page.")
                missing_links.append(link)

# --- First pass ---
print("🔁 Starting first scraping round...\n")
for link in product_links:
    scrape_product(link)

# --- Retry for missing ones ---
if missing_links:
    print(f"\n🔁 Retrying {len(missing_links)} failed/missing URLs...\n")
    retry_links = missing_links.copy()
    missing_links = []
    for link in retry_links:
        scrape_product(link)

# --- Save results ---
with open("product_details2.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["Product Name", "Item Number", "Price ($)", "Image URL", "URL"])
    writer.writeheader()
    writer.writerows(data)

# --- Log permanently failed ones ---
if missing_links:
    with open("missing_final.txt", "w") as f:
        f.write("\n".join(missing_links))

print(f"\n🎯 Done! Extracted {len(data)} products. Missed {len(missing_links)}. Results saved to 'product_details2.csv'")
driver.quit()