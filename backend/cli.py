"""CLI for offline ingestion and database management."""

import argparse
from pathlib import Path
import sys

from backend.db import DEFAULT_DB_PATH, init_db
from backend.services.ingestion import (
    get_db_stats,
    ingest_actuals,
    ingest_forecasts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Elexon BMRS Offline Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize database tables")
    init_parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH))

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingest actuals and forecasts from Elexon")
    ingest_parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH))
    ingest_parser.add_argument("--settlement-from", type=str, default="2025-12-30", help="Actuals settlementDateFrom (YYYY-MM-DD)")
    ingest_parser.add_argument("--settlement-to", type=str, default="2026-02-02", help="Actuals settlementDateTo (YYYY-MM-DD)")
    ingest_parser.add_argument("--publish-from", type=str, default="2025-12-29T00:00:00Z", help="Forecasts publishDateTimeFrom (ISO UTC)")
    ingest_parser.add_argument("--publish-to", type=str, default="2026-02-02T23:59:59Z", help="Forecasts publishDateTimeTo (ISO UTC)")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Display database summary stats")
    stats_parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH))

    args = parser.parse_args()

    if args.command == "init":
        db_path = Path(args.db_path)
        print(f"Initializing database schema at: {db_path}")
        init_db(db_path)
        print("Database initialized successfully.")

    elif args.command == "ingest":
        db_path = Path(args.db_path)
        print(f"Target database: {db_path}")

        print(f"\n1. Ingesting actual wind generation (FUELHH) from {args.settlement_from} to {args.settlement_to}...")
        act_rec, act_ins, act_skp = ingest_actuals(
            settlement_date_from=args.settlement_from,
            settlement_date_to=args.settlement_to,
            fuel_type="WIND",
            db_path=db_path,
        )
        print(f"   Actuals: received={act_rec}, inserted={act_ins}, skipped={act_skp}")

        print(f"\n2. Ingesting wind forecasts (WINDFOR) from {args.publish_from} to {args.publish_to}...")
        fc_rec, fc_ins, fc_skp = ingest_forecasts(
            publish_date_time_from=args.publish_from,
            publish_date_time_to=args.publish_to,
            db_path=db_path,
        )
        print(f"   Forecasts: received={fc_rec}, inserted={fc_ins}, skipped={fc_skp}")

        print("\nIngestion complete.")
        stats = get_db_stats(db_path)
        print(f"Stats: {stats}")

    elif args.command == "stats":
        db_path = Path(args.db_path)
        stats = get_db_stats(db_path)
        print(f"Database statistics for {db_path}:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
