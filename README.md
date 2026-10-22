# Google Hotels scraper in Python: hotel prices by booking site

> This repository calls a paid Apify Actor built by Flatrow Data Studio (the author). Links to apify.com carry the author's affiliate code: the author may earn a commission if you sign up to Apify through them, at no extra cost to you.

A small Google Hotels scraper in Python. `scrape.py` runs Google Hotels searches such as "hotels in Lisbon" for your dates and saves **one row per hotel** to CSV: lowest price per night and for the stay with taxes and fees, hotel class, guest rating, review count, amenities, coordinates and website. With `--offers` it also saves **every booking site's rate** for each hotel (Booking.com, Expedia, the hotel's own site...) with direct links: a rate parity check in one command. `monitor_prices.py` turns the same search into a **hotel price tracker** that returns only the price drops, price rises and new hotels since its previous run.

Both scripts run the [Google Hotels Scraper & Price Tracker](https://apify.com/myth84/google-hotels-scraper?fpr=pnpkfc) on Apify through the official `apify-client` package: the Actor runs in Apify's cloud and returns clean rows, so there is no browser, HTML parsing or proxy to maintain on your side. No login, no cookies, and **no personal data**: nothing about guests or reviewers is collected.

## Use cases

- **Hotel price comparison**: the lowest price of every hotel of a city for the same stay, taxes included, in your currency.
- **Rate parity checks** for hoteliers: the hotel's own website against every booking site Google lists (`officialSitePriceTotal` against `cheapestOfferPriceTotal`).
- **Hotel price tracking**: a daily cron job that prints the hotels whose price dropped or rose.
- **Travel datasets**: class, rating, amenities and coordinates of the hotels of a destination, ready for pandas, Excel or a map.

## Installation

You need Python 3.11 or later and a free [Apify account](https://apify.com/?fpr=pnpkfc) (the free plan includes monthly credit).

```bash
git clone https://github.com/flatrow-data-studio/google-hotels-scraper-python.git
cd google-hotels-scraper-python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export APIFY_TOKEN="<your-apify-token>"   # Apify Console > Settings > API & Integrations
```

## Run it

```bash
# Hotels in Lisbon for 20-23 November 2026, 2 adults, prices in USD
python scrape.py "hotels in Lisbon" --check-in 2026-11-20 --check-out 2026-11-23 --max-results 60

# Rate parity: every booking site's rate for 20 hotels in Rome, a 3-night stay starting in 30 days
python scrape.py "hotels in Rome" --offers --max-results 20
```

The script writes `google_hotels.csv` (change it with `--output`), and with `--offers` also `google_hotels_offers.csv`, one line per hotel and booking site; the booking-site rates come at no extra charge. It prints the five cheapest stays. Without `--check-in` / `--check-out` it searches a stay that starts 30 days from today for 3 nights (`--check-in-days`, `--nights`), so the command never expires. Other options: `--adults`, `--currency` (USD by default), several searches in one run (`"hotels in Paris" "hotels in Rome"`), and `--max-charge 0.50` to stop a run once it has cost 50 cents; `python scrape.py --help` lists them all.

## Track prices every day

```bash
python monitor_prices.py "hotels in Paris" --check-in-days 14 --nights 2
```

The first run records the price of every hotel as the reference (they all come back as `new`). From the second run on, only the new hotels and the hotels whose price changed are returned, with `previousPrice`, `priceDelta` and `priceDeltaPercent`; they are printed and appended to `google_hotels_price_changes.csv`. The reference lives in a key-value store of your Apify account (`--store`, `google-hotels-price-monitor` by default), so the script can run from cron on any machine:

```bash
0 7 * * * cd /path/to/google-hotels-scraper-python && .venv/bin/python monitor_prices.py "hotels in Paris" >> tracker.log 2>&1
```

Keep the same search, stay, travellers and currency from run to run: changing them starts a new reference.

## Sample output

One real row from a Lisbon search with the booking-site rates (USD, 20–23 November 2026, 2 adults), key columns only:

```json
{
  "title": "Brown's | Avenue Hotel",
  "propertyType": "5-star hotel",
  "city": "Lisbon",
  "checkIn": "2026-11-20",
  "checkOut": "2026-11-23",
  "currency": "USD",
  "pricePerNight": 169.26,
  "priceTotal": 564.25,
  "rating": 4.6,
  "reviewCount": 283,
  "cheapestOfferSite": "Vio.com",
  "officialSitePriceTotal": 565.73
}
```

## Columns

`scrape.py` writes these columns; lists such as `amenities` are written as JSON text.

| Column | Meaning |
|---|---|
| `platformListingId` | Google Hotels entity id |
| `title` | Hotel name |
| `propertyType` | Class as Google shows it, e.g. 5-star hotel |
| `city` | City |
| `checkIn` | Check-in date of the quoted stay |
| `checkOut` | Check-out date of the quoted stay |
| `nights` | Nights of the stay |
| `currency` | Currency of every price |
| `pricePerNight` | Lowest price per night, before taxes |
| `pricePerNightWithTaxes` | Lowest price per night, with taxes and fees |
| `priceTotal` | Lowest price of the stay, with taxes and fees |
| `taxesAndFees` | Taxes and fees of the stay |
| `rating` | Guest rating out of 5 |
| `reviewCount` | Number of reviews |
| `starRating` | Hotel class |
| `amenities` | Amenities such as Free Wi-Fi or Outdoor pool |
| `offerCount` | Number of booking sites with a rate (with `--offers`) |
| `cheapestOfferSite` | Cheapest booking site (with `--offers`) |
| `cheapestOfferPriceTotal` | Its price for the stay (with `--offers`) |
| `officialSitePriceTotal` | Price on the hotel's own website (with `--offers`) |
| `latitude` | Latitude |
| `longitude` | Longitude |
| `website` | Hotel website |
| `searchLocation` | The search that found the hotel |
| `url` | Google Hotels link with your dates |

`google_hotels_offers.csv` has the hotel's `title`, `checkIn` and `checkOut`, then for each booking site: `site`, `isOfficialSite`, `currency`, `pricePerNight`, `priceTotal` (before taxes), `priceTotalWithTaxes` and `bookingUrl`. The dataset of each run has more columns (rating breakdown, photos, description, Google Maps ids...): add their names to `COLUMNS` in `scrape.py`. The full list is on the [Actor page](https://apify.com/myth84/google-hotels-scraper?fpr=pnpkfc).

## Pricing

The Actor is pay-per-event: from $2.50 per 1,000 hotels on Apify's Free plan, lower on paid plans, with compute and proxies included. Apify's free monthly credit of $5 covers about 1,999 hotels. You pay per hotel saved and nothing else: every booking site's rate comes at no extra charge, `--max-results` caps every search of a run, and in price-tracking mode only the new and changed hotels are saved and charged.

## FAQ

**Do I need to write a scraper or run a browser?** No. The Actor runs in Apify's cloud and is kept up to date when Google changes its pages; your script receives JSON rows.

**Can I follow a fixed list of hotels instead of a search?** Yes: the Actor takes `hotelUrls`, Google Hotels links of precise hotels, each with every booking site's rate. Put them in `run_input` in `build_input`; the [Actor page](https://apify.com/myth84/google-hotels-scraper?fpr=pnpkfc) documents every input field.

**Is there personal data in the output?** No. Rows contain hotel facts (business names), the average rating and the number of reviews; nothing about guests or reviewers. Use the data for analysis, respect Google's terms and the law of your country, and do not republish listings.

## Related

Other Python examples by Flatrow Data Studio, all with a CSV export and a price tracker:

- [airbnb-scraper-python](https://github.com/flatrow-data-studio/airbnb-scraper-python): Airbnb listings, nightly and total prices, ratings and availability.
- [booking-scraper-python](https://github.com/flatrow-data-studio/booking-scraper-python): Booking.com hotel prices, taxes, review scores and stars.
- [amazon-scraper-python](https://github.com/flatrow-data-studio/amazon-scraper-python): Amazon product prices, ratings and price drops.
- [aliexpress-scraper-python](https://github.com/flatrow-data-studio/aliexpress-scraper-python): AliExpress product prices, units sold and shipping.
- [ebay-scraper-python](https://github.com/flatrow-data-studio/ebay-scraper-python): eBay listing prices, condition and units sold.

## License

MIT, see [LICENSE](LICENSE). Google Hotels is a trademark of its owner; this project is not affiliated with Google.
