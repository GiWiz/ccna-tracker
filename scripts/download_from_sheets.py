import gspread
import csv
import os
import sys

SHEET_ID = "1IbXOQClp9Z6icLKtPTJ2bDoJP4bQKnk2iksrNG2Vcqk"
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned", "current_schedule.csv")
MASTER_LIST_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned", "current_master_list.csv")

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
        sys.exit(1)

    print(f"Successfully opened sheet: {sh.title}")
    
    try:
        worksheet = sh.worksheet("Schedule")
        data = worksheet.get_all_values()
        print(f"Downloaded {len(data)} rows from Schedule.")
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        print(f"Saved current schedule state to {OUTPUT_CSV}")
    except gspread.exceptions.WorksheetNotFound:
        print("ERROR: Schedule tab not found in Google Sheets")
        sys.exit(1)
        
    try:
        master_ws = sh.worksheet("Master_Task_List")
        m_data = master_ws.get_all_values()
        print(f"Downloaded {len(m_data)} rows from Master_Task_List.")
        with open(MASTER_LIST_CSV, 'w', encoding='utf-8', newline='') as mf:
            mwriter = csv.writer(mf)
            mwriter.writerows(m_data)
        print(f"Saved current master list state to {MASTER_LIST_CSV}")
    except gspread.exceptions.WorksheetNotFound:
        print("INFO: Master_Task_List tab not found in Google Sheets. It will be created on the next upload.")

if __name__ == "__main__":
    main()
