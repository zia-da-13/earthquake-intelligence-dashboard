"""Store and retrieve earthquake records using SQLite."""

from pathlib import Path
import sqlite3

import pandas as pd


DATABASE_PATH = Path("data") / "earthquakes.db"
TABLE_NAME = "earthquakes"


def create_database_connection(
    database_path: Path = DATABASE_PATH,
) -> sqlite3.Connection:
    """
    Create a connection to the SQLite earthquake database.

    Args:
        database_path: Location of the SQLite database.

    Returns:
        Active SQLite database connection.
    """
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(database_path)


def save_earthquakes_to_database(
    earthquake_dataframe: pd.DataFrame,
    database_path: Path = DATABASE_PATH,
) -> int:
    """
    Save cleaned earthquake records into SQLite.

    Existing earthquakes are replaced when their earthquake IDs match.

    Args:
        earthquake_dataframe: Cleaned earthquake records.
        database_path: Location of the SQLite database.

    Returns:
        Number of records processed.
    """
    if earthquake_dataframe.empty:
        return 0

    database_dataframe = earthquake_dataframe.copy()

    datetime_columns = [
        "event_time",
        "updated_time",
    ]

    for column in datetime_columns:
        if column in database_dataframe.columns:
            database_dataframe[column] = (
                database_dataframe[column]
                .astype(str)
            )

    connection = create_database_connection(
        database_path
    )

    try:
        create_earthquake_table(connection)

        database_records = database_dataframe.to_dict(
            orient="records"
        )

        insert_statement = """
            INSERT INTO earthquakes (
                earthquake_id,
                place,
                magnitude,
                longitude,
                latitude,
                depth_km,
                event_time,
                updated_time,
                status,
                event_type,
                felt_reports,
                significance,
                tsunami_alert,
                details_url,
                severity
            )
            VALUES (
                :earthquake_id,
                :place,
                :magnitude,
                :longitude,
                :latitude,
                :depth_km,
                :event_time,
                :updated_time,
                :status,
                :event_type,
                :felt_reports,
                :significance,
                :tsunami_alert,
                :details_url,
                :severity
            )
            ON CONFLICT(earthquake_id) DO UPDATE SET
                place = excluded.place,
                magnitude = excluded.magnitude,
                longitude = excluded.longitude,
                latitude = excluded.latitude,
                depth_km = excluded.depth_km,
                event_time = excluded.event_time,
                updated_time = excluded.updated_time,
                status = excluded.status,
                event_type = excluded.event_type,
                felt_reports = excluded.felt_reports,
                significance = excluded.significance,
                tsunami_alert = excluded.tsunami_alert,
                details_url = excluded.details_url,
                severity = excluded.severity
        """

        connection.executemany(
            insert_statement,
            database_records,
        )

        connection.commit()

        return len(database_records)

    finally:
        connection.close()


def create_earthquake_table(
    connection: sqlite3.Connection,
) -> None:
    """
    Create the earthquakes table when it does not exist.

    Args:
        connection: Active SQLite connection.
    """
    create_table_statement = """
        CREATE TABLE IF NOT EXISTS earthquakes (
            earthquake_id TEXT PRIMARY KEY,
            place TEXT NOT NULL,
            magnitude REAL,
            longitude REAL,
            latitude REAL,
            depth_km REAL,
            event_time TEXT,
            updated_time TEXT,
            status TEXT,
            event_type TEXT,
            felt_reports REAL,
            significance REAL,
            tsunami_alert INTEGER,
            details_url TEXT,
            severity TEXT
        )
    """

    connection.execute(create_table_statement)
    connection.commit()


def load_earthquakes_from_database(
    database_path: Path = DATABASE_PATH,
) -> pd.DataFrame:
    """
    Load all earthquake records from SQLite.

    Args:
        database_path: Location of the SQLite database.

    Returns:
        Earthquake records as a pandas DataFrame.
    """
    if not database_path.exists():
        return pd.DataFrame()

    connection = create_database_connection(
        database_path
    )

    try:
        query = """
            SELECT
                earthquake_id,
                place,
                magnitude,
                longitude,
                latitude,
                depth_km,
                event_time,
                updated_time,
                status,
                event_type,
                felt_reports,
                significance,
                tsunami_alert,
                details_url,
                severity
            FROM earthquakes
            ORDER BY event_time DESC
        """

        earthquake_dataframe = pd.read_sql_query(
            query,
            connection,
        )

    finally:
        connection.close()

    datetime_columns = [
        "event_time",
        "updated_time",
    ]

    for column in datetime_columns:
        if column in earthquake_dataframe.columns:
            earthquake_dataframe[column] = pd.to_datetime(
                earthquake_dataframe[column],
                utc=True,
                errors="coerce",
            )

    return earthquake_dataframe


def get_database_record_count(
    database_path: Path = DATABASE_PATH,
) -> int:
    """
    Return the total number of earthquake records in SQLite.

    Args:
        database_path: Location of the SQLite database.

    Returns:
        Number of stored earthquake records.
    """
    if not database_path.exists():
        return 0

    connection = create_database_connection(
        database_path
    )

    try:
        create_earthquake_table(connection)

        cursor = connection.execute(
            "SELECT COUNT(*) FROM earthquakes"
        )

        result = cursor.fetchone()

        if result is None:
            return 0

        return int(result[0])

    finally:
        connection.close()