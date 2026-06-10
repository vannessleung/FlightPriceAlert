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
        flihgt_lines = lines[start:]

        cards = []
        current = []
        for line in flight_lines:
            current.append(line)
            if line.startswith("Avoids"):
                cards.append(current)
                current = []
        if line.startswith("£"):
            print("PRICES:", line)
        if "-" in line and len(line)<10:
            print("Airport:", line)
        if "hrs" in line:
            print("Flight duration:", line)
        if "stop" in line:
            print(line)
        

        print(prices)
        print("prices are printed")

        with open("page.txt", "w", encoding="utf-8") as f:
            f.write(text)

        browser.close()

check_price()
