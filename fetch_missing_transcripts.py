import os
import json
import time

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    print("Please install youtube-transcript-api first by running:")
    print("pip install youtube-transcript-api")
    exit(1)

import zipfile
import re

def sanitize_filename(title):
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'\s+', '_', safe.strip())
    return safe[:80]

missing_data = [
    {'id': 'ffnJ5oBIObY', 'title': 'Free CCNA | Configuring EIGRP | Day 25 Lab | CCNA 200-301 Complete Course'},
    {'id': 'pvuaoJ9YzoI', 'title': 'Free CCNA | OSPF Part 1 | Day 26 | CCNA 200-301 Complete Course'},
    {'id': 'LeLRWjfylcs', 'title': 'Free CCNA | Configuring OSPF (1) | Day 26 Lab | CCNA 200-301 Complete Course'},
    {'id': 'VtzfTA21ht0', 'title': 'Free CCNA | OSPF Part 2 | Day 27 | CCNA 200-301 Complete Course'},
    {'id': 'UEyQW-EcnY8', 'title': 'Free CCNA | Configuring OSPF (2) | Day 27 Lab | CCNA 200-301 Complete Course'},
    {'id': '3ew26ujkiDI', 'title': 'Free CCNA | OSPF Part 3 | Day 28 | CCNA 200-301 Complete Course'},
    {'id': 'Goekjm3bK5o', 'title': 'Free CCNA | Configuring OSPF (3) | Day 28 Lab | CCNA 200-301 Complete Course'},
    {'id': '43WnpwQMolo', 'title': 'Free CCNA | First Hop Redundancy Protocols | Day 29 | CCNA 200-301 Complete Course'},
    {'id': 'uho5Z2nFhb8', 'title': 'Free CCNA | Configuring HSRP | Day 29 Lab | CCNA 200-301 Complete Course'},
    {'id': 'LIEACBqlntY', 'title': 'Free CCNA | TCP & UDP | Day 30 | CCNA 200-301 Complete Course'},
    {'id': 'pJKFahkqMU8', 'title': 'Free CCNA | Wireshark Demo (TCP/UDP) | Day 30 Lab | CCNA 200-301 Complete Course'},
    {'id': 'ZNuXyOXae5U', 'title': 'Free CCNA | IPv6 Part 1 | Day 31 | CCNA 200-301 Complete Course'},
    {'id': 'BdsIahtrWIA', 'title': 'Free CCNA | Configuring IPv6 (Part 1) | Day 31 Lab | CCNA 200-301 Complete Course'},
    {'id': 'BrTMMOXFhDU', 'title': 'Free CCNA | IPv6 Part 2 | Day 32 | CCNA 200-301 Complete Course'},
    {'id': 'Zfhpd7dl6QI', 'title': 'Free CCNA | Configuring IPv6 (Part 2) | Day 32 Lab | CCNA 200-301 Complete Course'},
    {'id': 'rwkHfsWQwy8', 'title': 'Free CCNA | IPv6 Part 3 | Day 33 | CCNA 200-301 Complete Course'},
    {'id': 'WSBEVFANMmc', 'title': 'Free CCNA | Configuring IPv6 (Part 3) | Day 33 Lab | CCNA 200-301 Complete Course'},
    {'id': 'z023_eRUtSo', 'title': 'Free CCNA | Standard ACLs | Day 34 | CCNA 200-301 Complete Course'},
    {'id': 'sJ8PXmiAkvs', 'title': 'Free CCNA | Standard ACLs | Day 34 Lab | CCNA 200-301 Complete Course'},
    {'id': 'dUttKY_CNXE', 'title': 'Free CCNA | Extended ACLs | Day 35 | CCNA 200-301 Complete Course'},
    {'id': '1cuMzWBrEYs', 'title': 'Free CCNA | Extended ACLs | Day 35 Lab | CCNA 200-301 Complete Course'},
    {'id': '_hnMZBzXRRk', 'title': 'Free CCNA | CDP & LLDP | Day 36 | CCNA 200-301 Complete Course'},
    {'id': '4s8qqL7R9W8', 'title': 'Free CCNA | CDP & LLDP | Day 36 Lab | CCNA 200-301 Complete Course'},
    {'id': 'qGJaJx7OfUo', 'title': 'Free CCNA | NTP | Day 37 | CCNA 200-301 Complete Course'},
    {'id': 'Miys7Ft9wWI', 'title': 'Free CCNA | NTP | Day 37 Lab | CCNA 200-301 Complete Course'},
    {'id': '4C6eeQes4cs', 'title': 'Free CCNA | DNS | Day 38 | CCNA 200-301 Complete Course'},
    {'id': '7D_FapNrRUM', 'title': 'Free CCNA | DNS | Day 38 Lab | CCNA 200-301 Complete Course'},
    {'id': 'hzkleGAC2_Y', 'title': 'Free CCNA | DHCP | Day 39 | CCNA 200-301 Complete Course'},
    {'id': 'cgMsoIQB9Wk', 'title': 'Free CCNA | DHCP | Day 39 Lab | CCNA 200-301 Complete Course'},
    {'id': 'HXu0Ifj0oWU', 'title': 'Free CCNA | SNMP | Day 40 | CCNA 200-301 Complete Course'},
    {'id': 'v8WxIytUdS4', 'title': 'Free CCNA | SNMP | Day 40 Lab | CCNA 200-301 Complete Course'},
    {'id': 'RaQPSKQ4J5A', 'title': 'Free CCNA | Syslog | Day 41 | CCNA 200-301 Complete Course'},
    {'id': '-R_CYM6Wm-Y', 'title': 'Free CCNA | Syslog | Day 41 Lab | CCNA 200-301 Complete Course'},
    {'id': 'AvgYqI2qSD4', 'title': 'Free CCNA | SSH | Day 42 | CCNA 200-301 Complete Course'},
    {'id': 'QnHq7iCOtTc', 'title': 'Free CCNA | SSH | Day 42 Lab | CCNA 200-301 Complete Course'},
    {'id': '50hcfsoBf4Q', 'title': 'Free CCNA | FTP & TFTP | Day 43 | CCNA 200-301 Complete Course'},
    {'id': 'W9PLvA2wZ28', 'title': 'Free CCNA | FTP & TFTP | Day 43 Lab | CCNA 200-301 Complete Course'},
    {'id': '2TZCfTgopeg', 'title': 'Free CCNA | NAT (Part 1) | Day 44 | CCNA 200-301 Complete Course'},
    {'id': 'vir6n_NVZFw', 'title': 'Free CCNA | Static NAT | Day 44 Lab | CCNA 200-301 Complete Course'},
    {'id': 'kILDNs4KjYE', 'title': 'Free CCNA | NAT (part 2) | Day 45 | CCNA 200-301 Complete Course'},
    {'id': 'vNs1xxiwGJs', 'title': 'Free CCNA | Dynamic NAT | Day 45 Lab | CCNA 200-301 Complete Course'},
    {'id': 'H6FKJMiiL6E', 'title': 'Free CCNA | QoS (Part 1) | Day 46 | CCNA 200-301 Complete Course'},
    {'id': 'kGX76QNIjsE', 'title': 'Free CCNA | Voice VLANs | Day 46 Lab | CCNA 200-301 Complete Course'},
    {'id': '4vurfhVjcMM', 'title': 'Free CCNA | QoS (Part 2) | Day 47 | CCNA 200-301 Complete Course'},
    {'id': '63tD4t8189k', 'title': 'Free CCNA | QoS | Day 47 Lab | CCNA 200-301 Complete Course'},
    {'id': 'VvFuieyTTSw', 'title': 'Free CCNA | Security Fundamentals | Day 48 | CCNA 200-301 Complete Course'},
    {'id': 'EBs47-0ZD-A', 'title': 'Free CCNA | Kali Linux Demo | Day 48 Lab | CCNA 200-301 Complete Course'},
    {'id': 'sHN3jOJIido', 'title': 'Free CCNA | Port Security | Day 49 | CCNA 200-301 Complete Course'},
    {'id': 'zZwhrxKeGj8', 'title': 'Free CCNA | Port Security | Day 49 Lab | CCNA 200-301 Complete Course'},
    {'id': 'qYYeg2kz1yE', 'title': 'Free CCNA | DHCP Snooping | Day 50 | CCNA 200-301 Complete Course'},
    {'id': 'YMom_e545H4', 'title': 'Free CCNA | DHCP Snooping | Day 50 Lab | CCNA 200-301 Complete Course'},
    {'id': 'HwbTKaIvL6s', 'title': 'Free CCNA | Dynamic ARP Inspection | Day 51 | CCNA 200-301 Complete Course'},
    {'id': 'oLF2mbmYMAk', 'title': 'Free CCNA | Dynamic ARP Inspection | Day 51 Lab | CCNA 200-301 Complete Course'},
    {'id': 'PvyEcLhmNBk', 'title': 'Free CCNA | LAN Architectures | Day 52 | CCNA 200-301 Complete Course'},
    {'id': 'BgIEhyoETgU', 'title': 'Free CCNA | STP & FHRP Synchronization | Day 52 Lab | CCNA 200-301 Complete Course'},
    {'id': 'BW3fQgdf4-w', 'title': 'Free CCNA | WAN Architectures | Day 53 | CCNA 200-301 Complete Course'},
    {'id': '_MMuU5viinM', 'title': 'Free CCNA | GRE Tunnels | Day 53 Lab | CCNA 200-301 Complete Course'},
    {'id': '_S3greGajJA', 'title': 'Free CCNA | Virtualization & Cloud | Day 54 (part 1) | CCNA 200-301 Complete Course'},
    {'id': 'K731pAS22Aw', 'title': 'Free CCNA | Containers | Day 54 (part 2) | CCNA 200-301 Complete Course'},
    {'id': 'Ge4644KUvh4', 'title': 'Free CCNA | VRF | Day 54 (part 3) | CCNA 200-301 Complete Course'},
    {'id': 'swqADfQk2jM', 'title': 'Free CCNA | Oracle VirtualBox | Day 54 Lab | CCNA 200-301 Complete Course'},
    {'id': 'zuYiktLqNYQ', 'title': 'Free CCNA | Wireless Fundamentals | Day 55 | CCNA 200-301 Complete Course'},
    {'id': 'uX1h0F6wpBY', 'title': 'Free CCNA | Wireless Architectures | Day 56 | CCNA 200-301 Complete Course'},
    {'id': 'wHXKo9So5y8', 'title': 'Free CCNA | Wireless Security | Day 57 | CCNA 200-301 Complete Course'},
    {'id': 'r9o6GFI87go', 'title': 'Free CCNA | Wireless Configuration | Day 58 | CCNA 200-301 Complete Course'},
    {'id': 'Il8ev78fcqw', 'title': 'Free CCNA | Wireless LANs | Day 58 Lab | CCNA 200-301 Complete Course'},
    {'id': '4tsBgMCPVuc', 'title': 'Intro to Network Automation | CCNA 200-301 Day 59 (part 1)'},
    {'id': 'Fn_kAv35W5A', 'title': 'AI & Machine Learning | CCNA 200-301 Day 59 (part 2)'},
    {'id': 'nohde2-QNJ4', 'title': 'Free CCNA | JSON, XML, & YAML | Day 60 | CCNA 200-301 Complete Course'},
    {'id': 'Luei0p-2h10', 'title': 'Free CCNA | REST APIs | Day 61 | CCNA 200-301 Complete Course'},
    {'id': 'bmqr_xpt6sc', 'title': 'REST API Authentication | CCNA 200-301 Day 61 (part 2)'},
    {'id': '7HhWCeXDTpA', 'title': 'Free CCNA | Software-Defined Networking | Day 62 | CCNA 200-301 Complete Course'},
    {'id': 'Kog9gHTjALI', 'title': 'Free CCNA | Ansible, Puppet, & Chef | Day 63 (part 1) | CCNA 200-301 Complete Course'},
    {'id': 'VAwUaffejWU', 'title': 'Terraform | CCNA 200-301 Day 63 (part 2)'},
    {'id': '2p7-MluKAgE', 'title': 'Complete Network Configuration // CCNA Mega Lab! / OSPF, VLANs, STP, DHCP, Security, Wireless + more'},
]

