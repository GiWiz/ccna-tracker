import csv
import os
import datetime
import json
import requests
from datetime import timedelta

JEREMY_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'jeremy_curriculum.csv')
MAPPING_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'topic_mapping.csv')
BOSON_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'boson_labs_cleaned.csv')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'final_schedule_v3.csv')

HOLIDAYS_2026 = [
    datetime.date(2026, 9, 7),   # Labor Day
    datetime.date(2026, 10, 12), # Columbus Day
]

# Map categories to Boson labs based on official syllabus
BOSON_CATEGORIES = {
    # Network Fundamentals
    'Explore Cisco Devices': 'Network Fundamentals',
    'Router Basics': 'Network Fundamentals',
    'Switch Basics': 'Network Fundamentals',
    'Configure a Cisco Device': 'Network Fundamentals',
    'Interpret Interface Errors': 'Network Fundamentals',
    'Configure Global IPv4 Addressing': 'Network Fundamentals',
    'Configure RFC 1918 IP Addressing': 'Network Fundamentals',
    'Subnet an IPv4 Network': 'Network Fundamentals',
    'Configure VLSM on an IPv4 Network': 'Network Fundamentals',
    'Configure IPv6 Address Types': 'Network Fundamentals',
    'Configure IPv6 by Using Modified EUI-64': 'Network Fundamentals',
    'Explore the MAC Address Table': 'Network Fundamentals',
    'Implement IPv4 Addressing': 'Network Fundamentals',
    'Implement IPv6 Addressing': 'Network Fundamentals',
    'Boson CCNA Challenge Lab 1': 'Network Fundamentals',
    # Network Access
    'Explore and Configure Switch Access Ports': 'Network Access',
    'Explore and Configure Switch Trunk Ports': 'Network Access',
    'Configure InterVLAN Routing': 'Network Access',
    'Explore the Native VLAN': 'Network Access',
    'Configure and Verify VTP': 'Network Access',
    'Configure and Verify CDP': 'Network Access',
    'Configure and Verify LLDP': 'Network Access',
    'Configure Layer 2 EtherChannel LACP': 'Network Access',
    'Configure Layer 3 EtherChannel LACP and Load Balancing': 'Network Access',
    'Explore Spanning Tree Protocol Port Roles': 'Network Access',
    'Explore Spanning Tree Protocol Port States and PortFast': 'Network Access',
    'Configure a Wireless LAN by Using the WLC GUI': 'Network Access',
    'Implement InterVLAN Routing': 'Network Access',
    'Implement CDP and LLDP': 'Network Access',
    'Implement PVST+': 'Network Access',
    'Boson CCNA Challenge Lab 2': 'Network Access',
    # IP Connectivity
    'Explore the Routing Table': 'IP Connectivity',
    'Route Selection by Using Administrative Distance': 'IP Connectivity',
    'Route Selection by Using Routing Protocol Metric': 'IP Connectivity',
    'Manually Configure Default Routes on IPv4 Networks': 'IP Connectivity',
    'Manually Configure Default Routes on IPv6 Networks': 'IP Connectivity',
    'Manually Configure Network Routes on IPv4 Networks': 'IP Connectivity',
    'Manually Configure Network Routes on IPv6 Networks': 'IP Connectivity',
    'Manually Configure Host Routes on IPv4 Networks': 'IP Connectivity',
    'Manually Configure Host Routes on IPv6 Networks': 'IP Connectivity',
    'Configure OSPFv2 Adjacencies': 'IP Connectivity',
    'Configure Point-to-Point OSPFv2': 'IP Connectivity',
    'Explore OSPFv2 DR and BDR Router Selection': 'IP Connectivity',
    'Explore and Configure OSPFv2 Router IDs': 'IP Connectivity',
    'Plan and Configure Single-Area OSPF': 'IP Connectivity',
    'Explore HSRP': 'IP Connectivity',
    'Explore VRRP': 'IP Connectivity',
    'Implement Route Selection': 'IP Connectivity',
    'Implement Static and Default Routes': 'IP Connectivity',
    'Implement Single-Area OSPFv2': 'IP Connectivity',
    'Implement HSRP': 'IP Connectivity',
    'Implement VRRP': 'IP Connectivity',
    'Troubleshoot an OSPFv2 Configuration': 'IP Connectivity',
    'Boson CCNA Challenge Lab 3': 'IP Connectivity',
    # IP Services
    'Configure Static NAT': 'IP Services',
    'Configure Dynamic NAT': 'IP Services',
    'Configure PAT': 'IP Services',
    'Configure an NTP Server': 'IP Services',
    'Configure an NTP Client': 'IP Services',
    'Configure and Test a DNS Server': 'IP Services',
    'Explore Syslog Output': 'IP Services',
    'Explore and Configure Syslog Levels': 'IP Services',
    'Configure DHCP for IPv4 Networks': 'IP Services',
    'Configure DHCP Relay for IPv4 Networks': 'IP Services',
    'Configure SSH': 'IP Services',
    'Explore and Configure TFTP': 'IP Services',
    'Explore and Configure FTP': 'IP Services',
    'Implement NAT': 'IP Services',
    'Implement NTP': 'IP Services',
    'Implement DNS': 'IP Services',
    'Implement DHCP': 'IP Services',
    'Implement SSH': 'IP Services',
    'Boson CCNA Challenge Lab 4': 'IP Services',
    # Security Fundamentals
    'Configure the Enable Password': 'Security Fundamentals',
    'Configure the Enable Secret Password': 'Security Fundamentals',
    'Configure Local User Accounts': 'Security Fundamentals',
    'Secure the Console and VTY Ports': 'Security Fundamentals',
    'Encrypt Passwords on a Cisco Device': 'Security Fundamentals',
    'Explore Password Complexity': 'Security Fundamentals',
    'Explore and Configure Standard Numbered ACLs': 'Security Fundamentals',
    'Explore and Configure Extended Numbered ACLs': 'Security Fundamentals',
    'Explore and Configured Numbered IP ACLs': 'Security Fundamentals',
    'Configure Standard Named ACLs': 'Security Fundamentals',
    'Configure Extended Named ACLs': 'Security Fundamentals',
    'Explore and Configure Port Security': 'Security Fundamentals',
    'Explore AAA': 'Security Fundamentals',
    'Implement Passwords': 'Security Fundamentals',
    'Implement Local User Accounts': 'Security Fundamentals',
    'Implement Standard ACLs': 'Security Fundamentals',
    'Implement Extended ACLs': 'Security Fundamentals',
    'Implement Port Security': 'Security Fundamentals',
    'Troubleshoot Port Security': 'Security Fundamentals',
    'Troubleshoot ACLs': 'Security Fundamentals',
    'Troubleshooting ACLs 1: Extended ACLs': 'Security Fundamentals',
    'Troubleshooting ACLs 2: Standard ACLs': 'Security Fundamentals',
    'Troubleshooting ACLs 3: Named ACLs': 'Security Fundamentals',
    'Boson CCNA Challenge Lab 5': 'Security Fundamentals',
    # Automation and Programmability
    'Compare a Traditional Network to a Controller-Based Network': 'Automation and Programmability',
    'Explore HTTP Server Verbs': 'Automation and Programmability',
    'Submit and Explore Ansible, Chef, and Puppet Queries': 'Automation and Programmability',
    'Obtain and Interpret JSON Output': 'Automation and Programmability',
    # Demo Labs
    'Configuration Demo 1': 'Demo Labs',
    'Using NetSim Online': 'Demo Labs'
}

