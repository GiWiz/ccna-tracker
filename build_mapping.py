"""
build_mapping.py - Hand-Curated Mapping Engine v3
====================================================
Every single one of the 103 Boson labs has been manually reviewed and assigned
to the correct Jeremy IT Lab day based on:
  - Reading every Boson lab title, objective, and CCNA_Topics
  - Reading Jeremy's transcript summaries for all multi-day topics
  - Understanding what specific sub-topic each Jeremy day covers

This is a HUMAN-CURATED mapping, not an algorithm.
"""

import csv
import json
import os
import re
from collections import defaultdict

PLAYLIST_JSON = "jeremy_playlist.json"
BOSON_CSV = "data/cleaned/boson_labs_cleaned.csv"
OUTPUT_CSV = "data/cleaned/topic_mapping.csv"

# ─── HAND-CURATED MAPPING ─────────────────────────────────────────
# Lab_ID -> Jeremy Day
#
# Reasoning documented inline for every assignment.
#
# Jeremy's Curriculum Structure (from transcripts):
#   Day 4:  CLI basics, hostname, enable secret, passwords, console/VTY config
#   Day 7:  IPv4 Addressing Part 1 (IP classes, network/host portions, /prefix)
#   Day 8:  IPv4 Addressing Part 2 (calculating hosts/network/broadcast, configuring IPs)
#   Day 9:  Switch Interfaces (speed, duplex, interface status, errors)
#   Day 11: Routing Fundamentals (connected/local routes, routing table, static routes, default routes)
#   Day 16: VLANs Part 1 (what is a VLAN, access ports, basic VLAN config)
#   Day 17: VLANs Part 2 (trunk ports, 802.1Q, trunk config, router-on-a-stick intro)
#   Day 18: VLANs Part 3 (native VLAN, L3 switching/multilayer switching, inter-VLAN routing)
#   Day 19: DTP/VTP
#   Day 20: STP Part 1 (redundancy, STP basics, root bridge election, port roles/states)
#   Day 21: STP Part 2 (STP states/timers, STP toolkit: PortFast, BPDU Guard/Filter, Root Guard, Loop Guard, PVST config)
#   Day 22: Rapid STP (RSTP, rapid PVST+, port roles, link types)
#   Day 23: EtherChannel (L2/L3 EtherChannel, LACP, PAgP, load balancing)
#   Day 25: RIP & EIGRP
#   Day 26: OSPF Part 1 (OSPF basics, areas, basic config with network command, loopback interfaces)
#   Day 27: OSPF Part 2 (OSPF cost/metric, neighbor adjacency process, ip ospf interface config, passive-interface)
#   Day 28: OSPF Part 3 (network types: broadcast/point-to-point, DR/BDR election, neighbor requirements, LSA types, serial interfaces)
#   Day 29: FHRP (HSRP, VRRP, GLBP - overview and basic HSRP config)
#   Day 31: IPv6 Part 1 (hex review, why IPv6, address format, shortening, global unicast basics, dual-stack, basic config)
#   Day 32: IPv6 Part 2 (EUI-64, address types: global unicast, unique local, link-local, multicast, anycast, solicited-node)
#   Day 33: IPv6 Part 3 (IPv6 header, NDP/SLAAC, IPv6 static routing)
#   Day 34: Standard ACLs (ACL intro, ACL logic, standard numbered ACLs, standard named ACLs)
#   Day 35: Extended ACLs (extended numbered ACLs, extended named ACLs, editing ACLs)
#   Day 36: CDP & LLDP
#   Day 37: NTP
#   Day 38: DNS
#   Day 39: DHCP
#   Day 40: SNMP
#   Day 41: Syslog
#   Day 42: SSH
#   Day 43: FTP & TFTP
#   Day 44: NAT Part 1 (private addresses, NAT intro, static NAT config)
#   Day 45: NAT Part 2 (dynamic NAT, PAT/overload config)
#   Day 48: Security Fundamentals (security concepts, common attacks, passwords, MFA, AAA)
#   Day 49: Port Security (switchport port-security, violation modes, sticky, aging)
#   Day 55: Wireless Fundamentals (RF, Wi-Fi standards, WLAN basics)
#   Day 58: Wireless Config (WLC GUI, WLAN setup)
#   Day 59: Network Automation intro
#   Day 60: JSON, XML, YAML
#   Day 61: REST APIs
#   Day 62: SDN (Software-Defined Networking)
#   Day 63: Ansible, Puppet, Chef

