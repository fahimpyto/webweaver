import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from collections import deque
import time


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
    if soup:
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()[:60]
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            return h1_tag.get_text().strip()[:60]
    parsed = urlparse(url)
    name = parsed.path.strip('/').replace('-', ' ').replace('_', ' ').title()
    return name or 'Homepage'


def get_seo_data(soup):
    seo = {
        'title': '',
        'meta_desc': '',
        'h1_count': 0,
        'h2_count': 0,
        'internal_links': 0,
        'external_links': 0,
        'images': 0,
    }
    if not soup:
        return seo
    
    title_tag = soup.find('title')
    if title_tag:
        seo['title'] = title_tag.get_text().strip()[:100]
    
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        seo['meta_desc'] = meta_desc.get('content', '')[:200]
    
    seo['h1_count'] = len(soup.find_all('h1'))
    seo['h2_count'] = len(soup.find_all('h2'))
    
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        if href.startswith('http'):
            seo['external_links'] += 1
        else:
            seo['internal_links'] += 1
    
    seo['images'] = len(soup.find_all('img'))
    
    return seo


async def crawl_website(start_url, max_pages=None):
    print(f"Starting crawl at: {start_url}")
    print("-" * 50)
    
    start_time = time.time()
    base_domain = urlparse(start_url).netloc
    start_normalized = normalize_url(start_url)
    
    queue = deque([start_normalized])
    visited = set()
    pages = {}
    errors = {}
    pages_crawled = 0
    
    BATCH_SIZE = 10
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        while queue:
            if max_pages and pages_crawled >= max_pages:
                break
            
            batch = []
            while len(batch) < BATCH_SIZE and queue:
                url = queue.popleft()
                if url not in visited:
                    batch.append(url)
            
            if not batch:
                break
            
            tasks = []
            for url in batch:
                tasks.append(crawl_page(url, browser, base_domain, visited))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(batch, results):
                visited.add(url)
                
                if isinstance(result, Exception):
                    errors[url] = str(result)[:50]
                    print(f"  -> [ERROR] {url}: {result}")
                    pages[url] = {
                        'title': get_page_title(None, url),
                        'links': [],
                        'seo': get_seo_data(None),
                        'load_time': 0,
                        'page_size': 0,
                        'status': 0,
                    }
                else:
                    status, html, load_time, page_size = result
                    
                    if status == 200 and html:
                        soup = html
                        title = get_page_title(soup, url)
                        links = set()
                        
                        for link in soup.find_all('a', href=True):
                            absolute_url = urljoin(url, link['href'])
                            absolute_url = absolute_url.split('#')[0]
                            if is_valid_url(absolute_url, base_domain):
                                normalized = normalize_url(absolute_url)
                                links.add(normalized)
                                if normalized not in visited:
                                    queue.append(normalized)
                        
                        seo = get_seo_data(soup)
                        
                        pages[url] = {
                            'title': title,
                            'links': list(links),
                            'seo': seo,
                            'load_time': round(load_time, 2),
                            'page_size': round(page_size / 1024, 1),
                            'status': status,
                        }
                        
                        print(f"[{pages_crawled + 1}] {url} - {status} - {round(load_time, 0)}ms - {round(page_size/1024, 1)}KB")
                    else:
                        errors[url] = f"HTTP {status}" if status else "failed"
                        pages[url] = {
                            'title': get_page_title(None, url),
                            'links': [],
                            'seo': get_seo_data(None),
                            'load_time': round(load_time, 2),
                            'page_size': round(page_size / 1024, 1),
                            'status': status,
                        }
                        print(f"  -> [{status}] {url}")
                    
                    pages_crawled += 1
            
            elapsed = time.time() - start_time
            print(f"  -> Batch done. Queue: {len(queue)}, Elapsed: {elapsed:.1f}s\n")
    
    total_time = time.time() - start_time
    print(f"\nDone. Successfully crawled {pages_crawled} page(s) in {total_time:.1f}s.")
    return pages, errors, base_domain, total_time


async def crawl_page(url, browser, base_domain, visited):
    page_time = time.time()
    try:
        page = await browser.new_page()
        response = await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        status = response.status if response else 0
        
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        content = await page.content()
        load_time = (time.time() - page_time) * 1000
        page_size = len(content.encode('utf-8'))
        
        await page.close()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        return status, soup, load_time, page_size
    except Exception as e:
        load_time = (time.time() - page_time) * 1000
        return 0, None, load_time, 0