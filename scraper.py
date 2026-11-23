import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import urllib3
import json
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BCV_URL = "https://www.bcv.org.ve/"
HEADERS = {
    "User-Agent": "ElMandado-Rate/1.0 (https://github.com/ElChuchoXd/el-mandado-rate)"
}

def scrape_bcv_usd():
    r = requests.get(BCV_URL, headers=HEADERS, timeout=25, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    div = soup.find(id="dolar")
    if not div: raise ValueError("No se encontró #dolar")
    strong = div.find("strong")
    if not strong: raise ValueError("No se encontró <strong>")
    raw = strong.get_text(strip=True)
    normalized = raw.replace(".", "").replace(",", ".")
    value = float(normalized)
    if value <= 0: raise ValueError("Tasa inválida")
    return value, raw

def main():
    try:
        value, raw = scrape_bcv_usd()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "value": value,
        "source": "bcv-scraper",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "raw": raw,
    }
    
    # Guardamos la tasa en un archivo local
    with open("data.json", "w") as f:
        json.dump(payload, f)
    print(f"OK: USD = {value}")

if __name__ == "__main__":
    main()
