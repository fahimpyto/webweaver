import os
from urllib.parse import urlparse
from crawler import crawl_website
from tree import build_tree
from renderer import generate_html


def get_domain_name(url):
    return urlparse(url).netloc.replace('www.', '')


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

    pages, domain = crawl_website(start_url, max_pages)
    tree = build_tree(pages, start_url)
    domain_name = get_domain_name(start_url)

    output_file = f"{domain_name}.html"
    print(f"\nGenerating {output_file} ...")
    html = generate_html(tree, domain_name)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Done! Open '{output_path}' in your browser.")
