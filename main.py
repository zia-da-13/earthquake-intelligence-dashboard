from pathlib import Path

from src.data_cleaning import create_earthquake_dataframe
from src.earthquake_api import fetch_earthquake_data


OUTPUT_FILE = Path("data") / "earthquakes.csv"


def main():
    print("Downloading live earthquake data...")

    try:
        earthquake_data = fetch_earthquake_data()
        earthquake_dataframe = create_earthquake_dataframe(
            earthquake_data
        )
    except Exception as error:
        print(f"Error: {error}")
        return

    if earthquake_dataframe.empty:
        print("No earthquake records were returned.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    earthquake_dataframe.to_csv(OUTPUT_FILE, index=False)

    largest_earthquake = earthquake_dataframe.loc[
        earthquake_dataframe["magnitude"].idxmax()
    ]

    print("\nDownload and cleaning successful!")
    print(f"Total earthquakes: {len(earthquake_dataframe)}")
    print(f"CSV saved to: {OUTPUT_FILE}")

    print("\nLargest earthquake")
    print("----------------------------")
    print(f"Location: {largest_earthquake['place']}")
    print(f"Magnitude: {largest_earthquake['magnitude']}")
    print(f"Depth: {largest_earthquake['depth_km']} km")
    print(f"Time: {largest_earthquake['event_time']}")

    print("\nMost recent earthquake records")
    print(
        earthquake_dataframe[
            ["event_time", "place", "magnitude", "depth_km"]
        ].head(10)
    )


if __name__ == "__main__":
    main()