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

        # =========================
        # 3. PARSE EACH CARD
        # =========================
        flights = []

        for card in cards:

            flight = {
                "airline": None,
                "departure": None,
                "arrival": None,
                "route": None,
                "stops": None,
                "duration": None,
                "price": None
            }

            time_pattern = re.compile(r"\d{2}:\d{2}")

            for line in card:

                # 1. PRICE
                price = extract_price(line)
                if price:
                    flight["price"] = price
                    continue

                # 2. TIME (this is the key fix)
                if time_pattern.fullmatch(line):
                    if "departure" not in flight:
                        flight["departure"] = line
                    else:
                        flight["arrival"] = line
                    continue

                # 3. DURATION
                if "hrs" in line:
                    flight["duration"] = line
                    continue

                # 4. ROUTE
                if "LHR" in line or "HND" in line or "–" in line:
                    flight["route"] = line
                    continue

                # 5. STOPS
                if "stop" in line.lower():
                    flight["stops"] = line
                    continue

                # 6. AIRLINE (ONLY AFTER EVERYTHING ELSE)
                if (
                    "£" not in line and
                    "hrs" not in line and
                    "stop" not in line.lower() and
                    "–" not in line and
                    "CO2" not in line and
                    len(line) < 60
                ):
                if flight["airline"] is None:
                    flight["airline"] = line

                    flights.append(flight)

                with open("page.txt", "w", encoding="utf-8") as f:
                    f.write(text)

        # =========================
        # 4. OUTPUT RESULTS
        # =========================
        flights = [f for f in flights if f["price"] is not None]

        flights.sort(key=lambda x: x["price"])

        print("\n===== TOP 3 FLIGHTS =====")
        for f in flights[:3]:
            print(f)

        if flights:
            print("\n===== CHEAPEST =====")
            print(flights[0])

        browser.close()


check_price()
