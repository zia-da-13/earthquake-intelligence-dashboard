from src.earthquake_api import fetch_earthquake_data


def main():
    print("Downloading live earthquake data...\n")

    earthquake_data = fetch_earthquake_data()

    print("Download successful!")
    print(f"Number of earthquakes: {len(earthquake_data['features'])}")

    first = earthquake_data["features"][0]

    print("\nLatest Earthquake")
    print("----------------------------")
    print(f"Location : {first['properties']['place']}")
    print(f"Magnitude: {first['properties']['mag']}")
    print(f"Time     : {first['properties']['time']}")


if __name__ == "__main__":
    main()