import re
import base64
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

# ================================
# CONFIG
# ================================
ORIGINAL_TFS = "CBwQAhojEgoyMDI2LTEyLTI0agcIARIDTEhScgwIAxIIL20vMDdkZmsaIxIKMjAyNy0wMS0yMWoMCAMSCC9tLzA3ZGZrcgcIARIDTEhSQAFAAUABSAFwAYIBCwj___________8BmAEB"
ORIGINAL_RETURN_DATE = "2027-01-21"

RETURN_DATE_START = date(2027, 1, 18)
RETURN_DATE_END   = date(2027, 1, 24)


# ================================
# URL GENERATION
# ================================
def make_url(return_date_str: str) -> str:
    padding = (4 - len(ORIGINAL_TFS) % 4) % 4
    decoded = base64.urlsafe_b64decode(ORIGINAL_TFS + "=" * padding)
    updated = decoded.replace(ORIGINAL_RETURN_DATE.encode(), return_date_str.encode())
    tfs = base64.urlsafe_b64encode(updated).decode().rstrip("=")
    return f"https://www.google.com/travel/flights/search?tfs={tfs}&tfu=EgoIABAAGAAgAigB&hl=en-GB&gl=GB"


def return_dates():
    delta = RETURN_DATE_END - RETURN_DATE_START
    return [str(RETURN_DATE_START + timedelta(days=i)) for i in range(delta.days + 1)]


# ================================
# PARSING
# ================================
def extract_price(line):
    match = re.search(r'£\d{1,3}(?:,\d{3})*', line)
    if match:
        return int(match.group().replace("£", "").replace(",", ""))
    return None


def parse_flights(text, return_date):
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Remove UI noise
    cleaned = []
    for l in lines:
        if any(x in l for x in [
            "Skip to main content", "Fetching results",
            "Checking prices", "Searching", "Other departing flights"
        ]):
            continue
        cleaned.append(l)

    # Split into cards
    cards = []
    current = []
    started = False
    for line in cleaned:
        if re.match(r"\d{2}:\d{2}", line):
            started = True
        if not started:
            continue
        current.append(line)
        if "round trip" in line:
            cards.append(current)
            current = []

    # Parse each card
    flights = []
    for card in cards:
        flight = {
            "return_date": return_date,
            "airline": None,
            "departure": None,
            "arrival": None,
            "route": None,
            "stops": None,
            "duration": None,
            "transfer": None,
            "price": None,
        }

        for line in card:
            price = extract_price(line)
            if price:
                flight["price"] = price
                continue

            if re.match(r"\d{2}:\d{2}", line):
                if flight["departure"] is None:
                    flight["departure"] = line
                else:
                    flight["arrival"] = line
                continue

            if "hrs" in line:
                transfer_match = re.search(r"(\d+\s*hrs\s*\d+\s*min)\s*([A-Z]{3})", line)
                if transfer_match:
                    flight["transfer"] = line
                    continue
                total_match = re.fullmatch(r"\d+\s*hrs\s*\d+\s*min", line)
                if total_match:
                    flight["duration"] = line
                    continue

            if "LHR" in line and "–" in line:
                flight["route"] = line
                continue

            if "stop" in line.lower():
                flight["stops"] = line
                continue

            if (
                "£" not in line and "hrs" not in line and
                "stop" not in line.lower() and "–" not in line and
                "CO2" not in line and not line.isdigit() and
                not re.match(r"\d{2}:\d{2}", line) and
                not re.match(r"\d{2}:\d{2}\+\d", line) and
                len(line) < 60
            ):
                if flight["airline"] is None:
                    flight["airline"] = line

        if flight["price"] is not None:
            flights.append(flight)

    return flights


# ================================
# MAIN
# ================================
def check_prices():
    all_flights = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for return_date in return_dates():
            print(f"Scraping {return_date}...")
            page.goto(make_url(return_date))
            page.wait_for_timeout(10000)

            text = page.inner_text("body")
            flights = parse_flights(text, return_date)
            print(f"  → {len(flights)} flights found")
            all_flights.extend(flights)

        browser.close()

    all_flights.sort(key=lambda x: x["price"])

    print("\n===== TOP 5 CHEAPEST ACROSS ALL DATES =====")
    for f in all_flights[:5]:
        print(f)

    print("\n===== CHEAPEST PER RETURN DATE =====")
    seen = {}
    for f in all_flights:
        if f["return_date"] not in seen:
            seen[f["return_date"]] = f
    for d in sorted(seen):
        print(f"  {d}: £{seen[d]['price']} — {seen[d]['airline']}")


check_prices()
