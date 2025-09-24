from fastapi import FastAPI
import subprocess
import os
import pandas as pd
import psycopg2
import threading
import sys
import time
import random

app = FastAPI()

# Global lock flag
scraping_in_progress = False
lock = threading.Lock()

# File names (temporary)
CSV_FILE = "products2.csv"
DETAILS_FILE = "product_details2.csv"

# PostgreSQL connection config
DB_CONFIG = {
    "dbname": "costco_db",
    "user": "postgres",
    "password": "9314110690",
    "host": "localhost",   # or your DB server IP
    "port": "5432"
}

# Ensure DB setup
def init_db():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT,
            item_number TEXT,
            price TEXT,
            image_url TEXT,
            url TEXT UNIQUE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()


@app.get("/")
def root():
    return {"status": "API running. Use /scrape to fetch products."}


@app.get("/scrape")
def scrape_all():
    global scraping_in_progress

    with lock:
        if scraping_in_progress:
            return {"status": "busy", "message": "Scraping already in progress. Try again later."}
        scraping_in_progress = True

    try:
        # --- Step 1: Run first script (collect product URLs)
        print("▶️ Running script 1 (collect product URLs)...")
        subprocess.run([sys.executable, "products.py"], check=True)

        if not os.path.exists(CSV_FILE):
            scraping_in_progress = False
            return {"error": "products2.csv not generated"}
        time.sleep(random.uniform(290, 320))
        # --- Step 2: Run second script (scrape details)
        print("▶️ Running script 2 (scrape product details)...")
        subprocess.run([sys.executable, "scrapping.py"], check=True)

        if not os.path.exists(DETAILS_FILE):
            scraping_in_progress = False
            return {"error": "Scraped details file not found"}

        # --- Step 3: Load scraped CSV into PostgreSQL
        df = pd.read_csv(DETAILS_FILE)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        inserted = 0
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO products (name, item_number, price, image_url, url)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE 
                        SET name = EXCLUDED.name,
                            item_number = EXCLUDED.item_number,
                            price = EXCLUDED.price,
                            image_url = EXCLUDED.image_url
                """, (
                    row.get("Product Name", ""),
                    row.get("Item Number", ""),
                    row.get("Price ($)", ""),
                    row.get("Image URL", ""),
                    row.get("URL", "")
                ))
                inserted += 1
            except Exception as e:
                print(f"⚠️ Skipped row due to DB error: {e}")

        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "inserted": inserted}

    except subprocess.CalledProcessError as e:
        return {"error": f"Script failed: {e}"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        # --- Cleanup temp files ---
        for f in [CSV_FILE, DETAILS_FILE]:
            if os.path.exists(f):
                os.remove(f)
                print(f"🗑️ Removed {f}")

        # Always release the lock at the end
        scraping_in_progress = False


@app.get("/products")
def get_products(limit: int = 20):
    """Fetch products from PostgreSQL"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT name, item_number, price, image_url, url FROM products LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"name": r[0], "item_number": r[1], "price": r[2], "image_url": r[3], "url": r[4]}
        for r in rows
    ]
