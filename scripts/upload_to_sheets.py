"""
Phase 4: Google Sheets Importer
Reads the generated CSV files and writes them directly to the Google Sheet.
Uses gspread and a service account credentials JSON.
"""
import gspread
import csv
import os
import sys

SHEET_ID = "1IbXOQClp9Z6icLKtPTJ2bDoJP4bQKnk2iksrNG2Vcqk"
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")

# Map of tab names to their source CSV files
TABS_TO_IMPORT = {
    "Schedule": "final_schedule_v3.csv",
    "Boson_Master_Index": "boson_labs_cleaned.csv",
    "Jeremy_Curriculum": "jeremy_curriculum.csv",
    "Topic_Mapping": "topic_mapping.csv"
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")

def read_csv(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return list(reader)

def main():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: Credentials file not found at {CREDENTIALS_FILE}")
        sys.exit(1)

    print("Authenticating with Google Sheets...")
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    
    try:
        sh = gc.open_by_key(SHEET_ID)
    except Exception as e:
        print(f"ERROR opening sheet: {e}")
        print("Did you share the sheet with the service account email?")
        sys.exit(1)

    print(f"Successfully opened sheet: {sh.title}")

    # Delete existing default "Sheet1" if we are going to create our own tabs
    # But we'll do this at the end to ensure we don't delete the last tab before creating new ones.

    for tab_name, csv_filename in TABS_TO_IMPORT.items():
        print(f"\nProcessing tab: {tab_name}")
        
        # Read CSV data
        data = read_csv(csv_filename)
        if not data:
            print(f"WARNING: No data found in {csv_filename}, skipping.")
            continue
            
        # Get or create worksheet
        try:
            worksheet = sh.worksheet(tab_name)
            print("  Worksheet exists. Clearing old data...")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            print("  Worksheet does not exist. Creating...")
            # Create with enough rows and cols
            rows = max(len(data) + 10, 100)
            cols = max(len(data[0]) + 2, 10)
            worksheet = sh.add_worksheet(title=tab_name, rows=str(rows), cols=str(cols))
            
        # Update data
        print(f"  Uploading {len(data)} rows...")
        worksheet.update(values=data, range_name=f"A1")
        
        # Formatting for Schedule tab
        if tab_name == "Schedule":
            # Add checkboxes to the 'Done' column (Column A) for rows 2 to len(data)
            # In gspread, we can use DataValidationRule
            from gspread.utils import a1_to_rowcol
            
            # Format header
            worksheet.format("A1:I1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            
            # Add checkboxes to column A
            validation_rule = {
                "condition": {
                    "type": "BOOLEAN"
                },
                "showCustomUi": True
            }
            # The range is A2:A[len(data)]
            worksheet.client.request(
                'post',
                f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}:batchUpdate',
                json={
                    "requests": [
                        {
                            "setDataValidation": {
                                "range": {
                                    "sheetId": worksheet.id,
                                    "startRowIndex": 1,
                                    "endRowIndex": len(data),
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 1
                                },
                                "rule": validation_rule
                            }
                        }
                    ]
                }
            )
            print("  Added checkboxes to Schedule -> Done column")

    # Clean up default Sheet1 if it exists
    try:
        sheet1 = sh.worksheet("Sheet1")
        sh.del_worksheet(sheet1)
        print("\nRemoved default 'Sheet1'")
    except gspread.exceptions.WorksheetNotFound:
        pass

    print("\n✅ All imports completed successfully!")

if __name__ == "__main__":
    main()
