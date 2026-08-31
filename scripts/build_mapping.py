"""
Phase 3: Build the cross-reference mapping between Jeremy's IT Lab videos
and Boson NetSim labs using a 3-layer matching strategy.

Layer 1: Title/topic keyword matching
Layer 2: Command overlap analysis
Layer 3: Transcript keyword density matching
"""
import csv
import json
import os
import re
from collections import Counter

BOSON_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'boson_labs_cleaned.csv')
JEREMY_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'jeremy_curriculum.csv')
KEYWORD_INDEX = os.path.join(os.path.dirname(__file__), '..', 'data', 'transcripts', 'keyword_index.json')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'topic_mapping.csv')

# Topic synonyms: maps Jeremy video topics to Boson lab topic keywords
# This handles cases where the same concept uses different terminology
TOPIC_SYNONYMS = {
    'vlan': ['vlan', 'access port', 'trunk port', 'native vlan', 'intervlan', 'switchport'],
    'ospf': ['ospf', 'ospfv2', 'single-area ospf', 'dr and bdr', 'router id'],
    'eigrp': ['eigrp'],
    'rip': ['rip'],
    'stp': ['spanning tree', 'stp', 'pvst', 'rstp', 'rapid spanning', 'portfast', 'bpdu'],
    'etherchannel': ['etherchannel', 'lacp', 'pagp', 'port-channel', 'layer 2 etherchannel', 'layer 3 etherchannel'],
    'acl': ['acl', 'access control', 'standard acl', 'extended acl', 'standard named', 'extended named', 'numbered'],
    'nat': ['nat', 'static nat', 'dynamic nat', 'pat', 'overload'],
    'dhcp': ['dhcp', 'ip helper', 'dhcp relay', 'dhcp snooping'],
    'dns': ['dns', 'domain name', 'name server'],
    'ntp': ['ntp', 'clock'],
    'ssh': ['ssh', 'crypto key'],
    'syslog': ['syslog', 'logging'],
    'snmp': ['snmp'],
    'cdp': ['cdp'],
    'lldp': ['lldp'],
    'ftp': ['ftp', 'tftp'],
    'port security': ['port security', 'port-security', 'mac address sticky', 'violation'],
    'hsrp': ['hsrp', 'standby', 'first hop redundancy'],
    'vrrp': ['vrrp'],
    'ipv4': ['ipv4', 'ip address', 'subnet', 'vlsm', 'rfc 1918'],
    'ipv6': ['ipv6', 'eui-64', 'ipv6 address'],
    'routing': ['routing', 'route', 'static route', 'default route', 'routing table', 'administrative distance'],
    'switch': ['switch', 'interface', 'mac address table'],
    'password': ['password', 'enable secret', 'encryption', 'local user'],
    'aaa': ['aaa', 'authentication', 'radius', 'tacacs'],
    'wireless': ['wireless', 'wlan', 'wlc', 'ssid'],
    'vtp': ['vtp', 'vlan trunking protocol'],
    'dtp': ['dtp', 'dynamic trunking'],
    'qos': ['qos', 'quality of service', 'voice vlan'],
    'wan': ['wan', 'gre tunnel', 'wan architecture'],
    'automation': ['ansible', 'puppet', 'chef', 'terraform', 'automation'],
    'api': ['rest api', 'http', 'json', 'xml', 'yaml', 'api'],
    'sdn': ['sdn', 'software-defined', 'controller'],
    'subnetting': ['subnet', 'vlsm', 'cidr'],
    'arp': ['arp', 'dynamic arp inspection', 'dai'],
}


