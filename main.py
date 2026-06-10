import re
from playwright.sync_api import sync_playwright

URL = "https://www.google.com/travel/flights/search?tfs=CBwQAhojEgoyMDI2LTEyLTI0agcIARIDTEhScgwIAxIIL20vMDdkZmsaIxIKMjAyNy0wMS0yMWoMCAMSCC9tLzA3ZGZrcgcIARIDTEhSQAFAAUABSAFwAYIBCwj___________8BmAEB&tfu=EgoIABAAGAAgAigB&hl=en-GB&gl=GB"

def check_price():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_timeout(10000)

        text = page.inner_text("body")

        prices = re.findall(r'£\d{1,3}(?:,\d{3})*', text)

        cards = page.locator('[role="listitem"]')

        print("Cards found:", cards.count())

        for i in range(min(cards.count(), 10)):
            print("\n--- CARD", i, "---")
            print(cards.nth(i).inner_text())

        lines = text.splitlines()

        start = 0
        
        for i, line in enumerate(lines):
            if "Fetching results" in line:
                start = i
                break
        flight_lines = lines[start:]

        cards = []
        current = []
        for line in flight_lines:
            current.append(line)
            if line.startswith("Avoids"):
                cards.append(current)
                current = []
        for card in cards:

            flight = {

                "airline": None,

                "route": None,

                "stops": None,

                "duration": None,

                "price": None

            }

            for i, line in enumerate(card):

                if "£" in line:

                    flight["price"] = int(line.replace("£", "").replace(",", ""))

                elif "hrs" in line:

                    flight["duration"] = line

                elif "LHR" in line or "HND" in line or "–" in line:
        
                    flight["route"] = line

                elif "stop" in line.lower():

                    flight["stops"] = line

        # airline heuristic (important)

                elif (

                    "£" not in line and

                    "hrs" not in line and

                    "stop" not in line.lower() and

                    "–" not in line and

                    "CO2" not in line and

                    len(line) < 40

                ):

                    if flight["airline"] is None:

                        flight["airline"] = line

            flights.append(flight)
        

        print(prices)
        print("prices are printed")

        with open("page.txt", "w", encoding="utf-8") as f:
            f.write(text)

        browser.close()

check_price()
