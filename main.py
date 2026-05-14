import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from collections import deque
import re

def is_valid_url(url, base_domain):
    """Check if a URL is valid and belongs to the same domain."""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    if base_domain not in parsed.netloc:
        return False
    if parsed.path.endswith(('.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.xml', '.rss', '.ico')):
        return False
    return True

def get_page_title(soup, url):
    """Extract title from page."""
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text().strip()[:50]
    
    h1_tag = soup.find('h1')
    if h1_tag:
        return h1_tag.get_text().strip()[:50]
    
    parsed = urlparse(url)
    return parsed.path.strip('/') or parsed.netloc

def crawl_website(start_url, max_pages=None):
    """Crawl website and build hierarchical tree structure."""
    print(f"Starting crawl at: {start_url}")
    print("-" * 50)
    
    parsed_initial = urlparse(start_url)
    base_domain = parsed_initial.netloc
    
    queue = deque([start_url])
    visited = set()
    tree = {"url": start_url, "title": "Homepage", "links": []}
    pages_crawled = 0
    
    WARNING_THRESHOLD = 1000
    warned = False
    
    while queue:
        if max_pages and pages_crawled >= max_pages:
            print(f"\nReached max pages limit: {max_pages}")
            break
        
        queue_size = len(queue) + pages_crawled
        
        if not warned and queue_size >= WARNING_THRESHOLD:
            warned = True
            print(f"\n⚠️  Warning: {queue_size} pages found in queue!")
            response = input("Continue crawling? (y/n): ").strip().lower()
            if response != 'y':
                print("Crawling stopped by user.")
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
            
            links_on_page = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(current_url, link['href'])
                absolute_url = absolute_url.split('#')[0]
                
                if is_valid_url(absolute_url, base_domain):
                    links_on_page.append(absolute_url)
                    if absolute_url not in visited:
                        queue.append(absolute_url)
            
            add_to_tree(tree, current_url, title, links_on_page)
            pages_crawled += 1
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"  -> Failed: {e}")
        except Exception as e:
            print(f"  -> Error: {e}")
    
    print(f"\n✓ Crawling complete. Processed {pages_crawled} pages.")
    return tree, base_domain

def add_to_tree(tree, url, title, links):
    """Add a URL and its links to the tree structure."""
    if url == tree["url"]:
        tree["links"] = [{"url": link, "title": "", "links": []} for link in links]
        return
    
    def find_and_add(node, target_url):
        if node["url"] == target_url:
            node["links"] = [{"url": link, "title": "", "links": []} for link in links]
            return True
        
        for child in node.get("links", []):
            if find_and_add(child, target_url):
                return True
        return False
    
    find_and_add(tree, url)

