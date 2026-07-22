"""Run the earthquake extraction and storage pipeline."""

from pathlib import Path

from src.data_cleaning import create_earthquake_dataframe
from src.database import (
    get_database_record_count,
    save_earthquakes_to_database,
)
from src.earthquake_api import fetch_earthquake_data


CSV_OUTPUT_PATH = Path("data") / "earthquakes.csv"


def main() -> None:
    """
    Retrieve, clean, save, and summarize earthquake data.
    """
    print("=" * 60)
    print("GLOBAL EARTHQUAKE DATA PIPELINE")
    print("=" * 60)

    print("\n1. Downloading live data from USGS...")

    try:
        earthquake_data = fetch_earthquake_data()

    except Exception as error:
        print(
            f"Unable to retrieve earthquake data: {error}"
        )
        return

    print("   Download successful.")

    print("\n2. Cleaning earthquake records...")

    earthquake_dataframe = create_earthquake_dataframe(
        earthquake_data
    )

    if earthquake_dataframe.empty:
        print("   No valid earthquake records were returned.")
        return

    print(
        f"   Cleaned records: "
        f"{len(earthquake_dataframe):,}"
    )

    print("\n3. Saving data to CSV...")

    CSV_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    earthquake_dataframe.to_csv(
        CSV_OUTPUT_PATH,
        index=False,
    )

    print(f"   CSV saved to: {CSV_OUTPUT_PATH}")

    print("\n4. Saving data to SQLite...")

    try:
        processed_records = save_earthquakes_to_database(
            earthquake_dataframe
        )

        total_database_records = (
            get_database_record_count()
        )

    except Exception as error:
        print(
            f"   Unable to save data to SQLite: {error}"
        )
        return

    print(
        f"   Records processed: "
        f"{processed_records:,}"
    )

    print(
        f"   Total records in database: "
        f"{total_database_records:,}"
    )

    largest_earthquake = earthquake_dataframe.loc[
        earthquake_dataframe["magnitude"].idxmax()
    ]

    print("\n5. Largest earthquake in the current feed")
    print("-" * 60)

    print(
        f"Location: "
        f"{largest_earthquake['place']}"
    )

    print(
        f"Magnitude: "
        f"{largest_earthquake['magnitude']:.1f}"
    )

    print(
        f"Severity: "
        f"{largest_earthquake['severity']}"
    )

    print(
        f"Depth: "
        f"{largest_earthquake['depth_km']:.1f} km"
    )

    print(
        f"Event time: "
        f"{largest_earthquake['event_time']}"
    )

    print("\nPipeline completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()