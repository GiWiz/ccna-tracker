"""
Phase 2a: Build the structured Jeremy's IT Lab curriculum CSV
from the extracted playlist JSON.
"""
import json
import csv
import re
import os

RAW_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'jeremy_playlist.json')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned', 'jeremy_curriculum.csv')


def duration_to_seconds(d):
    """Convert duration string (MM:SS or H:MM:SS) to seconds."""
    if d == 'N/A' or not d:
        return 0
    parts = d.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def classify_video(title):
    """Classify video as Lecture, Lab, or Extra."""
    if 'Lab' in title:
        return 'Lab'
    elif 'Extra' in title or 'Anki' in title:
        return 'Extra'
    elif 'Mega Lab' in title or 'Complete Network Configuration' in title:
        return 'Mega Lab'
    else:
        return 'Lecture'


def extract_day(title):
    """Extract the Day number from a video title."""
    match = re.search(r'Day\s+(\d+)', title)
    return int(match.group(1)) if match else None


def extract_topic(title):
    """Extract the core topic from a video title by removing prefix/suffix."""
    topic = re.sub(r'^Free CCNA \| ', '', title)
    # Handle different title formats
    topic = re.sub(r' \| Day \d+.*$', '', topic)
    topic = re.sub(r' \| CCNA.*$', '', topic)
    topic = re.sub(r' // CCNA.*$', '', topic)
    # For non-standard titles
    topic = re.sub(r' \| CCNA 200-301 Day \d+.*$', '', topic)
    topic = re.sub(r' CCNA 200-301 Day \d+.*$', '', topic)
    return topic.strip()


# CCNA topic keywords for auto-tagging
TOPIC_KEYWORDS = {
    'Network Devices': ['router', 'switch', 'firewall', 'network device'],
    'Cables & Interfaces': ['cable', 'interface', 'ethernet', 'fiber', 'utp', 'sfp'],
    'OSI/TCP-IP Model': ['osi', 'tcp/ip', 'tcp ip', 'encapsulation', 'layer'],
    'CLI': ['cli', 'command-line', 'ios', 'privilege'],
    'Ethernet Switching': ['ethernet', 'switching', 'mac address', 'arp'],
    'IPv4': ['ipv4', 'ip address', 'subnet', 'vlsm', 'cidr'],
    'IPv6': ['ipv6'],
    'Subnetting': ['subnet', 'vlsm', 'cidr', 'network address'],
    'VLANs': ['vlan', 'trunk', 'access port'],
    'DTP/VTP': ['dtp', 'vtp'],
    'STP': ['spanning tree', 'stp', 'rstp', 'pvst', 'portfast', 'bpdu'],
    'EtherChannel': ['etherchannel', 'lacp', 'pagp', 'port-channel'],
    'Routing': ['routing', 'route', 'static route', 'default route'],
    'OSPF': ['ospf'],
    'EIGRP': ['eigrp'],
    'RIP': ['rip'],
    'FHRP': ['hsrp', 'vrrp', 'fhrp', 'first hop redundancy'],
    'TCP/UDP': ['tcp', 'udp', 'transport layer'],
    'ACLs': ['acl', 'access control list', 'access-list', 'standard acl', 'extended acl'],
    'NAT': ['nat', 'pat', 'network address translation'],
    'DHCP': ['dhcp', 'dhcp snooping'],
    'DNS': ['dns', 'domain name'],
    'NTP': ['ntp', 'time'],
    'CDP/LLDP': ['cdp', 'lldp'],
    'SNMP': ['snmp'],
    'Syslog': ['syslog', 'logging'],
    'SSH': ['ssh', 'secure shell'],
    'FTP/TFTP': ['ftp', 'tftp', 'file transfer'],
    'QoS': ['qos', 'quality of service', 'voice vlan'],
    'Security': ['security', 'port security', 'password', 'aaa', 'kali'],
    'DAI': ['dynamic arp inspection', 'dai', 'arp inspection'],
    'LAN Architecture': ['lan architecture', 'three-tier', 'spine-leaf'],
    'WAN Architecture': ['wan architecture', 'gre tunnel', 'leased line', 'mpls'],
    'Virtualization': ['virtual', 'cloud', 'container', 'vrf', 'docker'],
    'Wireless': ['wireless', 'wlan', 'wifi', 'wlc', 'ssid', 'wpa'],
    'Network Automation': ['automation', 'ansible', 'puppet', 'chef', 'terraform', 'ai', 'machine learning'],
    'REST APIs': ['rest api', 'http', 'json', 'xml', 'yaml'],
    'SDN': ['sdn', 'software-defined', 'controller'],
}


def auto_tag_topics(title, topic):
    """Auto-tag CCNA topics based on video title."""
    search_text = f"{title} {topic}".lower()
    topics = []
    for tag, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in search_text:
                topics.append(tag)
                break
    return sorted(set(topics))


def main():
    with open(RAW_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = data['videos']
    print(f"Loaded {len(videos)} videos from playlist JSON")

    rows = []
    for v in videos:
        title = v['title']
        duration = v['duration']
        video_id = v['video_id']

        if duration == 'N/A':
            continue  # Skip external playlist links

        day = extract_day(title)
        vid_type = classify_video(title)
        topic = extract_topic(title)
        dur_seconds = duration_to_seconds(duration)
        study_time = int(dur_seconds * 1.25) if vid_type == 'Lecture' else dur_seconds
        topics = auto_tag_topics(title, topic)

        rows.append({
            'Video_ID': video_id,
            'Day': day if day else '',
            'Type': vid_type,
            'Title': topic,
            'Full_Title': title,
            'Duration': duration,
            'Duration_Seconds': dur_seconds,
            'Study_Time_Estimate_Seconds': study_time,
            'CCNA_Topics': ', '.join(topics),
            'YouTube_URL': f'https://www.youtube.com/watch?v={video_id}',
        })

    # Write CSV
    fieldnames = ['Video_ID', 'Day', 'Type', 'Title', 'Full_Title', 'Duration',
                  'Duration_Seconds', 'Study_Time_Estimate_Seconds', 'CCNA_Topics', 'YouTube_URL']

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    lectures = [r for r in rows if r['Type'] == 'Lecture']
    labs = [r for r in rows if r['Type'] == 'Lab']
    extras = [r for r in rows if r['Type'] in ('Extra', 'Mega Lab')]

    lecture_days = sorted(set(r['Day'] for r in lectures if r['Day']))
    lab_days = sorted(set(r['Day'] for r in labs if r['Day']))
    no_lab_days = sorted(set(lecture_days) - set(lab_days))

    total_lecture_time = sum(r['Duration_Seconds'] for r in lectures)
    total_lab_time = sum(r['Duration_Seconds'] for r in labs)
    total_study_time = sum(r['Study_Time_Estimate_Seconds'] for r in rows)

    print(f"\n{'='*60}")
    print(f"PHASE 2a RESULTS")
    print(f"{'='*60}")
    print(f"Videos processed:         {len(rows)}")
    print(f"  Lectures:               {len(lectures)}")
    print(f"  Labs:                   {len(labs)}")
    print(f"  Extras/Mega Lab:        {len(extras)}")
    print(f"Day range:                1-{max(lecture_days)}")
    print(f"Days with no lab:         {no_lab_days}")
    print(f"Total lecture time:       {total_lecture_time // 3600}h {(total_lecture_time % 3600) // 60}m")
    print(f"Total lab time:           {total_lab_time // 3600}h {(total_lab_time % 3600) // 60}m")
    print(f"Total study estimate:     {total_study_time // 3600}h {(total_study_time % 3600) // 60}m")
    print(f"Output:                   {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
