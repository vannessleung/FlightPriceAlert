import re
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/travel/flights/search?tfs=CBwQAhojEgoyMDI2LTEyLTI0agcIARIDTEhScgwIAxIIL20vMDdkZmsaIxIKMjAyNy0wMS0yMWoMCAMSCC9tLzA3ZGZrcgcIARIDTEhSQAFAAUABSAFwAYIBCwj___________8BmAEB&tfu=EgoIABAAGAAgAigB&hl=en-GB&gl=GB"


def extract_price(line):
    match = re.search(r'£\d{1,3}(?:,\d{3})*', line)
    if match:
        return int(match.group().replace("£", "").replace(",", ""))
    return None


def check_price():

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_timeout(10000)

        # =========================
        # 1. GET PAGE TEXT
        # =========================
        text = page.inner_text("body")
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # remove UI noise
        cleaned = []
        for l in lines:
            if any(x in l for x in [
                "Skip to main content",
                "Fetching results",
                "Checking prices",
                "Searching",
                "Other departing flights"
            ]):
                continue
            cleaned.append(l)

        # =========================
        # 2. SPLIT INTO CARDS
        # =========================
        cards = []
        current = []

        for line in cleaned:
            current.append(line)

            if "Avoid" in line or "trees absorb" in line:
                cards.append(current)
                current = []

        # =========================
        # 3. PARSE EACH CARD
        # =========================
        flights = []

        for card in cards:

            flight = {
                "airline": None,
                "route": None,
                "stops": None,
                "duration": None,
                "price": None
            }

            for line in card:

                # price
                price = extract_price(line)
                if price:
                    flight["price"] = price

                # duration
                elif "hrs" in line:
                    flight["duration"] = line

                # route
                elif "LHR" in line or "HND" in line or "–" in line:
                    flight["route"] = line

                # stops
                elif "stop" in line.lower():
                    flight["stops"] = line

                # airline (best-effort heuristic)
                elif (
                    "£" not in line and
                    "hrs" not in line and
                    "stop" not in line.lower() and
                    "–" not in line and
                    "CO2" not in line and
                    len(line) < 50
                ):
                    if flight["airline"] is None:
                        flight["airline"] = line

            flights.append(flight)

        # =========================
        # 4. OUTPUT RESULTS
        # =========================
        flights = [f for f in flights if f["price"] is not None]

        flights.sort(key=lambda x: x["price"])

        print("\n===== ALL FLIGHTS =====")
        for f in flights:
            print(f)

        if flights:
            print("\n===== CHEAPEST =====")
            print(flights[0])

        browser.close()


check_price()
