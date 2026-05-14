import os
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


def _count_nodes(node):
    crawled = 1 if node.crawled else 0
    discovered = 1
    for child in node.children:
        c, d = _count_nodes(child)
        crawled += c
        discovered += d
    return crawled, discovered

def _max_tree_depth(node, depth=0):
    if not node.children:
        return depth
    return max(_max_tree_depth(child, depth + 1) for child in node.children)


def generate_html(tree, domain):
    crawled, discovered = _count_nodes(tree)
    depth = _max_tree_depth(tree)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('output.html')

    stats = {
        'crawled': crawled,
        'discovered': discovered,
        'depth': depth,
    }

    html = template.render(
        domain=domain,
        tree=tree.to_dict(),
        stats=stats,
    )
    return html
