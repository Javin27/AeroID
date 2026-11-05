
import sqlite3
import pandas as pd
from pathlib import Path
import re


def clean_table_name(name):
    name = re.sub(r"\W+", "_", name.strip())
    return name or "records"


def clean_column_name(name):
    name = re.sub(r"\W+", "_", str(name).strip())
    return name or "unnamed_column"


def convert_excel_to_db():

    print("\n===== EXCEL TO SQLITE CONVERTER =====\n")

    # Get Excel path
    excel_path = Path(
        input("Enter Excel file path: ").strip().strip('"')
    )

    if not excel_path.exists() or not excel_path.is_file():
        print("Error: Excel file not found.")
        return

    if excel_path.suffix.lower() not in [".xlsx", ".xls"]:
        print("Error: Please provide an Excel file.")
        return

    try:
        # Read Excel
        df = pd.read_excel(excel_path)

        if df.empty:
            print("Error: Excel file has no records.")
            return

        # Clean column names
        df.columns = [clean_column_name(c) for c in df.columns]

        if len(set(df.columns)) != len(df.columns):
            print("Error: Duplicate column names after cleaning.")
            return

        # Create database beside Excel
        db_path = excel_path.with_suffix(".db")

        # Ask before overwriting
        if db_path.exists():
            choice = input(
                f"{db_path.name} already exists. Replace it? (y/n): "
            ).strip().lower()

            if choice != "y":
                print("Conversion cancelled.")
                return

            db_path.unlink()

        # Create table name from Excel filename
        table_name = clean_table_name(excel_path.stem)

        # Import into SQLite
        with sqlite3.connect(db_path) as connection:

            df.to_sql(
                table_name,
                connection,
                if_exists="fail",
                index=False
            )

        print("\nConversion successful!")
        print(f"Excel file: {excel_path}")
        print(f"Database:   {db_path}")
        print(f"Table:      {table_name}")
        print(f"Records:    {len(df)}")
        print(f"Columns:    {len(df.columns)}")

    except Exception as error:
        print(f"\nConversion failed: {error}")


if __name__ == "__main__":
    convert_excel_to_db()
