import requests
import json
import os
from datetime import datetime

RAKUTEN_APP_ID = "d2c61ae7-3ff0-43ed-96ec-9171f293515e"

def get_exchange_rates():
    try:
        res = requests.get("https://open.er-api.com/v6/latest/USD").json()
        rates = res.get("rates", {})
        jpy = rates.get("JPY", 155.0)
        myr = rates.get("MYR", 4.5)
        return {
            "MYR_JPY": round(jpy / myr, 2),
            "USD_JPY": round(jpy, 2)
        }
    except Exception as e:
        print(f"Rate fetch error: {e}")
        return {"MYR_JPY": 33.5, "USD_JPY": 155.0}

def get_rakuten_price(keyword):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170426"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "keyword": keyword,
        "sort": "+itemPrice",
        "hits": 3,
        "format": "json"
    }
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and len(res["Items"]) > 0:
            return res["Items"][0]["Item"]["itemPrice"]
    except Exception as e:
        print(f"Rakuten API error for {keyword}: {e}")
    return None

def get_shopee_price(page, url, option_text=None):
    if not page or not url or not url.startswith("http"):
        return None
    try:
        page.goto(url, wait_until="networkidle", timeout=15000)
        if option_text:
            btn = page.locator(f'button:has-text("{option_text}")').first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1000)
        price_el = page.locator('.pq8P2E').first
        if price_el.is_visible():
            p_text = price_el.inner_text().replace("RM", "").replace(",", "").strip()
            return float(p_text)
    except Exception as e:
        print(f"Shopee fetch error [{url}]: {e}")
    return None

def main():
    rates = get_exchange_rates()
    
    ram_targets = [
        # DDR4
        {"brand": "Crucial", "model": "CB8GS2666", "type": "DDR4", "capacity": "8GB", "rakuten_kw": "Crucial DDR4 SO-DIMM 8GB", "shopee_url": ""},
        {"brand": "Crucial", "model": "CT16G4SFRA32A", "type": "DDR4", "capacity": "16GB", "rakuten_kw": "Crucial DDR4 SO-DIMM 16GB", "shopee_url": ""},
        {"brand": "Crucial", "model": "CT32G4SFD832A", "type": "DDR4", "capacity": "32GB", "rakuten_kw": "Crucial DDR4 SO-DIMM 32GB", "shopee_url": ""},
        # DDR5
        {"brand": "Crucial", "model": "CT8G48C40U5", "type": "DDR5", "capacity": "8GB", "rakuten_kw": "Crucial DDR5 SO-DIMM 8GB", "shopee_url": ""},
        {"brand": "Crucial", "model": "CT16G48C40U5", "type": "DDR5", "capacity": "16GB", "rakuten_kw": "Crucial DDR5 SO-DIMM 16GB", "shopee_url": ""},
        {"brand": "Samsung", "model": "M425R4GA3BB0", "type": "DDR5", "capacity": "32GB", "rakuten_kw": "Samsung DDR5 SO-DIMM 32GB", "shopee_url": ""}
    ]

    ssd_targets = [
        # PCIe 3.0
        {"brand": "Crucial", "model": "P3", "spec": "PCIe 3.0", "capacity": "512GB", "rakuten_kw": "Crucial P3 500GB NVMe", "shopee_url": ""},
        {"brand": "Crucial", "model": "P3", "spec": "PCIe 3.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 1TB NVMe", "shopee_url": ""},
        {"brand": "Crucial", "model": "P3", "spec": "PCIe 3.0", "capacity": "2TB", "rakuten_kw": "Crucial P3 2TB NVMe", "shopee_url": ""},
        # PCIe 4.0
        {"brand": "Crucial", "model": "P3 Plus", "spec": "PCIe 4.0", "capacity": "512GB", "rakuten_kw": "Crucial P3 Plus 500GB NVMe", "shopee_url": ""},
        {"brand": "Crucial", "model": "P3 Plus", "spec": "PCIe 4.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 Plus 1TB NVMe", "shopee_url": ""},
        {"brand": "Western Digital", "model": "SN580", "spec": "PCIe 4.0", "capacity": "2TB", "rakuten_kw": "WD Blue SN580 2TB", "shopee_url": ""}
    ]

    ram_results = []
    ssd_results = []

    playwright_instance = None
    browser = None
    page = None
    try:
        from playwright.sync_api import sync_playwright
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(headless=True)
        page = browser.new_page()
    except Exception as e:
        print(f"Playwright bypass/fallback: {e}")

    for item in ram_targets:
        r_price = get_rakuten_price(item["rakuten_kw"])
        s_price = get_shopee_price(page, item.get("shopee_url"), item.get("shopee_opt")) if page else None
        ram_results.append({
            "brand": item["brand"],
            "model": item.get("model", "-"),
            "type": item["type"],
            "capacity": item["capacity"],
            "rakuten_jpy": r_price,
            "shopee_myr": s_price
        })

    for item in ssd_targets:
        r_price = get_rakuten_price(item["rakuten_kw"])
        s_price = get_shopee_price(page, item.get("shopee_url"), item.get("shopee_opt")) if page else None
        ssd_results.append({
            "brand": item["brand"],
            "model": item.get("model", "-"),
            "spec": item["spec"],
            "capacity": item["capacity"],
            "rakuten_jpy": r_price,
            "shopee_myr": s_price
        })

    if browser:
        browser.close()
    if playwright_instance:
        playwright_instance.stop()

    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "exchange_rates": rates,
        "ram": ram_results,
        "ssd": ssd_results
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print("data.json updated successfully.")

if __name__ == "__main__":
    main()
