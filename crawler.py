import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque


EXCLUDED_EXTENSIONS = (
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js',
    '.xml', '.rss', '.ico', '.svg', '.webp', '.zip', '.tar',
    '.gz', '.mp4', '.mp3', '.avi', '.mov', '.woff', '.woff2',
    '.eot', '.ttf', '.otf',
)


def normalize_url(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')
    for suffix in ['/index.html', '/index.php', '/index.htm', '/default.aspx']:
        if path.endswith(suffix):
            path = path[:-len(suffix)]
            break
    return f"{parsed.scheme}://{netloc}{path}"


def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    if base_domain not in parsed.netloc:
        return False
    if parsed.path.lower().endswith(EXCLUDED_EXTENSIONS):
        return False
    return True


def get_page_title(soup, url):
    title_tag = soup.find('title')
    if title_tag and title_tag.get_text().strip():
        return title_tag.get_text().strip()[:60]
    h1_tag = soup.find('h1')
    if h1_tag and h1_tag.get_text().strip():
        return h1_tag.get_text().strip()[:60]
    parsed = urlparse(url)
    name = parsed.path.strip('/').replace('-', ' ').replace('_', ' ').title()
    return name or 'Homepage'


def crawl_website(start_url, max_pages=None):
    print(f"Starting crawl at: {start_url}")
    print("-" * 50)

    base_domain = urlparse(start_url).netloc
    start_normalized = normalize_url(start_url)

    queue = deque([start_normalized])
    visited = set()
    pages = {}
    pages_crawled = 0

    warned = False
    WARNING_THRESHOLD = 1000

    while queue:
        if max_pages and pages_crawled >= max_pages:
            break

        total_discovered = len(queue) + pages_crawled
        if not warned and total_discovered >= WARNING_THRESHOLD:
            warned = True
            print(f"\n[!] Warning: {total_discovered} pages found in queue!")
            resp = input("Continue crawling? (y/n): ").strip().lower()
            if resp != 'y':
                print("Stopping by user.")
                break

        current_url = queue.popleft()
        if current_url in visited:
            continue

        print(f"[{pages_crawled + 1}] Crawling: {current_url}")
        visited.add(current_url)

        try:
            headers = {'User-Agent': 'WebWeaver-Crawler/1.0'}
            response = requests.get(current_url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title = get_page_title(soup, current_url)

            links = set()
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(current_url, link['href'])
                absolute_url = absolute_url.split('#')[0]
                if is_valid_url(absolute_url, base_domain):
                    links.add(normalize_url(absolute_url))

            pages[current_url] = {'title': title, 'links': list(links)}

            for normalized_link in links:
                if normalized_link not in visited:
                    queue.append(normalized_link)

            pages_crawled += 1
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"  -> Failed: {e}")
        except Exception as e:
            print(f"  -> Error: {e}")

    print(f"\nDone. Processed {pages_crawled} pages.")
    return pages, base_domain
