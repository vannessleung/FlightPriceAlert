from playwright.sync_api import sync_playwright

URL = "CBwQAhojEgoyMDI2LTEyLTI0agcIARIDTEhScgwIAxIIL20vMDdkZmsaIxIKMjAyNy0wMS0yMWoMCAMSCC9tLzA3ZGZrcgcIARIDTEhSQAFAAUABSAFwAYIBCwj___________8BmAEB&tfu=EgoIABAAGAAgAigB&hl=en-GB&gl=GB"

def check_price():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL)
        page.wait_for_timeout(10000)  # wait for results

        text = page.content()

        # VERY simple first attempt (we refine later)
        prices = []

        for word in text.split():
            if "£" in word:
                prices.append(word)

        if not prices:
            print("NO PRICE FOUND - scraper may be broken")
            return

        print("Found prices:", prices)

        cheapest = min(prices, key=lambda x: int(x.replace("£","").replace(",","")))
        print("Cheapest:", cheapest)

if __name__ == "__main__":
    check_price()
