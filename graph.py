import networkx as nx
from pyvis.network import Network
from urllib.parse import urlparse
import os


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def generate_graph(pages, tree_root, domain):
    G = nx.DiGraph()

    all_nodes = list(_walk(tree_root))
    url_set = {n.url for n in all_nodes}

    for n in all_nodes:
        G.add_node(n.url)

    for url, data in pages.items():
        for link in data.get('links', []):
            if link in url_set:
                G.add_edge(url, link)

    def _connect_tree(node):
        for child in node.children:
            if not G.has_edge(node.url, child.url):
                G.add_edge(node.url, child.url)
            _connect_tree(child)
    _connect_tree(tree_root)

    net = Network(height="800px", width="100%", bgcolor="#0f172a", font_color="#f8fafc")

    for n in all_nodes:
        is_crawled = n.crawled
        color = (
            {'border': '#059669', 'background': '#34d399'}
            if is_crawled
            else {'border': '#d97706', 'background': '#fbbf24'}
        )
        deg = G.degree(n.url)
        size = min(max(deg * 5, 16), 50)
        parsed = urlparse(n.url)
        path = parsed.path.rstrip('/')
        label = (
            path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()[:18]
            if path
            else 'Home'
        )
        title = f"<b>{n.title}</b><br><small>{n.url}</small>"
        if not n.crawled:
            title += "<br><span style='color:#f59e0b'>\u2716 not crawled</span>"
        net.add_node(
            n.url,
            label=label,
            title=title,
            color=color,
            size=size,
            font={'size': 11, 'face': 'sans-serif'},
            borderWidth=2,
        )

    for u, v in G.edges():
        net.add_edge(
            u, v,
            color='rgba(148,163,184,0.35)',
            width=1,
            arrows={'to': {'enabled': True, 'scaleFactor': 0.4}},
        )

    net.set_options("""
var options = {
  "nodes": { "shape": "dot" },
  "edges": { "smooth": { "type": "continuous" } },
  "physics": {
    "enabled": true,
    "stabilization": { "iterations": 200 },
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -60,
      "springConstant": 0.03,
      "springLength": 130
    }
  },
  "interaction": {
    "hover": true,
    "tooltipDelay": 100,
    "navigationButtons": true,
    "keyboard": true
  }
}
    """)

    output_file = f"{domain}_graph.html"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    net.show(output_path, notebook=False)
    return output_path
