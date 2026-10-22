"""Google Hotels scraper in Python: hotel prices by booking site, to CSV.

Runs the Google Hotels Scraper (an Apify Actor) for one or more searches and
saves one row per hotel to a CSV file; with --offers, also one row per hotel
and booking site to a second CSV file (rate parity).

    export APIFY_TOKEN="<your-apify-token>"
    python scrape.py "hotels in Lisbon" --check-in 2026-11-20 --check-out 2026-11-23
    python scrape.py "hotels in Rome" --offers --max-results 20
"""

import argparse
import csv
import json
import os
import sys
from decimal import Decimal

from apify_client import ApifyClient

ACTOR = "myth84/google-hotels-scraper"

# Columns written to the CSV. Every row of the dataset has more (see the README).
COLUMNS = [
    "platformListingId",
    "title",
    "propertyType",
    "city",
    "checkIn",
    "checkOut",
    "nights",
    "currency",
    "pricePerNight",
    "pricePerNightWithTaxes",
    "priceTotal",
    "taxesAndFees",
    "rating",
    "reviewCount",
    "starRating",
    "amenities",
    "offerCount",
    "cheapestOfferSite",
    "cheapestOfferPriceTotal",
    "officialSitePriceTotal",
    "latitude",
    "longitude",
    "website",
    "searchLocation",
    "url",
]

# Keys of each booking site's rate in the offers column, written with --offers.
OFFER_COLUMNS = [
    "site",
    "isOfficialSite",
    "currency",
    "pricePerNight",
    "priceTotal",
    "priceTotalWithTaxes",
    "bookingUrl",
]


def make_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("queries", nargs="+", help='searches as typed on Google, e.g. "hotels in Lisbon"')
    parser.add_argument("--check-in", help="check-in date, YYYY-MM-DD (with --check-out)")
    parser.add_argument("--check-out", help="check-out date, YYYY-MM-DD")
    parser.add_argument("--check-in-days", type=int, default=30,
                        help="without fixed dates: check-in in N days, recomputed at every run (default 30)")
    parser.add_argument("--nights", type=int, default=3, help="without fixed dates: nights of the stay (default 3)")
    parser.add_argument("--adults", type=int, default=2)
    parser.add_argument("--currency", default="USD", help="ISO code: USD, EUR, GBP, JPY...")
    parser.add_argument("--max-results", type=int, default=50,
                        help="hotels per search (default 50); you pay per hotel saved")
    parser.add_argument("--max-charge", type=Decimal, help="stop the run once it has cost this many USD")
    return parser


def build_input(args):
    if bool(args.check_in) != bool(args.check_out):
        sys.exit("--check-in and --check-out go together.")
    run_input = {
        "searchQueries": args.queries,
        "adults": args.adults,
        "currency": args.currency,
        "maxResults": args.max_results,
    }
    if args.check_in:
        run_input["checkIn"] = args.check_in
        run_input["checkOut"] = args.check_out
    else:
        run_input["checkInDaysFromNow"] = args.check_in_days
        run_input["nights"] = args.nights
    return run_input


def run_actor(run_input, max_charge=None):
    """Runs the Actor, waits for it to finish and returns the rows of its dataset."""
    if not os.environ.get("APIFY_TOKEN"):
        sys.exit("Set APIFY_TOKEN first: Apify Console > Settings > API & Integrations.")
    client = ApifyClient(os.environ["APIFY_TOKEN"])
    run = client.actor(ACTOR).call(run_input=run_input, max_total_charge_usd=max_charge)
    if run is None:
        sys.exit("The run could not be started.")
    status = getattr(run.status, "value", run.status)  # SUCCEEDED, FAILED, TIMED-OUT...
    if status != "SUCCEEDED":
        sys.exit(f"The run ended as {status}: open its log in Apify Console.")
    return list(client.dataset(run.default_dataset_id).iterate_items())


def cell(value):
    """Lists and objects as JSON text, so that every CSV row has the same columns."""
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value


def write_csv(rows, path, columns=COLUMNS, append=False):
    new_file = not (append and os.path.exists(path))
    with open(path, "a" if append else "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(columns)
        for row in rows:
            writer.writerow([cell(row.get(column)) for column in columns])


def write_offers_csv(rows, path):
    """One line per hotel and booking site, cheapest site first."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "checkIn", "checkOut"] + OFFER_COLUMNS)
        for row in rows:
            for offer in row.get("offers") or []:
                writer.writerow([row["title"], row["checkIn"], row["checkOut"]]
                                + [offer.get(column) for column in OFFER_COLUMNS])


def main():
    parser = make_parser("Scrape Google Hotels prices, ratings and booking-site rates to CSV.")
    parser.add_argument("--offers", action="store_true",
                        help="add every booking site's rate for each hotel (no extra charge)")
    parser.add_argument("--output", default="google_hotels.csv", help="CSV file (default google_hotels.csv)")
    parser.add_argument("--offers-output", default="google_hotels_offers.csv",
                        help="CSV file of the booking-site rates, with --offers (default google_hotels_offers.csv)")
    args = parser.parse_args()

    run_input = build_input(args)
    if args.offers:
        run_input["includeOffers"] = True
    rows = run_actor(run_input, args.max_charge)
    write_csv(rows, args.output)
    print(f"{len(rows)} hotels saved to {args.output}")
    if args.offers:
        write_offers_csv(rows, args.offers_output)
        print(f"Booking-site rates saved to {args.offers_output}")

    priced = sorted((row for row in rows if row.get("priceTotal") is not None), key=lambda row: row["priceTotal"])
    for row in priced[:5]:
        cheapest = f'  cheapest on {row["cheapestOfferSite"]}' if row.get("cheapestOfferSite") else ""
        print(f'{row["priceTotal"]:>9} {row["currency"]} for {row["nights"]} nights  '
              f'{row.get("rating") or "-":>3}/5  {row["title"]}{cheapest}')


if __name__ == "__main__":
    main()
