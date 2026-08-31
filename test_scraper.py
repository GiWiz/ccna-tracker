import requests
import re
import html

vid = '1cuMzWBrEYs'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
try:
    r = requests.get(f'https://youtubetranscript.com/?server_vid2={vid}', headers=headers)
    print('Status:', r.status_code)
    if '<transcript>' in r.text:
        snippets = re.findall(r'<text[^>]*>(.*?)</text>', r.text)
        print(f'Got {len(snippets)} snippets!')
        print(html.unescape(snippets[0]))
    else:
        print('No transcript XML found. Text snippet:', r.text[:100])
except Exception as e:
    print('Error:', e)