import http.cookiejar as cookielib
import requests

def main():
    os.makedirs('downloaded_transcripts', exist_ok=True)
    
    print("Loading cookies from cookies.txt...")
    try:
        cookie_jar = cookielib.MozillaCookieJar('cookies.txt')
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        session = requests.Session()
        session.cookies = cookie_jar
        api = YouTubeTranscriptApi(http_client=session)
        print("Cookies loaded successfully!\n")
    except Exception as e:
        print(f"Failed to load cookies.txt: {e}")
        print("Make sure cookies.txt is in the same folder as this script!")
        return

    success = 0
    fail = 0
    
    print(f"Attempting to download {len(missing_data)} missing transcripts...\n")
    
    for i, v in enumerate(missing_data):
        vid = v['id']
        title = v['title']
        day_match = re.search(r'Day\s+(\d+)', title)
        day_prefix = f"Day_{int(day_match.group(1)):02d}" if day_match else "Extra"
        safe_title = sanitize_filename(title)
        filename = f"downloaded_transcripts/{day_prefix}_{safe_title}.txt"
        
        print(f"[{i+1}/{len(missing_data)}] {title[:50]}...", end='', flush=True)
        
        try:
            # We try fetching the default or the manual English one
            transcript_list = api.list(vid)
            try:
                # Prioritize manually created english transcripts
                transcript = transcript_list.find_transcript(['en'])
            except:
                # Fallback to any english generated ones
                transcript = transcript_list.find_generated_transcript(['en'])
                
            data = transcript.fetch()
            full_text = ' '.join(snippet.text.replace('\n', ' ') for snippet in data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_text)
                
            print(f" OK!")
            success += 1
            
        except Exception as e:
            print(f" FAILED: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            fail += 1
            
        time.sleep(0.5)
        
    print(f"\nDone! Downloaded {success}, Failed {fail}.")
    
    if success > 0:
        print("Zipping up the transcripts...")
        with zipfile.ZipFile('missing_transcripts.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk('downloaded_transcripts'):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        print("Created 'missing_transcripts.zip'! You can now upload this file back to the AI.")

if __name__ == '__main__':
    main()
