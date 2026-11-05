import pandas as pd

file_path = input("Enter Excel file path: ").strip().strip('"')

try:
    data = pd.read_excel(file_path)

    print("\nExcel columns:")
    for column in data.columns:
        print("-", column)

    print("\nFirst 5 rows:")
    print(data.head())

except Exception as error:
    print("Error:", error)