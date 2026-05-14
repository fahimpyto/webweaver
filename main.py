import os
from urllib.parse import urlparse
from crawler import crawl_website
from tree import build_tree
from renderer import generate_html
from graph import generate_graph


def get_domain_name(url):
    return urlparse(url).netloc.replace('www.', '')


BASE = os.path.dirname(os.path.abspath(__file__))


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

    tree_file = f"{domain_name}.html"
    graph_file = f"{domain_name}_graph.html"
    tree_path = os.path.join(BASE, tree_file)
    graph_path = os.path.join(BASE, graph_file)

    print(f"\nGenerating {tree_file} ...")
    html = generate_html(tree, domain_name)
    with open(tree_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generating {graph_file} ...")
    generate_graph(pages, tree, domain_name)

    print(f"\nDone! Open in your browser:")
    print(f"  \u2022 Tree:  file:///{tree_path}")
    print(f"  \u2022 Graph: file:///{graph_path}")