MANUAL_MAPPING = {
    # ─── Lab 1: Configuration Demo 1 (EIGRP config) -> Day 25 (RIP & EIGRP) ───
    1: 25,
    # ─── Lab 2: Using NetSim Online (intro/tutorial) -> Day 4 (CLI intro) ───
    2: 4,
    # ─── Lab 3: Explore Cisco Devices (show commands) -> Day 4 (CLI basics) ───
    3: 4,
    # ─── Lab 4: Router Basics (basic router config) -> Day 4 (CLI basics) ───
    4: 4,
    # ─── Lab 5: Switch Basics (basic switch config) -> Day 9 (Switch Interfaces) ───
    5: 9,
    # ─── Lab 6: Configure a Cisco Device (hostname, passwords) -> Day 4 ───
    6: 4,
    # ─── Lab 7: Interpret Interface Errors (CRC, runts) -> Day 9 (Switch Interfaces) ───
    7: 9,
    # ─── Lab 8: Configure Global IPv4 Addressing -> Day 8 (IPv4 Part 2, configuring IPs) ───
    8: 8,
    # ─── Lab 9: Configure RFC 1918 IP Addressing -> Day 7 (IPv4 Part 1, IP classes) ───
    9: 7,
    # ─── Lab 10: Subnet an IPv4 Network -> Day 13 (Subnetting Part 1) ───
    10: 13,
    # ─── Lab 11: Configure VLSM on an IPv4 Network -> Day 15 (Subnetting Part 3 - VLSM) ───
    11: 15,
    # ─── Lab 12: Configure IPv6 Address Types -> Day 31 (IPv6 Part 1) ───
    12: 31,
    # ─── Lab 13: Configure IPv6 by Using Modified EUI-64 -> Day 32 (IPv6 Part 2, EUI-64) ───
    13: 32,
    # ─── Lab 14: Explore the MAC Address Table -> Day 9 (Switch Interfaces) ───
    14: 9,
    # ─── Lab 15: Implement IPv4 Addressing -> Day 8 (IPv4 Part 2) ───
    15: 8,
    # ─── Lab 16: Implement IPv6 Addressing -> Day 31 (IPv6 Part 1) ───
    16: 31,
    # ─── Lab 17: Boson CCNA Challenge Lab 1 (multi-topic: IPv6, routing) -> Day 33 (IPv6 Part 3, static routes) ───
    17: 33,
    # ─── Lab 18: Explore and Configure Switch Access Ports -> Day 16 (VLANs Part 1) ───
    18: 16,
    # ─── Lab 19: Explore and Configure Switch Trunk Ports -> Day 17 (VLANs Part 2, trunking) ───
    19: 17,
    # ─── Lab 20: Configure InterVLAN Routing -> Day 18 (VLANs Part 3, router-on-a-stick) ───
    20: 18,
    # ─── Lab 21: Explore the Native VLAN -> Day 18 (VLANs Part 3, native VLAN) ───
    21: 18,
    # ─── Lab 22: Configure and Verify VTP -> Day 19 (DTP/VTP) ───
    22: 19,
    # ─── Lab 23: Configure and Verify CDP -> Day 36 (CDP & LLDP) ───
    23: 36,
    # ─── Lab 24: Configure and Verify LLDP -> Day 36 ───
    24: 36,
    # ─── Lab 25: Configure Layer 2 EtherChannel LACP -> Day 23 (EtherChannel) ───
    25: 23,
    # ─── Lab 26: Configure Layer 3 EtherChannel LACP and Load Balancing -> Day 23 ───
    26: 23,
    # ─── Lab 27: Explore Spanning Tree Protocol Port Roles -> Day 20 (STP Part 1, port roles) ───
    27: 20,
    # ─── Lab 28: Explore STP Port States and PortFast -> Day 21 (STP Part 2, states/PortFast) ───
    28: 21,
    # ─── Lab 29: Configure a Wireless LAN by Using the WLC GUI -> Day 58 (Wireless Config) ───
    29: 58,
    # ─── Lab 30: Implement InterVLAN Routing -> Day 18 (VLANs Part 3) ───
    30: 18,
    # ─── Lab 31: Implement CDP and LLDP -> Day 36 ───
    31: 36,
    # ─── Lab 32: Implement PVST+ -> Day 21 (STP Part 2, PVST config) ───
    32: 21,
    # ─── Lab 33: Boson CCNA Challenge Lab 2 (multi-topic: CDP, EtherChannel, STP, VLANs, VTP) -> Day 23 (EtherChannel day, covers preceding topics) ───
    33: 23,
    # ─── Lab 34: Explore the Routing Table -> Day 11 (Routing Fundamentals) ───
    34: 11,
    # ─── Lab 35: Route Selection by Using Administrative Distance -> Day 11 ───
    35: 11,
    # ─── Lab 36: Route Selection by Using Routing Protocol Metric -> Day 11 ───
    36: 11,
    # ─── Lab 37: Manually Configure Default Routes on IPv4 Networks -> Day 11 ───
    37: 11,
    # ─── Lab 38: Manually Configure Default Routes on IPv6 Networks -> Day 33 (IPv6 static routing) ───
    38: 33,
    # ─── Lab 39: Manually Configure Network Routes on IPv4 Networks -> Day 11 ───
    39: 11,
    # ─── Lab 40: Manually Configure Network Routes on IPv6 Networks -> Day 33 ───
    40: 33,
    # ─── Lab 41: Manually Configure Host Routes on IPv4 Networks -> Day 11 ───
    41: 11,
    # ─── Lab 42: Manually Configure Host Routes on IPv6 Networks -> Day 33 ───
    42: 33,
    # ─── Lab 43: Configure OSPFv2 Adjacencies -> Day 27 (OSPF Part 2, adjacency process) ───
    43: 27,
    # ─── Lab 44: Configure Point-to-Point OSPFv2 -> Day 28 (OSPF Part 3, network types) ───
    44: 28,
    # ─── Lab 45: Explore OSPFv2 DR and BDR Router Selection -> Day 28 (OSPF Part 3, DR/BDR) ───
    45: 28,
    # ─── Lab 46: Explore and Configure OSPFv2 Router IDs -> Day 26 (OSPF Part 1, router IDs) ───
    46: 26,
    # ─── Lab 47: Plan and Configure Single-Area OSPF -> Day 26 (OSPF Part 1, basic OSPF) ───
    47: 26,
    # ─── Lab 48: Explore HSRP -> Day 29 (FHRP) ───
    48: 29,
    # ─── Lab 49: Explore VRRP -> Day 29 ───
    49: 29,
    # ─── Lab 50: Implement Route Selection -> Day 11 ───
    50: 11,
    # ─── Lab 51: Implement Static and Default Routes -> Day 11 ───
    51: 11,
    # ─── Lab 52: Implement Single-Area OSPFv2 -> Day 27 (OSPF Part 2) ───
    52: 27,
    # ─── Lab 53: Implement HSRP -> Day 29 ───
    53: 29,
    # ─── Lab 54: Implement VRRP -> Day 29 ───
    54: 29,
    # ─── Lab 55: Troubleshoot an OSPFv2 Configuration -> Day 28 (OSPF Part 3 lab is troubleshooting) ───
    55: 28,
    # ─── Lab 56: Boson CCNA Challenge Lab 3 (multi-topic: OSPF, static routes, ACLs, NAT) -> Day 28 (post-OSPF capstone) ───
    56: 28,
    # ─── Lab 57: Configure Static NAT -> Day 44 (NAT Part 1, static NAT) ───
    57: 44,
    # ─── Lab 58: Configure Dynamic NAT -> Day 45 (NAT Part 2, dynamic NAT) ───
    58: 45,
    # ─── Lab 59: Configure PAT -> Day 45 (NAT Part 2, PAT) ───
    59: 45,
    # ─── Lab 60: Configure an NTP Server -> Day 37 (NTP) ───
    60: 37,
    # ─── Lab 61: Configure an NTP Client -> Day 37 ───
    61: 37,
    # ─── Lab 62: Configure and Test a DNS Server -> Day 38 (DNS) ───
    62: 38,
    # ─── Lab 63: Explore Syslog Output -> Day 41 (Syslog) ───
    63: 41,
    # ─── Lab 64: Explore and Configure Syslog Levels -> Day 41 ───
    64: 41,
    # ─── Lab 65: Configure DHCP for IPv4 Networks -> Day 39 (DHCP) ───
    65: 39,
    # ─── Lab 66: Configure DHCP Relay for IPv4 Networks -> Day 39 ───
    66: 39,
    # ─── Lab 67: Configure SSH -> Day 42 (SSH) ───
    67: 42,
    # ─── Lab 68: Explore and Configure TFTP -> Day 43 (FTP & TFTP) ───
    68: 43,
    # ─── Lab 69: Explore and Configure FTP -> Day 43 ───
    69: 43,
    # ─── Lab 70: Implement NAT -> Day 44 (NAT Part 1) ───
    70: 44,
    # ─── Lab 71: Implement NTP -> Day 37 ───
    71: 37,
    # ─── Lab 72: Implement DNS -> Day 38 ───
    72: 38,
    # ─── Lab 73: Implement DHCP -> Day 39 ───
    73: 39,
    # ─── Lab 74: Implement SSH -> Day 42 ───
    74: 42,
    # ─── Lab 75: Boson CCNA Challenge Lab 4 (DHCP, SSH, DNS, NTP, ACLs, NAT) -> Day 39 (capstone for IP services section) ───
    75: 39,
    # ─── Lab 76: Configure the Enable Password -> Day 4 (CLI basics, passwords) ───
    76: 4,
    # ─── Lab 77: Configure the Enable Secret Password -> Day 4 ───
    77: 4,
    # ─── Lab 78: Configure Local User Accounts -> Day 4 ───
    78: 4,
    # ─── Lab 79: Secure the Console and VTY Ports -> Day 4 ───
    79: 4,
    # ─── Lab 80: Encrypt Passwords on a Cisco Device -> Day 4 ───
    80: 4,
    # ─── Lab 81: Explore Password Complexity -> Day 4 ───
    81: 4,
    # ─── Lab 82: Explore and Configure Standard Numbered ACLs -> Day 34 (Standard ACLs) ───
    82: 34,
    # ─── Lab 83: Explore and Configure Extended Numbered ACLs -> Day 35 (Extended ACLs) ───
    83: 35,
    # ─── Lab 84: Explore and Configured Numbered IP ACLs -> Day 34 (standard + extended overlap, starts with standard) ───
    84: 34,
    # ─── Lab 85: Configure Standard Named ACLs -> Day 34 ───
    85: 34,
    # ─── Lab 86: Configure Extended Named ACLs -> Day 35 ───
    86: 35,
    # ─── Lab 87: Explore and Configure Port Security -> Day 49 (Port Security) ───
    87: 49,
    # ─── Lab 88: Explore AAA -> Day 48 (Security Fundamentals, AAA) ───
    88: 48,
    # ─── Lab 89: Implement Passwords -> Day 4 ───
    89: 4,
    # ─── Lab 90: Implement Local User Accounts -> Day 4 ───
    90: 4,
    # ─── Lab 91: Implement Standard ACLs -> Day 34 ───
    91: 34,
    # ─── Lab 92: Implement Extended ACLs -> Day 35 ───
    92: 35,
    # ─── Lab 93: Implement Port Security -> Day 49 ───
    93: 49,
    # ─── Lab 94: Troubleshoot Port Security -> Day 49 ───
    94: 49,
    # ─── Lab 95: Troubleshoot ACLs (multi-topic including NAT, VLANs) -> Day 35 ───
    95: 35,
    # ─── Lab 96: Troubleshooting ACLs 1: Extended ACLs -> Day 35 ───
    96: 35,

    # ─── Lab 97: Troubleshooting ACLs 2: Standard ACLs ───
    # Standard ACL troubleshooting. Day 34.
    97: 34,

    # ─── Lab 98: Troubleshooting ACLs 3: Named ACLs ───
    # Named ACL troubleshooting. Day 35.
    98: 35,

    # ─── Lab 99: Boson CCNA Challenge Lab 5 ───
    # "Configure security features: passwords, ACLs, OSPF, port security"
    # Multi-topic security lab. Day 48 (Security Fundamentals, capstone for security section).
    99: 48,

    # ─── Lab 100: Compare a Traditional Network to a Controller-Based Network ───
    # SDN concepts. Day 62 (Software-Defined Networking).
    100: 62,

    # ─── Lab 101: Explore HTTP Server Verbs ───
    # HTTP verbs (GET, POST, PUT, DELETE) for REST APIs. Day 61 (REST APIs).
    101: 61,

    # ─── Lab 102: Submit and Explore Ansible, Chef, and Puppet Queries ───
    # Config management tools. Day 63 (Ansible, Puppet, Chef).
    102: 63,

    # ─── Lab 103: Obtain and Interpret JSON Output ───
    # JSON data format. Day 60 (JSON, XML, YAML).
    103: 60,
}