def load_boson_labs():
    """Load cleaned Boson labs."""
    with open(BOSON_CSV, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_jeremy_curriculum():
    """Load Jeremy curriculum, grouped by Day."""
    with open(JEREMY_CSV, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    # Group lectures by day
    days = {}
    for row in rows:
        if row['Type'] == 'Lecture' and row['Day']:
            day = int(row['Day'])
            if day not in days:
                days[day] = {
                    'day': day,
                    'lectures': [],
                    'topics': set(),
                }
            days[day]['lectures'].append(row)
            for topic in row.get('CCNA_Topics', '').split(', '):
                if topic.strip():
                    days[day]['topics'].add(topic.strip())

    return days


def load_keyword_index():
    """Load transcript keyword index if available."""
    if os.path.exists(KEYWORD_INDEX):
        with open(KEYWORD_INDEX, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def normalize_text(text):
    """Normalize text for comparison."""
    return re.sub(r'[^a-z0-9\s]', '', text.lower().strip())


def layer1_title_match(jeremy_day, boson_lab):
    """Layer 1: Match based on title/topic keyword overlap."""
    jeremy_topics = jeremy_day['topics']
    boson_title = boson_lab['Lab_Title'].lower()
    boson_topics = boson_lab.get('CCNA_Topics', '').lower()
    boson_text = f"{boson_title} {boson_topics}"

    # Check each Jeremy topic against Boson lab
    matches = []
    for topic in jeremy_topics:
        topic_lower = topic.lower()
        # Direct match
        if topic_lower in boson_text:
            matches.append(topic)
            continue
        # Synonym match
        for syn_key, syn_values in TOPIC_SYNONYMS.items():
            if any(sv in topic_lower for sv in syn_values):
                if any(sv in boson_text for sv in syn_values):
                    matches.append(topic)
                    break

    if matches:
        return len(matches) / max(len(jeremy_topics), 1), matches
    return 0.0, []


def layer2_command_match(jeremy_day, boson_lab, keyword_index):
    """Layer 2: Match based on command keyword overlap from transcripts."""
    # Get keywords from Jeremy's lectures for this day
    jeremy_keywords = Counter()
    for lecture in jeremy_day['lectures']:
        video_id = lecture['Video_ID']
        if video_id in keyword_index:
            for kw, count in keyword_index[video_id].get('keywords', {}).items():
                jeremy_keywords[kw] += count

    if not jeremy_keywords:
        return 0.0

    # Get Boson lab commands
    boson_commands = boson_lab.get('Commands', '').lower()
    boson_details = boson_lab.get('Command_Details', '').lower()
    boson_objective = boson_lab.get('Objective', '').lower()
    boson_text = f"{boson_commands} {boson_details} {boson_objective}"

    # Count how many of Jeremy's mentioned keywords appear in Boson lab
    overlap = 0
    total = 0
    for kw, count in jeremy_keywords.items():
        total += 1
        if kw.lower() in boson_text:
            overlap += 1

    return overlap / max(total, 1)


def layer3_topic_synonym_match(jeremy_day, boson_lab):
    """Layer 3: Deep synonym and contextual matching."""
    # Build combined text from Jeremy day
    jeremy_text = ''
    for lecture in jeremy_day['lectures']:
        jeremy_text += f" {lecture['Title']} {lecture.get('CCNA_Topics', '')}"
    jeremy_text = jeremy_text.lower()

    boson_title = boson_lab['Lab_Title'].lower()
    boson_objective = boson_lab.get('Objective', '').lower()
    boson_text = f"{boson_title} {boson_objective}"

    # Score based on synonym group overlap
    score = 0
    max_score = 0
    for syn_key, syn_values in TOPIC_SYNONYMS.items():
        jeremy_has = any(sv in jeremy_text for sv in syn_values)
        boson_has = any(sv in boson_text for sv in syn_values)
        if jeremy_has:
            max_score += 1
            if boson_has:
                score += 1

    return score / max(max_score, 1)


def compute_confidence(l1_score, l2_score, l3_score):
    """Compute overall confidence and label."""
    # Weighted combination
    weighted = (l1_score * 0.5) + (l2_score * 0.3) + (l3_score * 0.2)

    if weighted >= 0.4:
        return 'High', weighted
    elif weighted >= 0.2:
        return 'Medium', weighted
    elif weighted > 0.05:
        return 'Low', weighted
    else:
        return None, weighted


def determine_match_method(l1_score, l2_score, l3_score):
    """Describe which matching layers contributed."""
    methods = []
    if l1_score > 0:
        methods.append('title')
    if l2_score > 0:
        methods.append('commands')
    if l3_score > 0:
        methods.append('transcript')
    return '+'.join(methods) if methods else 'none'


def main():
    boson_labs = load_boson_labs()
    jeremy_days = load_jeremy_curriculum()
    keyword_index = load_keyword_index()

    print(f"Loaded {len(boson_labs)} Boson labs")
    print(f"Loaded {len(jeremy_days)} Jeremy days")
    print(f"Loaded {len(keyword_index)} transcript keyword profiles")

    # Build mappings
    mappings = []

    for day_num in sorted(jeremy_days.keys()):
        jeremy_day = jeremy_days[day_num]
        day_topics = ', '.join(sorted(jeremy_day['topics']))
        day_title = jeremy_day['lectures'][0]['Title'] if jeremy_day['lectures'] else ''

        day_matches = []
        for boson_lab in boson_labs:
            l1_score, l1_topics = layer1_title_match(jeremy_day, boson_lab)
            l2_score = layer2_command_match(jeremy_day, boson_lab, keyword_index)
            l3_score = layer3_topic_synonym_match(jeremy_day, boson_lab)

            confidence, weighted_score = compute_confidence(l1_score, l2_score, l3_score)
            if confidence:
                method = determine_match_method(l1_score, l2_score, l3_score)
                day_matches.append({
                    'Jeremy_Day': day_num,
                    'Jeremy_Topic': day_title,
                    'Jeremy_CCNA_Topics': day_topics,
                    'Boson_Lab_ID': boson_lab['Lab_ID'],
                    'Boson_Lab_Title': boson_lab['Lab_Title'],
                    'Boson_Command_Count': boson_lab['Command_Count'],
                    'Boson_Task_Count': boson_lab['Task_Count'],
                    'Match_Confidence': confidence,
                    'Match_Score': f"{weighted_score:.3f}",
                    'Match_Method': method,
                })

        # Sort by score descending, take top matches
        day_matches.sort(key=lambda x: float(x['Match_Score']), reverse=True)

        if day_matches:
            # Keep High + Medium matches, limit to top 4 per day
            high_medium = [m for m in day_matches if m['Match_Confidence'] in ('High', 'Medium')]
            if high_medium:
                mappings.extend(high_medium[:4])
            else:
                mappings.extend(day_matches[:2])  # Top 2 low-confidence matches
        else:
            # No match found - record it
            mappings.append({
                'Jeremy_Day': day_num,
                'Jeremy_Topic': day_title,
                'Jeremy_CCNA_Topics': day_topics,
                'Boson_Lab_ID': '',
                'Boson_Lab_Title': '(no matching lab)',
                'Boson_Command_Count': '',
                'Boson_Task_Count': '',
                'Match_Confidence': 'None',
                'Match_Score': '0.000',
                'Match_Method': 'none',
            })

    # Write output CSV
    fieldnames = ['Jeremy_Day', 'Jeremy_Topic', 'Jeremy_CCNA_Topics', 'Boson_Lab_ID',
                  'Boson_Lab_Title', 'Boson_Command_Count', 'Boson_Task_Count',
                  'Match_Confidence', 'Match_Score', 'Match_Method']

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)

    # Stats
    high = sum(1 for m in mappings if m['Match_Confidence'] == 'High')
    medium = sum(1 for m in mappings if m['Match_Confidence'] == 'Medium')
    low = sum(1 for m in mappings if m['Match_Confidence'] == 'Low')
    none_count = sum(1 for m in mappings if m['Match_Confidence'] == 'None')
    unique_days_mapped = len(set(m['Jeremy_Day'] for m in mappings if m['Match_Confidence'] != 'None'))
    unique_boson_labs = len(set(m['Boson_Lab_ID'] for m in mappings if m['Boson_Lab_ID']))

    print(f"\n{'='*60}")
    print(f"PHASE 3 RESULTS")
    print(f"{'='*60}")
    print(f"Total mappings:           {len(mappings)}")
    print(f"  High confidence:        {high}")
    print(f"  Medium confidence:      {medium}")
    print(f"  Low confidence:         {low}")
    print(f"  No match:               {none_count}")
    print(f"Jeremy days with match:   {unique_days_mapped}/{len(jeremy_days)}")
    print(f"Boson labs referenced:    {unique_boson_labs}/{len(boson_labs)}")
    print(f"Output:                   {OUTPUT_CSV}")

    # Show unmapped days
    unmapped_days = [m for m in mappings if m['Match_Confidence'] == 'None']
    if unmapped_days:
        print(f"\nUnmapped Jeremy days:")
        for m in unmapped_days:
            print(f"  Day {m['Jeremy_Day']}: {m['Jeremy_Topic']} ({m['Jeremy_CCNA_Topics']})")

    # Show sample mappings
    print(f"\n{'='*60}")
    print(f"SAMPLE MAPPINGS (first 20)")
    print(f"{'='*60}")
    for m in mappings[:20]:
        print(f"  Day {str(m['Jeremy_Day']):>2} {m['Jeremy_Topic'][:30]:<32} -> "
              f"{m['Boson_Lab_Title'][:40]:<42} [{m['Match_Confidence']:>6}] ({m['Match_Method']})")


if __name__ == '__main__':
    main()
