"""
Phase 2b: Fetch YouTube auto-generated transcripts for all Jeremy's IT Lab videos.

Uses youtube-transcript-api to extract captions without any API key.
Builds a keyword index for topic matching against Boson labs.
"""
import json
import os
import re
import sys
import time
from collections import Counter

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

RAW_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'jeremy_playlist.json')
TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'transcripts')
KEYWORD_INDEX_PATH = os.path.join(TRANSCRIPT_DIR, 'keyword_index.json')

# CCNA-specific keywords/phrases to track in transcripts
CCNA_KEYWORDS = [
    # Routing
    'ospf', 'eigrp', 'rip', 'bgp', 'static route', 'default route', 'routing table',
    'administrative distance', 'metric', 'next hop', 'gateway', 'ip route',
    'router ospf', 'network area', 'router id', 'dr bdr', 'designated router',
    'hello interval', 'dead interval', 'passive interface', 'default information originate',
    'floating static', 'dynamic routing',
    # Switching
    'vlan', 'trunk', 'access port', 'native vlan', 'switchport', 'dot1q',
    'spanning tree', 'stp', 'rstp', 'pvst', 'portfast', 'bpdu guard', 'bpdu filter',
    'root guard', 'loop guard', 'root bridge', 'designated port', 'root port',
    'etherchannel', 'lacp', 'pagp', 'port channel', 'channel group',
    'vtp', 'dtp', 'mac address table', 'cam table',
    'intervlan', 'router on a stick',
    # Layer 3
    'ip address', 'subnet mask', 'subnetting', 'vlsm', 'cidr',
    'ipv6', 'eui-64', 'link local', 'global unicast', 'multicast',
    'arp', 'icmp', 'ping', 'traceroute',
    # Security
    'access list', 'acl', 'standard acl', 'extended acl', 'named acl',
    'permit', 'deny', 'wildcard mask',
    'nat', 'pat', 'static nat', 'dynamic nat', 'overload',
    'port security', 'mac address sticky', 'violation',
    'dhcp snooping', 'dynamic arp inspection', 'dai',
    'aaa', 'radius', 'tacacs', 'authentication',
    'enable secret', 'enable password', 'service password encryption',
    'ssh', 'crypto key', 'transport input',
    # Services
    'dhcp', 'ip helper address', 'dhcp pool', 'dhcp relay',
    'dns', 'domain name', 'name server',
    'ntp', 'ntp server', 'clock',
    'syslog', 'logging',
    'snmp', 'snmp server',
    'ftp', 'tftp',
    'cdp', 'lldp',
    # FHRP
    'hsrp', 'vrrp', 'standby', 'virtual ip', 'preempt',
    # QoS
    'qos', 'quality of service', 'dscp', 'cos', 'policing', 'shaping',
    'voice vlan',
    # Wireless
    'wireless', 'wlan', 'wifi', 'wlc', 'ssid', 'wpa', 'wpa2', 'wpa3',
    'access point', 'lightweight', 'autonomous', 'capwap',
    # WAN
    'wan', 'leased line', 'mpls', 'vpn', 'gre tunnel',
    # Architecture
    'lan architecture', 'spine leaf', 'three tier', 'collapsed core',
    'virtualization', 'cloud', 'container', 'docker', 'vrf',
    # Automation
    'automation', 'ansible', 'puppet', 'chef', 'terraform',
    'json', 'xml', 'yaml', 'rest api', 'api',
    'sdn', 'software defined', 'controller',
    # CLI basics
    'configure terminal', 'privileged exec', 'user exec',
    'show running config', 'show startup config',
    'hostname', 'interface', 'no shutdown', 'shutdown',
    'copy running startup',
]


def sanitize_filename(title):
    """Create a safe filename from a video title."""
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'\s+', '_', safe.strip())
    return safe[:80]


def extract_keywords(text):
    """Count CCNA keyword occurrences in transcript text."""
    text_lower = text.lower()
    counts = {}
    for kw in CCNA_KEYWORDS:
        count = text_lower.count(kw.lower())
        if count > 0:
            counts[kw] = count
    return counts


def main():
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

    with open(RAW_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    videos = [v for v in data['videos'] if v['duration'] != 'N/A']
    print(f"Processing {len(videos)} videos for transcript extraction")

    keyword_index = {}
    success_count = 0
    fail_count = 0
    failed_videos = []

    ytt_api = YouTubeTranscriptApi()

    for i, v in enumerate(videos):
        video_id = v['video_id']
        title = v['title']
        day_match = re.search(r'Day\s+(\d+)', title)
        day_prefix = f"Day_{int(day_match.group(1)):02d}" if day_match else "Extra"
        safe_title = sanitize_filename(title)
        filename = f"{day_prefix}_{safe_title}.txt"
        filepath = os.path.join(TRANSCRIPT_DIR, filename)

        # Skip if already downloaded
        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            keywords = extract_keywords(text)
            keyword_index[video_id] = {
                'title': title,
                'day': int(day_match.group(1)) if day_match else None,
                'filename': filename,
                'word_count': len(text.split()),
                'keywords': keywords,
            }
            success_count += 1
            print(f"  [{i+1:3d}/{len(videos)}] CACHED: {title[:60]}")
            continue

        print(f"  [{i+1:3d}/{len(videos)}] Fetching: {title[:60]}...", end='', flush=True)

        try:
            transcript = ytt_api.fetch(video_id)
            # Concatenate all text segments
            full_text = ' '.join(
                snippet.text.replace('\n', ' ')
                for snippet in transcript
            )

            # Save transcript
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_text)

            # Extract keywords
            keywords = extract_keywords(full_text)

            keyword_index[video_id] = {
                'title': title,
                'day': int(day_match.group(1)) if day_match else None,
                'filename': filename,
                'word_count': len(full_text.split()),
                'keywords': keywords,
            }
            success_count += 1
            kw_count = len(keywords)
            print(f" OK ({len(full_text.split())} words, {kw_count} CCNA keywords)")

        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            fail_count += 1
            failed_videos.append((video_id, title, str(e)))
            print(f" FAILED: {type(e).__name__}")

        except Exception as e:
            fail_count += 1
            failed_videos.append((video_id, title, str(e)))
            print(f" ERROR: {e}")

        # Small delay to be respectful
        time.sleep(0.3)

    # Save keyword index
    with open(KEYWORD_INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(keyword_index, f, indent=2, ensure_ascii=False)

    # Results
    print(f"\n{'='*60}")
    print(f"PHASE 2b RESULTS")
    print(f"{'='*60}")
    print(f"Total videos:             {len(videos)}")
    print(f"Transcripts fetched:      {success_count}")
    print(f"Transcripts failed:       {fail_count}")
    print(f"Success rate:             {success_count/len(videos)*100:.1f}%")
    print(f"Keyword index saved to:   {KEYWORD_INDEX_PATH}")

    if failed_videos:
        print(f"\nFailed videos:")
        for vid, title, err in failed_videos:
            print(f"  {vid}: {title[:60]} - {err[:50]}")

    # Top keywords across all videos
    total_keywords = Counter()
    for entry in keyword_index.values():
        for kw, count in entry.get('keywords', {}).items():
            total_keywords[kw] += count

    print(f"\nTop 20 CCNA keywords across all transcripts:")
    for kw, count in total_keywords.most_common(20):
        print(f"  {kw:<30} {count:>5} mentions")


if __name__ == '__main__':
    main()