def get_daily_limits(current_date):
    """Returns (target_minutes, max_minutes) for a given date"""
    if current_date.weekday() >= 5 or current_date in HOLIDAYS_2026:
        return 240, 360
    return 120, 120

def load_data():
    boson_metadata = {}
    with open(BOSON_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lab_id = row['Lab_ID']
            task_count = int(row['Task_Count'] or 0)
            cmd_count = int(row['Command_Count'] or 0)
            est_time = (task_count * 5) + (cmd_count * 1)
            est_time = max(10, min(est_time, 45))
            
            title = row['Lab_Title']
            category = BOSON_CATEGORIES.get(title, 'Unknown Category')
            formatted_title = f"{category} -> {title}"
            
            boson_metadata[lab_id] = {
                'title': formatted_title,
                'raw_title': title,
                'est_min': est_time
            }

    jeremy_days = {}
    with open(JEREMY_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            day_str = row['Day']
            if not day_str: continue
            day = int(day_str)
            title = row['Title']
            duration_sec = int(row['Study_Time_Estimate_Seconds'])
            duration_min = duration_sec / 60.0
            type_col = row['Type']
            
            if day not in jeremy_days:
                jeremy_days[day] = {'lectures': [], 'labs': [], 'boson': []}
                
            if type_col == 'Lab':
                pt_attempt = 15
                if duration_min > 20: pt_attempt = 40
                elif duration_min > 12: pt_attempt = 25
                
                jeremy_days[day]['labs'].append({
                    'title': title, 
                    'min': duration_min, 
                    'pt_attempt_min': pt_attempt,
                    'is_pt': True
                })
            elif type_col in ('Extra', 'Toolkit', 'Quiz'):
                # We skip these per user request
                continue
            else:
                jeremy_days[day]['lectures'].append({'title': title, 'min': duration_min})

    with open(MAPPING_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            day = int(row['Day'])
            if row['Boson_Lab_IDs']:
                ids = [x.strip() for x in row['Boson_Lab_IDs'].split(';')]
                for lab_id in ids:
                    if lab_id in boson_metadata:
                        jeremy_days[day]['boson'].append({
                            'title': boson_metadata[lab_id]['title'],
                            'raw_title': boson_metadata[lab_id]['raw_title'],
                            'min': boson_metadata[lab_id]['est_min']
                        })

    return jeremy_days

def send_discord_notification(is_on_track, missed_days=0, mega_lab_date=None):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url:
        return

    if is_on_track:
        content = "✅ **CCNA Tracker Update**: Great job! You are perfectly on track. Your schedule has been updated with today's tasks."
    else:
        content = f"⚠️ **CCNA Tracker Update**: It looks like you missed {missed_days} day(s) of study! Don't worry, I've automatically pushed your schedule forward. Your new Mega Lab date is now **{mega_lab_date}**."

    data = {"content": content}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def generate_schedule():
    jeremy_days = load_data()
    
    # Load state from Google Sheets download
    completed_items = set()
    history_rows = []
    last_history_date = datetime.date(2026, 7, 19)
    
    try:
        with open('data/cleaned/current_schedule.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Done') == 'TRUE':
                    history_rows.append(row)
                    # Parse date
                    m, d, y = map(int, row['Date'].split('/'))
                    row_date = datetime.date(y, m, d)
                    if row_date > last_history_date:
                        last_history_date = row_date
                    
                    if row.get('Lectures'):
                        for l in row['Lectures'].split(' | '): completed_items.add(l.strip())
                    if row.get('PT_Labs'):
                        for pt in row['PT_Labs'].split(' | '): completed_items.add(pt.strip())
                    if row.get('Boson_Labs'):
                        for b in row['Boson_Labs'].split(' | '): completed_items.add(b.strip())
    except FileNotFoundError:
        pass
    
    # Calculate start date for future scheduling
    today = datetime.date.today()
    start_date = max(today, last_history_date + timedelta(days=1))
    current_date = start_date
    
    schedule = []
    
    curr_day = {
        'date': current_date,
        'j_days_involved': set(),
        'lectures': [],
        'pt_labs': [],
        'boson_labs': [],
        'total_min': 0
    }
    
    def close_day():
        nonlocal current_date, curr_day
        if curr_day['total_min'] > 0:
            schedule.append(curr_day)
        current_date += timedelta(days=1)
        curr_day = {
            'date': current_date,
            'j_days_involved': set(),
            'lectures': [],
            'pt_labs': [],
            'boson_labs': [],
            'total_min': 0
        }

    def add_item(item, category, j_day, duration):
        nonlocal current_date, curr_day
        
        target_min, max_min = get_daily_limits(current_date)
        
        if curr_day['total_min'] + duration > max_min and curr_day['total_min'] > 0:
            close_day()
            
        curr_day['j_days_involved'].add(str(j_day))
        curr_day[category].append(item)
        curr_day['total_min'] += duration
        
        if curr_day['total_min'] >= target_min:
            pass

    # Load pending labs
    pending_labs = set()
    try:
        with open(r"C:\Users\swrav\.gemini\antigravity-ide\brain\beffb45c-4358-4cc5-ac87-97c70f1f958b\scratch\pending_boson.json", 'r', encoding='utf-8') as f:
            pending_labs = set(json.load(f))
        print(f"Loaded {len(pending_labs)} pending labs in generate_schedule.py")
    except Exception as e:
        print("Error loading JSON:", e)

    # Build temp items
    temp_schedule_items = []
    catchup_queue = []
    
    for j_day in sorted(jeremy_days.keys()):
        data = jeremy_days[j_day]
        for lec in data['lectures']: 
            if lec['title'] not in completed_items:
                temp_schedule_items.append({'item': lec['title'], 'cat': 'lectures', 'j_day': j_day, 'min': lec['min']})
        for pt in data['labs']: 
            if pt['title'] not in completed_items:
                temp_schedule_items.append({'item': pt['title'], 'cat': 'pt_labs', 'j_day': j_day, 'min': pt['min'] + pt['pt_attempt_min']})
        for boson in data['boson']: 
            if boson['title'] in completed_items:
                continue
            if j_day < 26 and boson['raw_title'] in pending_labs:
                catchup_queue.append({'item': boson['title'], 'cat': 'boson_labs', 'j_day': 'Catch-up', 'min': boson['min']})
            else:
                temp_schedule_items.append({'item': boson['title'], 'cat': 'boson_labs', 'j_day': j_day, 'min': boson['min']})

    first_day_64 = True
    for item in temp_schedule_items:
        if item['j_day'] == 64 and first_day_64:
            close_day()
            
            # Process Catch-up week queue
            print(f"Catch-up queue has {len(catchup_queue)} items.")
            for catchup_item in catchup_queue:
                add_item(catchup_item['item'], catchup_item['cat'], catchup_item['j_day'], catchup_item['min'])
            close_day()
            
            # Push Day 64 to land on October 3rd (Saturday), or the next Saturday if it overflows
            target_date = datetime.date(2026, 10, 3)
            if current_date < target_date:
                current_date = target_date
            else:
                while current_date.weekday() != 5: # Saturday
                    current_date += timedelta(days=1)
            curr_day['date'] = current_date
            first_day_64 = False
        add_item(item['item'], item['cat'], item['j_day'], item['min'])
    close_day()

    # Determine tracking status
    missed_days = (today - (last_history_date + timedelta(days=1))).days
    is_on_track = missed_days <= 0
    
    mega_lab_date = None
    for row in schedule:
        if '64' in row['j_days_involved']:
            mega_lab_date = row['date'].strftime('%A, %B %d, %Y')
            break

    fieldnames = ['Done', 'Date', 'Day_Type', 'Jeremy_Days', 'Lectures_Total_Hrs', 'Lectures', 'PT_Labs', 'Boson_Labs', 'Total_Est_Hrs']
    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write history rows first
        for h_row in history_rows:
            # We must only write the fields that are in fieldnames
            clean_row = {k: h_row.get(k, '') for k in fieldnames}
            writer.writerow(clean_row)
        
        for row in schedule:
            actual_date = row['date']
            
            day_name = actual_date.strftime('%A')
            day_type = f"{day_name} (Holiday)" if actual_date in HOLIDAYS_2026 else day_name
            hours_val = round(row['total_min'] / 60.0, 1)
            
            # Determine if day is completely done (Catch-up days are NOT done)
            all_done = all((jd != 'Catch-up' and int(jd) < 26) for jd in row['j_days_involved'])
            lec_min = sum(l['min'] for l in temp_schedule_items if l['item'] in row['lectures'])
            
            writer.writerow({
                'Done': 'TRUE' if all_done else 'FALSE',
                'Date': actual_date.strftime('%m/%d/%Y'),
                'Day_Type': day_type,
                'Jeremy_Days': ', '.join(sorted(row['j_days_involved'], key=lambda x: 999 if x == 'Catch-up' else int(x))),
                'Lectures_Total_Hrs': round(lec_min / 60.0, 1),
                'Lectures': ' | '.join(row['lectures']),
                'PT_Labs': ' | '.join(row['pt_labs']),
                'Boson_Labs': ' | '.join(row['boson_labs']),
                'Total_Est_Hrs': hours_val
            })
            
    print(f"Schedule generated successfully: {OUTPUT_CSV}")
    
    # Send notification
    send_discord_notification(is_on_track, missed_days, mega_lab_date)

if __name__ == '__main__':
    generate_schedule()
