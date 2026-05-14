import os
import asyncio
from urllib.parse import urlparse
from crawler import crawl_website
from tree import build_tree
from renderer import generate_html


def get_domain_name(url):
    return urlparse(url).netloc.replace('www.', '')


BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE, 'output')


if __name__ == '__main__':
    print("=" * 60)
    print("       WebWeaver - Website Hierarchy Crawler")
    print("=" * 60)

    start_url = input("\nEnter URL to crawl: ").strip()
    if not start_url:
        print("No URL provided.")
        exit(1)
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url

    max_input = input("Max pages (Enter for unlimited): ").strip()
    max_pages = int(max_input) if max_input else None

    pages, errors, domain, total_time = asyncio.run(crawl_website(start_url, max_pages))
    tree = build_tree(pages, start_url, errors)
    domain_name = get_domain_name(start_url)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    tree_file = f"{domain_name}.html"
    tree_path = os.path.join(OUTPUT_DIR, tree_file)

    print(f"\nGenerating {tree_file} ...")
    html = generate_html(tree, domain_name, total_time, pages)
    with open(tree_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nDone! Open in your browser:")
    print(f"  file:///{tree_path.replace(os.sep, '/')}")