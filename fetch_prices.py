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

def get_rakuten_info(keyword):
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170426"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "keyword": keyword,
        "sort": "+itemPrice",
        "hits": 1,
        "format": "json"
    }
    try:
        res = requests.get(url, params=params).json()
        if "Items" in res and len(res["Items"]) > 0:
            item = res["Items"][0]["Item"]
            return {
                "price": item["itemPrice"],
                "shop": item["shopName"],
                "url": item["itemUrl"]
            }
    except Exception as e:
        print(f"Rakuten API error for {keyword}: {e}")
    return {"price": None, "shop": None, "url": None}

def get_shopee_info(page, url, option_text=None):
    if not url or not url.startswith("http"):
        return {"price": None, "shop": None, "url": None}
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        if option_text:
            btn = page.locator(f'button:has-text("{option_text}")').first
            if btn.is_visible():
                btn.click()
                page.wait_for_timeout(1000)
        
        price_el = page.locator('.pq8P2E').first
        shop_el = page.locator('.V_o_VL').first
        
        price = None
        shop = None
        
        if price_el.is_visible():
            p_text = price_el.inner_text().replace("RM", "").replace(",", "").strip()
            price = float(p_text)
        if shop_el.is_visible():
            shop = shop_el.inner_text().strip()
            
        return {"price": price, "shop": shop, "url": url}
    except Exception as e:
        print(f"Shopee fetch error [{url}]: {e}")
    return {"price": None, "shop": None, "url": None}

def main():
    rates = get_exchange_rates()
    
    # RAM 検索対象
    ram_targets = [
        # DDR4
        {"brand": "Crucial", "model": "CT8G4SFRA32A", "type": "DDR4", "capacity": "8GB", "rakuten_kw": "Crucial CT8G4SFRA32A", "shopee_url": "", "shopee_opt": "8GB"},
        {"brand": "Crucial", "model": "CT16G4SFRA32A", "type": "DDR4", "capacity": "16GB", "rakuten_kw": "Crucial CT16G4SFRA32A", "shopee_url": "", "shopee_opt": "16GB"},
        {"brand": "Crucial", "model": "CT32G4SFD832A", "type": "DDR4", "capacity": "32GB", "rakuten_kw": "Crucial CT32G4SFD832A", "shopee_url": "", "shopee_opt": "32GB"},
        # DDR5
        {"brand": "Crucial", "model": "CT8G48C40S5", "type": "DDR5", "capacity": "8GB", "rakuten_kw": "Crucial CT8G48C40S5", "shopee_url": "", "shopee_opt": "8GB"},
        {"brand": "Crucial", "model": "CT16G56C46S5", "type": "DDR5", "capacity": "16GB", "rakuten_kw": "Crucial CT16G56C46S5", "shopee_url": "", "shopee_opt": "16GB"},
        {"brand": "Samsung", "model": "M425R4GA3BB0-CQOD0", "type": "DDR5", "capacity": "32GB", "rakuten_kw": "Samsung DDR5 SO-DIMM 32GB", "shopee_url": "", "shopee_opt": "32GB"}
    ]

    # SSD 検索対象（PCIe 4.0 に 256GB / 500GB を追加）
    ssd_targets = [
        # PCIe 3.0 (Gen3)
        {"brand": "Transcend", "model": "TS256GMTE110S", "spec": "PCIe 3.0", "capacity": "256GB", "rakuten_kw": "Transcend TS256GMTE110S", "shopee_url": "", "shopee_opt": "256GB"},
        {"brand": "Crucial", "model": "CT500P3SSD8", "spec": "PCIe 3.0", "capacity": "500GB", "rakuten_kw": "Crucial P3 500GB CT500P3SSD8", "shopee_url": "", "shopee_opt": "500GB"},
        {"brand": "Crucial", "model": "CT1000P3SSD8", "spec": "PCIe 3.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 1TB CT1000P3SSD8", "shopee_url": "", "shopee_opt": "1TB"},
        {"brand": "Crucial", "model": "CT2000P3SSD8", "spec": "PCIe 3.0", "capacity": "2TB", "rakuten_kw": "Crucial P3 2TB CT2000P3SSD8", "shopee_url": "", "shopee_opt": "2TB"},
        # PCIe 4.0 (Gen4)
        {"brand": "Kingston", "model": "SNV2S/250G", "spec": "PCIe 4.0", "capacity": "250GB", "rakuten_kw": "Kingston NV2 250G SNV2S", "shopee_url": "", "shopee_opt": "250GB"},
        {"brand": "Crucial", "model": "CT500P3PSSD8", "spec": "PCIe 4.0", "capacity": "500GB", "rakuten_kw": "Crucial P3 Plus 500GB CT500P3PSSD8", "shopee_url": "", "shopee_opt": "500GB"},
        {"brand": "Crucial", "model": "CT1000P3PSSD8", "spec": "PCIe 4.0", "capacity": "1TB", "rakuten_kw": "Crucial P3 Plus 1TB CT1000P3PSSD8", "shopee_url": "", "shopee_opt": "1TB"},
        {"brand": "Western Digital", "model": "WDS200T3B0E", "spec": "PCIe 4.0", "capacity": "2TB", "rakuten_kw": "WD Blue SN580 2TB WDS200T3B0E", "shopee_url": "", "shopee_opt": "2TB"}
    ]

    ram_results = []
    ssd_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for item in ram_targets:
            r_info = get_rakuten_info(item["rakuten_kw"])
            s_info = get_shopee_info(page, item["shopee_url"], item["shopee_opt"])
            ram_results.append({
                "brand": item["brand"],
                "model": item["model"],
                "type": item["type"],
                "capacity": item["capacity"],
                "rakuten": r_info,
                "shopee": s_info
            })

        for item in ssd_targets:
            r_info = get_rakuten_info(item["rakuten_kw"])
            s_info = get_shopee_info(page, item["shopee_url"], item["shopee_opt"])
            ssd_results.append({
                "brand": item["brand"],
                "model": item["model"],
                "spec": item["spec"],
                "capacity": item["capacity"],
                "rakuten": r_info,
                "shopee": s_info
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