# ─── Helper: Parse Duration ────────────────────────────────────────
def parse_duration(d):
    parts = d.split(':')
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(d)


# ─── Load Data ─────────────────────────────────────────────────────
def load_jeremy_days():
    with open(PLAYLIST_JSON, 'r') as f:
        videos = json.load(f)['videos']

    days = defaultdict(lambda: {"lectures": [], "labs": [], "other": [], "all_titles": [], "day_num": 0})

    for v in videos:
        m = re.search(r'Day (\d+)', v['title'])
        if not m:
            continue
        day_num = int(m.group(1))
        days[day_num]["day_num"] = day_num

        title_lower = v['title'].lower()
        entry = {
            "title": v['title'],
            "video_id": v['video_id'],
            "duration_sec": parse_duration(v['duration']),
            "type": "unknown"
        }

        if 'lab' in title_lower:
            entry["type"] = "lab"
            days[day_num]["labs"].append(entry)
        elif 'flashcard' in title_lower or 'anki' in title_lower:
            entry["type"] = "flashcard"
            days[day_num]["other"].append(entry)
        elif 'toolkit' in title_lower:
            entry["type"] = "toolkit"
            days[day_num]["other"].append(entry)
        else:
            entry["type"] = "lecture"
            days[day_num]["lectures"].append(entry)

        days[day_num]["all_titles"].append(v['title'])

    return dict(days)


