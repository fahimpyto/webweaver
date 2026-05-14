import networkx as nx
from pyvis.network import Network
from urllib.parse import urlparse
import os


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _count(node):
    return 1 + sum(_count(c) for c in node.children)


def generate_graph(pages, tree_root, domain):
    G = nx.DiGraph()

    all_nodes = list(_walk(tree_root))

    for n in all_nodes:
        G.add_node(n.url)

    for url, data in pages.items():
        for link in data.get('links', []):
            if G.has_node(link):
                G.add_edge(url, link)

    def _connect_tree(node):
        for child in node.children:
            if not G.has_edge(node.url, child.url):
                G.add_edge(node.url, child.url)
            _connect_tree(child)
    _connect_tree(tree_root)

    net = Network(height="900px", width="100%", bgcolor="#ffffff", font_color="#1e293b")

    for n in all_nodes:
        is_crawled = n.crawled
        if is_crawled:
            color = {'border': '#059669', 'background': '#d1fae5'}
            text_color = '#065f46'
        else:
            color = {'border': '#d97706', 'background': '#fef3c7'}
            text_color = '#92400e'

        parsed = urlparse(n.url)
        path = parsed.path.rstrip('/')
        label = (path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()[:20]
                 if path else 'Home')

        subtree_size = _count(n)
        size = min(max(subtree_size * 3, 20), 60)

        tooltip = f"<b>{n.title}</b><br><small>{n.url}</small>"
        if not n.crawled:
            reason = n.error if n.error else "not accessible"
            tooltip += f"<br><span style='color:#d97706'>\u2716 {reason}</span>"

        net.add_node(
            n.url,
            label=label,
            title=tooltip,
            color=color,
            size=size,
            font={'size': 11, 'face': 'Inter, -apple-system, sans-serif', 'color': text_color},
            shape='dot',
            borderWidth=2,
        )

    for u, v in G.edges():
        is_link = u in pages and v in pages[u].get('links', [])
        net.add_edge(
            u, v,
            color='#cbd5e1' if is_link else '#e2e8f0',
            width=1.2 if is_link else 0.6,
            arrows={'to': {'enabled': True, 'scaleFactor': 0.3}},
            dashes=not is_link,
        )

    net.set_options("""
var options = {
  "layout": {
    "hierarchical": {
      "enabled": true,
      "direction": "UD",
      "sortMethod": "directed",
      "nodeSpacing": 180,
      "treeSpacing": 220,
      "levelSeparation": 160,
      "blockShifting": true,
      "edgeMinimization": true,
      "parentCentralization": true
    }
  },
  "physics": { "enabled": false },
  "edges": {
    "smooth": { "type": "cubicBezier", "forceDirection": "vertical" }
  },
  "interaction": {
    "dragNodes": true,
    "zoomView": true,
    "hover": true,
    "tooltipDelay": 150,
    "navigationButtons": true
  },
  "configure": { "enabled": false }
}
    """)

    output_file = f"{domain}_graph.html"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    net.show(output_path, notebook=False)
    return output_path
