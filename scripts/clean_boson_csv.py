"""
Phase 1: Clean and structure the Boson CCNA Master Index CSV.

Reads the raw CSV, extracts clean command/description pairs from the
messy Command Summary field, removes data bleed, and outputs a structured CSV.
"""
import csv
import re
import sys
import os

RAW_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'Boson_CCNA_Master_Index.csv')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'boson_labs_cleaned.csv')

# Sentinel phrases that indicate the start of data bleed
# (task instructions, router configs, IP tables, etc. that leaked into Command Summary)
DATA_BLEED_SENTINELS = [
    'The IP addresses',
    'tables below',
    'Copyright',
    'Lab Tasks',
    'Sample Configuration',
    'Task 1:',
    'The topology for this lab',
    'When the lab has finished',
    'To grade a lab',
    'To return to a lab',
    'This task',
    'If the prompt',
    'Signals to the CLI',
    'Triggers the device',
    'Synchronizes your terminal',
    'The prompt will not',
    'To practice using',
    'At the',
    'NetSim',
    'If you want to access',
    'In addition, you can click',
    'You can load the saved',
    'Practice loading',
    'NetSim will load',
    'Building configuration',
    'Current configuration',
    'Version ',
    'service timestamps',
    'no service',
    'ip subnet-zero',
    'ip cef',
    'no ip domain-lookup',
    'interface Serial',
    'interface FastEthernet',
    'interface GigabitEthernet',
    'interface Vlan',
    'no ip address',
    'no ip directed-broadcast',
    'no ip route-cache',
    'ip classless',
    'no ip http',
    'line con',
    'line aux',
    'line vty',
    'no scheduler',
    'Devices that have',
    'devices that have',
]

# Known intro text to strip from the beginning of Command Summary
INTRO_PATTERNS = [
    re.compile(r'^The command summary contains.*?lab\.\s*', re.IGNORECASE | re.DOTALL),
]

# CCNA topic keywords for auto-tagging based on lab title + commands
TOPIC_KEYWORDS = {
    'OSPF': ['ospf', 'router ospf', 'network area'],
    'EIGRP': ['eigrp', 'router eigrp'],
    'RIP': ['rip', 'router rip'],
    'VLANs': ['vlan', 'switchport access vlan', 'switchport trunk'],
    'InterVLAN Routing': ['intervlan', 'router-on-a-stick', 'encapsulation dot1q'],
    'STP': ['spanning-tree', 'spanning tree', 'stp', 'pvst', 'portfast', 'bpdu'],
    'EtherChannel': ['etherchannel', 'channel-group', 'port-channel', 'lacp', 'pagp'],
    'ACLs': ['access-list', 'acl', 'ip access-group', 'permit', 'deny'],
    'NAT': ['nat', 'ip nat', 'overload', 'pat'],
    'DHCP': ['dhcp', 'ip dhcp', 'ip helper-address'],
    'DNS': ['dns', 'ip name-server', 'ip domain-name'],
    'NTP': ['ntp', 'ntp server', 'clock set'],
    'SSH': ['ssh', 'crypto key', 'transport input ssh', 'ip ssh'],
    'Syslog': ['syslog', 'logging'],
    'SNMP': ['snmp', 'snmp-server'],
    'CDP': ['cdp', 'show cdp'],
    'LLDP': ['lldp', 'show lldp'],
    'Port Security': ['port-security', 'switchport port-security'],
    'AAA': ['aaa', 'radius', 'tacacs'],
    'IPv4 Addressing': ['ip address', 'subnet', 'ipconfig'],
    'IPv6 Addressing': ['ipv6', 'ipv6 address'],
    'Interface Configuration': ['interface', 'shutdown', 'no shutdown', 'speed', 'duplex'],
    'Routing Fundamentals': ['ip route', 'show ip route', 'default-gateway', 'routing table'],
    'Static Routes': ['ip route', 'ipv6 route'],
    'Wireless': ['wireless', 'wlan', 'wlc', 'ssid'],
    'HSRP': ['hsrp', 'standby'],
    'VRRP': ['vrrp'],
    'VTP': ['vtp', 'vtp mode', 'vtp domain'],
    'FTP/TFTP': ['ftp', 'tftp', 'copy tftp', 'copy ftp'],
    'Password Security': ['password', 'secret', 'service password-encryption', 'enable secret'],
    'Device Basics': ['hostname', 'enable', 'configure terminal', 'show version', 'show running-config'],
    'Network Automation': ['ansible', 'puppet', 'chef', 'json', 'xml', 'rest api', 'http'],
}


def parse_command_summary(raw_text):
    """
    Parse the raw Command Summary field into clean command/description pairs.

    The raw format is an HTML table scraped into text with alternating lines:
      Command Name
      Description of what the command does

    Returns:
        list of (command, description) tuples
    """
    if not raw_text or not raw_text.strip():
        return []

    # Split into lines and strip whitespace
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]

    # Remove any intro text lines (sentences that describe the command summary itself)
    while lines and (
        lines[0].startswith('The command summary contains') or
        lines[0].startswith('You should review')
    ):
        lines.pop(0)

    # Remove the "Command" / "Description" header pair wherever it appears
    # (could be at position 0 or after intro text was removed)
    if len(lines) >= 2 and lines[0] == 'Command' and lines[1] == 'Description':
        lines = lines[2:]
    elif len(lines) >= 1 and lines[0] == 'Command':
        lines.pop(0)
        if lines and lines[0] == 'Description':
            lines.pop(0)

    # Extract command/description pairs, stopping at data bleed
    pairs = []
    i = 0
    while i < len(lines) - 1:
        potential_cmd = lines[i]
        potential_desc = lines[i + 1]

        # Check if we've hit data bleed
        is_bleed = False
        for sentinel in DATA_BLEED_SENTINELS:
            if potential_cmd.startswith(sentinel) or potential_cmd == sentinel:
                is_bleed = True
                break

        if is_bleed:
            break

        # Validate: commands tend to be shorter technical strings,
        # descriptions tend to be longer explanatory text
        # But some commands are long (e.g., "switchport port-security violation shutdown")
        # and some descriptions are short (e.g., "enables an interface")
        # So we use a loose heuristic: if both look like sentences, it's probably bleed
        cmd_looks_like_sentence = (
            potential_cmd.endswith('.') and
            len(potential_cmd) > 80 and
            ' ' in potential_cmd and
            not any(kw in potential_cmd.lower() for kw in ['ip', 'show', 'no ', 'interface', 'router', 'network'])
        )

        if cmd_looks_like_sentence:
            break

        pairs.append((potential_cmd, potential_desc))
        i += 2

    return pairs