def load_boson_labs():
    with open(BOSON_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        labs = list(reader)

    for lab in labs:
        lab['task_count'] = int(lab.get('Task_Count', 0) or 0)
        lab['command_count'] = int(lab.get('Command_Count', 0) or 0)

    return labs


# ─── Generate Output ──────────────────────────────────────────────
def generate_output(days, boson_labs):
    # Build day -> labs mapping from manual curation
    day_to_labs = defaultdict(list)
    for lab in boson_labs:
        lab_id = int(lab['Lab_ID'])
        if lab_id in MANUAL_MAPPING:
            target_day = MANUAL_MAPPING[lab_id]
            day_to_labs[target_day].append(lab)
        else:
            print(f"WARNING: Lab {lab_id} ({lab['Lab_Title']}) has no manual mapping!")

    rows = []
    for day_num in sorted(days.keys()):
        day = days[day_num]

        lecture_titles = [v['title'] for v in day['lectures']]
        lecture_duration = sum(v['duration_sec'] for v in day['lectures'])

        lab_titles = [v['title'] for v in day['labs']]
        lab_duration = sum(v['duration_sec'] for v in day['labs'])

        other_titles = [v['title'] for v in day['other']]
        other_duration = sum(v['duration_sec'] for v in day['other'])

        assigned_boson = day_to_labs.get(day_num, [])
        boson_titles = [lab['Lab_Title'] for lab in assigned_boson]
        boson_ids = [lab['Lab_ID'] for lab in assigned_boson]

        # Estimate Boson lab time: Task_Count × 5 min + Command_Count × 1 min, clamped [10, 45]
        boson_time_min = 0
        for lab in assigned_boson:
            lab_time = lab['task_count'] * 5 + lab['command_count'] * 1
            lab_time = max(lab_time, 10)
            lab_time = min(lab_time, 45)
            boson_time_min += lab_time

        # PT lab attempt time (scaled by Jeremy's lab video complexity)
        pt_attempt_min = 0
        if day['labs']:
            avg_lab_min = lab_duration / 60 / len(day['labs'])
            if avg_lab_min <= 12:
                pt_attempt_min = 15
            elif avg_lab_min <= 20:
                pt_attempt_min = 25
            else:
                pt_attempt_min = 40

        total_min = (lecture_duration / 60) + pt_attempt_min + (lab_duration / 60) + boson_time_min + (other_duration / 60)

        rows.append({
            "Day": day_num,
            "Lecture_Titles": " | ".join(lecture_titles),
            "Lecture_Duration_Min": round(lecture_duration / 60, 1),
            "Lab_Titles": " | ".join(lab_titles),
            "Lab_Duration_Min": round(lab_duration / 60, 1),
            "PT_Attempt_Min": pt_attempt_min,
            "Other_Titles": " | ".join(other_titles),
            "Other_Duration_Min": round(other_duration / 60, 1),
            "Boson_Lab_IDs": "; ".join(boson_ids),
            "Boson_Lab_Titles": " | ".join(boson_titles),
            "Boson_Estimated_Min": boson_time_min,
            "Total_Estimated_Min": round(total_min, 1),
        })

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return rows


# ─── Main ─────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Hand-Curated Mapping Engine v3")
    print("=" * 60)

    print("\n[1/3] Loading data...")
    days = load_jeremy_days()
    boson_labs = load_boson_labs()
    print(f"      {len(days)} Jeremy days, {len(boson_labs)} Boson labs")

    # Verify all 103 labs are mapped
    mapped_ids = set(MANUAL_MAPPING.keys())
    all_ids = set(int(lab['Lab_ID']) for lab in boson_labs)
    unmapped = all_ids - mapped_ids
    if unmapped:
        print(f"      WARNING: {len(unmapped)} unmapped labs: {unmapped}")
    else:
        print(f"      All {len(all_ids)} labs have manual mappings [OK]")

    print("\n[2/3] Generating output...")
    rows = generate_output(days, boson_labs)

    print("\n[3/3] Summary:")
    total_hours = sum(r['Total_Estimated_Min'] for r in rows) / 60
    days_with_boson = sum(1 for r in rows if r['Boson_Lab_IDs'])

    # Show distribution
    from collections import Counter
    day_lab_counts = Counter()
    for lab_id, day_num in MANUAL_MAPPING.items():
        day_lab_counts[day_num] += 1

    print(f"      Total estimated study time: {total_hours:.1f} hours")
    print(f"      Days with Boson labs: {days_with_boson}/{len(rows)}")
    print(f"      Max labs on single day: {max(day_lab_counts.values())}")
    print(f"      Avg labs per assigned day: {sum(day_lab_counts.values())/len(day_lab_counts):.1f}")

    print(f"\n{'=' * 60}")
    print("  ALL MAPPINGS:")
    print(f"{'=' * 60}")
    for day_num in sorted(days.keys()):
        day = days[day_num]
        title = day['all_titles'][0][:65] if day['all_titles'] else "?"
        lab_count = day_lab_counts.get(day_num, 0)
        total_min = next((r['Total_Estimated_Min'] for r in rows if int(r['Day']) == day_num), 0)
        print(f"  Day {day_num:2d} [{lab_count:2d} Boson labs, {total_min:6.1f} min]: {title}")
        if lab_count > 0:
            for lab in boson_labs:
                if int(lab['Lab_ID']) in MANUAL_MAPPING and MANUAL_MAPPING[int(lab['Lab_ID'])] == day_num:
                    print(f"           -> Lab {lab['Lab_ID']:3s}: {lab['Lab_Title']}")

    print(f"\n  Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
