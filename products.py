from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random

# Setup undetected Chrome
options = uc.ChromeOptions()
options.add_argument("--headless")  # Set False to see the browser
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--profile-directory=Default")
options.add_argument("--incognito")
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options,version_main=120)

all_products = []

# Get the pagination element from the first page
driver.get("https://www.costco.com/s?keyword=OFF&currentPage=1")
last_page = 1
try:
    # Wait until all pagination buttons/links are loaded
    pagination_buttons = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "ul.MuiPagination-ul li button, ul.MuiPagination-ul li a")
        )
    )
    print(f"🔢 Pagination buttons found: {len(pagination_buttons)}")

    # Get texts from pagination buttons
    button_texts = [btn.text.strip() for btn in pagination_buttons if btn.text.strip()]
    print(f"📄 Pagination texts: {button_texts}")

    # Try to find the maximum numeric page
    page_numbers = [int(t) for t in button_texts if t.isdigit()]
    if page_numbers:
        last_page = max(page_numbers)
    else:
        last_page = 1
    print(f"✅ Last page detected: {last_page}")

except Exception as e:
    print(f"❌ Error detecting pagination: {e}")

# Loop through pages 1 to 30
for page in range(1, last_page + 1):
    url = f"https://www.costco.com/s?keyword=OFF&currentPage={page}"

    # Retry loop (max 3 attempts per page)
    for attempt in range(1, 4):
        print(f"\n🔄 Scraping page {page} (Attempt {attempt}/3)...")
        driver.get(url)
        try:
            top_deals_section = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.MuiPagination-ul li button"))
            )

            # Extract product <a> elements with product hrefs
            best_deals_section = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[id*='productList']"))
            )
            time.sleep(random.uniform(1, 3))
            product_elements = best_deals_section.find_elements(By.CSS_SELECTOR, "a[data-testid='Link'][href*='product']")
            # best_deals_section = driver.find_element(By.CSS_SELECTOR, "div[id*='productList']")
            # product_elements = best_deals_section.find_elements(By.CSS_SELECTOR, "a[data-testid='Link'][href*='product']")
            for elem in product_elements:
                title = elem.text.strip()
                link = elem.get_attribute("href")
                if title and link:
                    all_products.append({"Title": title, "URL": link, "Section": "Best deals for you"})
            break  # success → exit retry loop and move to next page
        except Exception as e:
            print(f"❌ Error on page {page}, attempt {attempt}: {e}")
            if attempt < 3:
                print("⏳ Waiting 5 minutes before retry...")
                time.sleep(random.uniform(290, 320))  # wait 5 min then retry
            else:
                print("⚠️ All 3 attempts failed, skipping to next page.")
                all_products.append({"Title": f"Error on page {page}", "URL": str(e), "Section": "Best deals for you"})

print(f"✅ Scraped {len(all_products)} products from {last_page} pages.")

# Save to CSV
with open("products2.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["Title", "URL", "Section"])
    writer.writeheader()
    writer.writerows(all_products)

# Save to TXT
with open("products.txt", "w", encoding="utf-8") as f:
    for p in all_products:
        f.write(f"{p['Title']}\n{p['URL']}\n\n")

driver.quit()

print("📁 Saved to 'products2.csv' and 'products.txt'")