def auto_tag_topics(lab_title, commands, objective):
    """Auto-tag CCNA topics based on lab title, commands, and objective text."""
    search_text = f"{lab_title} {' '.join(commands)} {objective}".lower()
    topics = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in search_text:
                topics.append(topic)
                break

    return sorted(set(topics))


def clean_objective(raw_objective):
    """Clean the objective text: remove lab topology description, trim to core objective."""
    if not raw_objective:
        return ''

    # Split at "Lab Topology" marker if present
    parts = raw_objective.split('Lab Topology')
    objective = parts[0].strip()

    # Remove trailing pipe separators
    objective = objective.rstrip(' |')

    # Trim excessively long objectives to first 2 sentences
    sentences = re.split(r'(?<=[.!?])\s+', objective)
    if len(sentences) > 3:
        objective = ' '.join(sentences[:3])

    return objective


def main():
    # Read raw CSV
    with open(RAW_CSV, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Read {len(raw_rows)} labs from raw CSV")

    # Process each lab
    cleaned_rows = []
    total_commands_extracted = 0
    data_bleed_rows = 0

    for i, row in enumerate(raw_rows):
        lab_id = i + 1
        lab_title = row['Lab Title'].strip()
        raw_objective = row.get('Objective', '').strip()
        raw_cmd_summary = row.get('Command Summary', '').strip()
        raw_task_headers = row.get('Task Headers', '').strip()

        # Parse command pairs
        pairs = parse_command_summary(raw_cmd_summary)

        # Track data bleed
        raw_length = len(raw_cmd_summary)
        if raw_length > 3000:
            data_bleed_rows += 1

        # Build clean fields
        commands_list = [cmd for cmd, _ in pairs]
        command_details = '\n'.join(f'• {cmd} — {desc}' for cmd, desc in pairs)
        commands_flat = '; '.join(commands_list)

        # Clean objective
        objective = clean_objective(raw_objective)

        # Parse task headers
        tasks = [t.strip() for t in raw_task_headers.split('|') if t.strip()]
        task_count = len(tasks)

        # Auto-tag topics
        topics = auto_tag_topics(lab_title, commands_list, objective)

        cleaned_rows.append({
            'Lab_ID': lab_id,
            'Lab_Title': lab_title,
            'Objective': objective,
            'Commands': commands_flat,
            'Command_Details': command_details,
            'Task_Headers': raw_task_headers,
            'Task_Count': task_count,
            'Command_Count': len(pairs),
            'CCNA_Topics': ', '.join(topics),
        })

        total_commands_extracted += len(pairs)

    # Write cleaned CSV
    fieldnames = ['Lab_ID', 'Lab_Title', 'Objective', 'Commands', 'Command_Details',
                  'Task_Headers', 'Task_Count', 'Command_Count', 'CCNA_Topics']

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    # Validation
    print(f"\n{'='*60}")
    print(f"PHASE 1 RESULTS")
    print(f"{'='*60}")
    print(f"Labs processed:           {len(cleaned_rows)}")
    print(f"Total commands extracted:  {total_commands_extracted}")
    print(f"Avg commands per lab:      {total_commands_extracted / len(cleaned_rows):.1f}")
    print(f"Data bleed rows cleaned:   {data_bleed_rows}")
    print(f"Output:                    {OUTPUT_CSV}")

    # Check for potential issues
    issues = []
    for row in cleaned_rows:
        if row['Command_Count'] == 0:
            issues.append(f"  Lab {row['Lab_ID']}: {row['Lab_Title']} — NO COMMANDS EXTRACTED")
        if len(row['Command_Details']) > 2000:
            issues.append(f"  Lab {row['Lab_ID']}: {row['Lab_Title']} — Command_Details still long ({len(row['Command_Details'])} chars)")
        if not row['CCNA_Topics']:
            issues.append(f"  Lab {row['Lab_ID']}: {row['Lab_Title']} — NO TOPICS TAGGED")

    if issues:
        print(f"\n[WARNING] ISSUES ({len(issues)}):")
        for issue in issues:
            print(issue)
    else:
        print(f"\n[OK] No issues found")

    # Sample output
    print(f"\n{'='*60}")
    print(f"SAMPLE OUTPUT (first 5 labs)")
    print(f"{'='*60}")
    for row in cleaned_rows[:5]:
        print(f"\nLab {row['Lab_ID']}: {row['Lab_Title']}")
        print(f"  Topics: {row['CCNA_Topics']}")
        print(f"  Commands ({row['Command_Count']}): {row['Commands'][:100]}...")
        print(f"  Tasks ({row['Task_Count']}): {row['Task_Headers'][:80]}...")


if __name__ == '__main__':
    main()