def get_domain_name(url):
    """Extract domain name for filename."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    return domain.replace('.', '_')

def generate_html(tree, domain_name):
    """Generate HTML using new_design.html template style."""
    
    def render_node(node, is_root=False):
        has_children = node.get("links") and len(node["links"]) > 0
        title = node.get("title", "") or get_page_title_from_url(node["url"])
        path = urlparse(node["url"]).path or "/"
        is_section = is_root or path.count('/') <= 2
        
        avatar = get_emoji_for_path(path)
        
        card_class = "root" if is_root else ("section" if is_section else "")
        badge = f'<div class="count-badge">{len(node.get("links", []))}</div>' if has_children else ""
        toggle = f'<button class="toggle-btn" onclick="toggleChildren(this)">+</button>' if has_children else ""
        
        children_html = ""
        if has_children:
            children_class = "children" if is_root else "sub-children"
            children_html = f'<div class="{children_class}">'
            for child in node["links"]:
                children_html += render_node(child)
            children_html += '</div>'
        
        item_class = "collapsed" if has_children else ""
        
        return f'''
        <div class="child-item {item_class}">
            <div class="node-card {card_class}" data-url="{node["url"]}">
                <div class="avatar">{avatar}</div>
                <div class="node-info">
                    <div class="node-title">{title}</div>
                    <div class="node-path">{path}</div>
                </div>
                {toggle}
                {badge}
            </div>
            {children_html}
        </div>'''
    
    def get_page_title_from_url(url):
        path = urlparse(url).path
        if not path or path == '/':
            return "Homepage"
        parts = path.strip('/').split('/')
        return parts[-1].replace('-', ' ').replace('_', ' ').title()[:40]
    
    def get_emoji_for_path(path):
        if '/' in path:
            section = path.split('/')[1] if len(path.split('/')) > 1 else path
        else:
            section = path
        
        emojis = {
            'blog': '📝', 'course': '🎓', 'project': '🛠️', 'about': '👤',
            'contact': '📧', 'product': '🛒', 'service': '💼', 'team': '👥',
            'news': '📰', 'faq': '❓', 'login': '🔐', 'signup': '✍️',
            'account': '👤', 'privacy': '🔒', 'terms': '📋', 'legal': '📜'
        }
        
        for key, emoji in emojis.items():
            if key in path.lower():
                return emoji
        return '📄'
    
    nodes_html = render_node(tree, is_root=True)
    
    def count_nodes(node):
        count = 1
        for child in node.get("links", []):
            count += count_nodes(child)
        return count
    
    def get_max_depth(node, depth=0):
        if not node.get("links"):
            return depth
        return max(get_max_depth(child, depth + 1) for child in node["links"])
    
    total_pages = count_nodes(tree)
    max_depth = get_max_depth(tree)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{domain_name} - Website Hierarchy</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; color: #1a202c; min-height: 100vh; padding: 20px; }}
        .header {{ max-width: 1800px; margin: 0 auto 40px; background: white; padding: 20px 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }}
        .title {{ font-size: 1.5rem; font-weight: 600; color: #2d3748; }}
        .controls {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        .search-input {{ padding: 10px 16px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.9rem; outline: none; width: 250px; transition: all 0.2s; }}
        .search-input:focus {{ border-color: #4299e1; box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1); }}
        button {{ padding: 10px 18px; background: white; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; color: #4a5568; }}
        button:hover {{ background: #f7fafc; border-color: #cbd5e0; }}
        .stats {{ display: flex; gap: 20px; }}
        .stat {{ text-align: center; padding: 8px 16px; background: #edf2f7; border-radius: 8px; }}
        .stat-num {{ font-size: 1.3rem; font-weight: 700; color: #2d3748; }}
        .stat-label {{ font-size: 0.75rem; color: #718096; text-transform: uppercase; }}
        .container {{ max-width: 1800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow-x: auto; }}
        .hierarchy {{ display: flex; flex-direction: column; gap: 40px; min-width: fit-content; }}
        .level {{ display: flex; align-items: flex-start; gap: 30px; position: relative; }}
        .node-card {{ display: inline-flex; align-items: center; gap: 12px; padding: 14px 20px; background: white; border: 1px solid #e2e8f0; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); transition: all 0.3s; cursor: pointer; position: relative; min-width: 240px; }}
        .node-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-color: #cbd5e0; }}
        .node-card.highlight {{ border-color: #f6ad55; background: #fffaf0; box-shadow: 0 4px 12px rgba(246, 173, 85, 0.3); }}
        .node-card.root {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 18px 24px; }}
        .node-card.section {{ background: #edf2f7; border-color: #cbd5e0; }}
        .avatar {{ width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: white; font-weight: 700; flex-shrink: 0; }}
        .node-card.root .avatar {{ background: rgba(255,255,255,0.3); }}
        .node-card.section .avatar {{ background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%); }}
        .node-info {{ flex: 1; }}
        .node-title {{ font-weight: 600; font-size: 0.95rem; color: #2d3748; margin-bottom: 3px; }}
        .node-card.root .node-title {{ color: white; font-size: 1.1rem; }}
        .node-path {{ font-size: 0.75rem; color: #718096; font-family: 'Courier New', monospace; }}
        .node-card.root .node-path {{ color: rgba(255,255,255,0.8); }}
        .count-badge {{ position: absolute; right: -12px; top: 50%; transform: translateY(-50%); background: #2d3748; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }}
        .toggle-btn {{ width: 28px; height: 28px; border-radius: 50%; background: #4299e1; color: white; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: 700; font-size: 1rem; position: absolute; right: -14px; top: 50%; transform: translateY(-50%); box-shadow: 0 2px 6px rgba(0,0,0,0.15); transition: all 0.3s; z-index: 10; }}
        .toggle-btn:hover {{ background: #3182ce; transform: translateY(-50%) scale(1.1); }}
        .children, .sub-children {{ display: flex; flex-direction: column; gap: 20px; padding-left: 80px; position: relative; }}
        .children::before, .sub-children::before {{ content: ''; position: absolute; left: -30px; top: 0; bottom: 0; width: 2px; background: #cbd5e0; }}
        .child-item {{ position: relative; display: flex; align-items: center; gap: 0; }}
        .child-item::before {{ content: ''; position: absolute; left: -30px; top: 50%; width: 30px; height: 2px; background: #cbd5e0; }}
        .collapsed .children, .collapsed .sub-children {{ display: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">Website Hierarchy</h1>
        <div class="controls">
            <input type="text" class="search-input" id="searchInput" placeholder="Search pages...">
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>
        <div class="stats">
            <div class="stat"><div class="stat-num">{total_pages}</div><div class="stat-label">Pages</div></div>
            <div class="stat"><div class="stat-num">{max_depth}</div><div class="stat-label">Depth</div></div>
        </div>
    </div>
    <div class="container">
        <div class="hierarchy">
            <div class="level">
                {nodes_html}
            </div>
        </div>
    </div>
    <script>
        function toggleChildren(btn) {{
            const item = btn.closest('.child-item');
            const children = item.querySelector('.children, .sub-children');
            if (children) {{
                item.classList.toggle('collapsed');
                btn.textContent = item.classList.contains('collapsed') ? '+' : '−';
            }}
        }}
        function expandAll() {{
            document.querySelectorAll('.collapsed').forEach(item => item.classList.remove('collapsed'));
            document.querySelectorAll('.toggle-btn').forEach(btn => btn.textContent = '−');
        }}
        function collapseAll() {{
            document.querySelectorAll('.child-item').forEach(item => {{
                if (item.querySelector('.children, .sub-children')) {{
                    item.classList.add('collapsed');
                    const btn = item.querySelector('.toggle-btn');
                    if (btn) btn.textContent = '+';
                }}
            }});
        }}
        document.getElementById('searchInput').addEventListener('input', (e) => {{
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.node-card').forEach(card => card.classList.remove('highlight'));
            if (term === '') return;
            document.querySelectorAll('.node-card').forEach(card => {{
                const url = card.dataset.url.toLowerCase();
                const title = card.querySelector('.node-title').textContent.toLowerCase();
                if (url.includes(term) || title.includes(term)) {{
                    card.classList.add('highlight');
                    let parent = card.closest('.child-item');
                    while (parent) {{
                        parent.classList.remove('collapsed');
                        const btn = parent.querySelector('.toggle-btn');
                        if (btn) btn.textContent = '−';
                        parent = parent.parentElement?.closest('.child-item');
                    }}
                }}
            }});
        }});
        document.querySelectorAll('.node-card').forEach(card => {{
            card.addEventListener('click', (e) => {{
                if (e.target.classList.contains('toggle-btn')) return;
                const url = card.dataset.url;
                if (url) {{
                    navigator.clipboard.writeText(url).then(() => {{
                        const original = card.style.background;
                        card.style.background = '#d1fae5';
                        setTimeout(() => card.style.background = original, 500);
                    }});
                }}
            }});
        }});
        document.addEventListener('DOMContentLoaded', () => {{
            collapseAll();
        }});
    </script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    print("=" * 60)
    print("       WebWeaver - Website Hierarchy Crawler")
    print("=" * 60)
    print()
    
    start_url = input("Enter the URL to crawl (e.g., https://example.com): ").strip()
    
    if not start_url:
        print("Error: Please enter a valid URL.")
        exit(1)
    
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url
    
    max_pages_input = input("Max pages to crawl (press Enter for unlimited): ").strip()
    max_pages = int(max_pages_input) if max_pages_input else None
    
    print()
    tree, domain = crawl_website(start_url, max_pages)
    
    domain_name = get_domain_name(start_url)
    output_file = f"{domain_name}.html"
    
    print(f"\nGenerating HTML: {output_file}")
    html_content = generate_html(tree, domain_name)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Done! Open '{output_file}' in your browser.")