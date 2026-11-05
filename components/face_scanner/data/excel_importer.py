import pandas as pd
import sqlite3
from pathlib import Path

# File locations
BASE_DIR = Path(__file__).resolve().parents[3]

EXCEL_FILE = BASE_DIR / "test_data" / "test_records.xlsx"
DATABASE_FILE = (
    BASE_DIR
    / "components"
    / "face_scanner"
    / "data"
    / "aeroid_parents.db"
)


def import_parents():

    if not EXCEL_FILE.exists():
        print("Excel file not found!")
        return

    try:
        data = pd.read_excel(EXCEL_FILE, sheet_name="TestData")
    except Exception as error:
        print(f"Could not read Excel file: {error}")
        return

    required_columns = [
        "Image Code",
        "Image Filename",
        "Students",
        "Test ID"
    ]

    # Validate columns
    if not all(column in data.columns for column in required_columns):
        print("Excel columns are missing!")
        print("Found columns:", data.columns.tolist())
        return

    data = data[required_columns].copy()

    # Remove completely empty rows
    data.dropna(how="all", inplace=True)

    # Clean values
    for column in required_columns:
        data[column] = data[column].astype("string").str.strip()

    # Validate missing values
    if data.isna().any().any() or (data == "").any().any():
        print("Missing values found!")
        return

    # Validate duplicate IDs
    for column in ["Image Code", "Image Filename", "Test ID"]:
        if data[column].duplicated().any():
            print(f"Duplicate values found in {column}!")
            return

    connection = sqlite3.connect(DATABASE_FILE)

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS parents (
                image_code TEXT PRIMARY KEY,
                image_filename TEXT UNIQUE NOT NULL,
                parent_name TEXT NOT NULL,
                test_id TEXT UNIQUE NOT NULL
            )
        """)

        # Prepare records
        records = [
            (
                row["Image Code"],
                row["Image Filename"],
                row["Students"],
                row["Test ID"]
            )
            for _, row in data.iterrows()
        ]

        # Import records
        connection.executemany("""
            INSERT INTO parents
            (image_code, image_filename, parent_name, test_id)
            VALUES (?, ?, ?, ?)
        """, records)

        connection.commit()

        print("\nImport successful!")
        print(f"Parent records imported: {len(records)}")
        print(f"Database: {DATABASE_FILE}")

    except sqlite3.IntegrityError:
        connection.rollback()
        print("Import stopped: A duplicate record already exists.")

    except Exception as error:
        connection.rollback()
        print(f"Import failed: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    import_parents()
