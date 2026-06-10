import re
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.google.com/travel/flights/search?tfs=CBwQAhosEgoyMDI2LTEyLTI0KAFgsAlqBwgBEgNMSFJyDAgDEggvbS8wN2Rma5AB6AIaLBIKMjAyNy0wMS0xOCgBYLAJagwIAxIIL20vMDdkZmtyBwgBEgNMSFKQAegCQAFAAUABSAFwAYIBCwj___________8BmAEB&tfu=EggIAhABIAIoAyIA&hl=en-GB&gl=GB&curr=GBP"


def extract_price(line):
    match = re.search(r'£\d{1,3}(?:,\d{3})*', line)
    if match:
        return int(match.group().replace("£", "").replace(",", ""))
    return None


def check_price(url):

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
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
                "transfer": None,
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
                if re.match(r"\d{2}:\d{2}", line):
                    if flight["departure"] is None:
                        flight["departure"] = line
                    else:
                        flight["arrival"] = line
                    continue

                # 3. DURATION
                if "hrs" in line:
                    transfer_match = re.search(r"(\d+\s*hrs\s*\d+\s*min)\s*([A-Z]{3})", line)
                    if transfer_match:
                        flight["transfer"] = line
                        continue
                    total_match = re.fullmatch(r"\d+\s*hrs\s*\d+\s*min", line)
                    if total_match:
                        flight["duration"] = line
                        continue

                # 4. ROUTE
                if "LHR" in line and "–" in line:
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
                    not line.isdigit() and
                    not re.match(r"\d{2}:\d{2}", line) and
                    not re.match(r"\d{2}:\d{2}\+\d", line) and
                    len(line) < 60
                ):
                    if flight["airline"] is None:
                        flight["airline"] = line

            flights.append(flight)


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

        with open("page.txt", "w", encoding="utf-8") as f:
            f.write(text)

        browser.close()

        return flights


return_dates = [
    "2027-01-18",
    "2027-01-19",
    "2027-01-20",
    "2027-01-21",
    "2027-01-22",
    "2027-01-23",
    "2027-01-24"
]

results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for date in return_dates:

        print("\n" + "="*50)
        print(f"Searching return date: {date}")
        print("="*50)

        page.goto(BASE_URL)
        page.wait_for_timeout(2000)

        # open return date picker (robust way)
        page.get_by_label("Return").click()

        # select date using stable attribute
        page.click(f'div[data-value="{date}"]')

        page.wait_for_timeout(5000)

        flights = check_price(page)

        if not flights:
            print("No flights found")
            continue

        cheapest = flights[0]

        print("Cheapest flight:")
        print(cheapest)

        results.append({
            "return_date": date,
            "price": cheapest["price"],
            "duration": cheapest["duration"],
            "stops": cheapest["stops"]
        })

    browser.close()
