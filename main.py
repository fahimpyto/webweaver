import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque
import networkx as nx
from pyvis.network import Network

def is_valid_url(url, base_domain):
    """Check if a URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    # Must have a scheme (http/https) and netloc (domain)
    if parsed.scheme not in ('http', 'https'):
        return False
    # If it's a relative path, join with base URL will make it valid
    # For absolute URLs, ensure the domain matches
    if base_domain not in parsed.netloc:
        return False
    # Filter out common non-page file types
    if parsed.path.endswith(('.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.xml', '.rss')):
        return False
    return True

def crawl_and_visualize(start_url, max_pages=50):
    """
    Crawls a website starting from start_url and visualizes the link structure.
    """
    print(f"Starting WebWeaver crawler at: {start_url}")
    print(f"Max pages to crawl: {max_pages}")

    # --- 1. Setup ---
    parsed_initial = urlparse(start_url)
    base_domain = parsed_initial.netloc
    # Use a queue (deque) for BFS
    queue = deque([start_url])
    visited = set()
    # Count how many pages we've processed
    pages_crawled = 0
    # Store graph edges
    graph = nx.DiGraph()

    # --- 2. Crawling Loop ---
    while queue and pages_crawled < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue

        print(f"Crawling ({pages_crawled + 1}/{max_pages}): {current_url}")
        visited.add(current_url)

        try:
            # Fetch the page
            headers = {'User-Agent': 'WebWeaver-Crawler/1.0'}
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes (4xx or 5xx)

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links
            links_on_page = []
            for link in soup.find_all('a', href=True):
                # Join relative URLs to absolute ones
                absolute_url = urljoin(current_url, link['href'])
                # Remove fragments (#section) for normalization
                absolute_url = absolute_url.split('#')[0]
                
                if is_valid_url(absolute_url, base_domain):
                    links_on_page.append(absolute_url)
                    # Add edge to graph (from current page to linked page)
                    graph.add_edge(current_url, absolute_url)
                    # Add to queue if not visited
                    if absolute_url not in visited:
                        queue.append(absolute_url)

            pages_crawled += 1
            # Be polite: wait a second before next request
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"  -> Failed to crawl {current_url}: {e}")
        except Exception as e:
            print(f"  -> An unexpected error occurred for {current_url}: {e}")

    print(f"\nCrawling finished. Processed {pages_crawled} pages.")
    print(f"Graph has {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    # --- 3. Visualization with PyVis ---
    print("Generating interactive visualization...")
    
    # Create a PyVis network object
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    # Set a physics layout for a nice, force-directed graph
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2,
        "size": 30,
        "color": {
          "border": "#2B7CE9",
          "background": "#97C2FC"
        },
        "font": {"color": "white"}
      },
      "edges": {
        "color": {"inherit": true},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}}
      },
      "physics": {
        "enabled": true,
        "stabilization": {"iterations": 100}
      }
    }
    """)

    # Add the graph from NetworkX to PyVis
    net.from_nx(graph)

    # Save the graph as an interactive HTML file
    output_file = "webweaver_map.html"
    net.show(output_file, notebook=False)
    print(f"Visualization saved to '{output_file}'. Open this file in your web browser!")

# --- 4. Run the Crawler ---
if __name__ == "__main__":
    # Example: Crawl a test site's homepage and its links
    starting_url = "https://abdulaouwal.com"  # CHANGE THIS TO YOUR TARGET URL
    # You can adjust max_pages to go deeper or keep it shallow for testing
    crawl_and_visualize(starting_url, max_pages=30)