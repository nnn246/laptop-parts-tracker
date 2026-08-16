import requests
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

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
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
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
        {"brand": "Crucial", "model": "-", "type": "DDR4", "capacity": "8GB", "rakuten_kw": "Crucial DDR4 SO-DIMM 8GB", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "8GB"},
        {"brand": "Crucial", "model": "-", "type": "DDR4", "capacity": "16GB", "rakuten_kw": "Crucial DDR4 SO-DIMM 16GB", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "16GB"},
        {"brand": "Crucial", "model": "-", "type": "DDR5", "capacity": "16GB", "rakuten_kw": "Crucial DDR5 SO-DIMM 16GB", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "16GB"},
        {"brand": "Samsung", "model": "-", "type": "DDR5", "capacity": "32GB", "rakuten_kw": "Samsung DDR5 SO-DIMM 32GB", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "32GB"}
    ]

    ssd_targets = [
        {"brand": "Crucial", "model": "P3", "spec": "PCIe 3.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 1TB NVMe", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "1TB"},
        {"brand": "Crucial", "model": "P3 Plus", "spec": "PCIe 4.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 Plus 1TB NVMe", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "1TB"},
        {"brand": "Western Digital", "model": "SN580", "spec": "PCIe 4.0", "capacity": "2TB", "rakuten_kw": "WD Blue SN580 2TB", "shopee_url": "https://shopee.com.my/...", "shopee_opt": "2TB"}
    ]

    ram_results = []
    ssd_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for item in ram_targets:
            r_price = get_rakuten_price(item["rakuten_kw"])
            s_price = get_shopee_price(page, item["shopee_url"], item["shopee_opt"]) if item["shopee_url"].startswith("http") else None
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
            s_price = get_shopee_price(page, item["shopee_url"], item["shopee_opt"]) if item["shopee_url"].startswith("http") else None
            ssd_results.append({
                "brand": item["brand"],
                "model": item.get("model", "-"),
                "spec": item["spec"],
                "capacity": item["capacity"],
                "rakuten_jpy": r_price,
                "shopee_myr": s_price
            })

        browser.close()

    output_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "exchange_rates": rates,
        "ram": ram_results,
        "ssd": ssd_results
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
