import os
import json
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BCV_URL = "https://www.bcv.org.ve/"
HEADERS = {
    "User-Agent": "ElMandado-Rate/1.0 (https://github.com/tu-usuario/el-mandado-rate)"
}

CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_KV_NAMESPACE_ID = os.environ["CF_KV_NAMESPACE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]


def scrape_bcv_usd():
    """Devuelve (value: float, raw: str). Lanza excepción si no puede."""
    r = requests.get(BCV_URL, headers=HEADERS, timeout=25, verify=False)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # El BCV publica la tasa USD dentro de <div id="dolar"><strong>36.500,00</strong></div>
    div = soup.find(id="dolar")
    if not div:
        raise ValueError("No se encontró el bloque #dolar en la página del BCV")

    strong = div.find("strong")
    if not strong:
        raise ValueError("No se encontró <strong> dentro de #dolar")

    raw = strong.get_text(strip=True)
    # Formato venezolano: "36.500,00" → "36500.00"
    normalized = raw.replace(".", "").replace(",", ".")
    try:
        value = float(normalized)
    except ValueError:
        raise ValueError(f"No se pudo parsear la tasa: {raw!r}")

    if value <= 0:
        raise ValueError(f"Tasa inválida: {value}")

    return value, raw


def kv_put(key: str, value: dict):
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{key}"
    )
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.put(url, headers=headers, data=json.dumps(value), timeout=20)
    r.raise_for_status()
    print(f"KV actualizado: {key} = {value}")


def main():
    try:
        value, raw = scrape_bcv_usd()
    except Exception as e:
        print(f"ERROR scraping BCV: {e}", file=sys.stderr)
        sys.exit(1)  # falla el workflow → GitHub te avisa

    payload = {
        "value": value,
        "source": "bcv-scraper",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "raw": raw,
    }
    kv_put("bcv_rate", payload)
    print(f"OK: USD = {value}")


if __name__ == "__main__":
    main()
