import os
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


def _tree_stats(node):
    total = 1
    ok_count = 1 if node.crawled else 0
    err_count = 0 if node.crawled else 1
    max_depth = node.depth
    for child in node.children:
        t, o, e, d = _tree_stats(child)
        total += t
        ok_count += o
        err_count += e
        max_depth = max(max_depth, d)
    return total, ok_count, err_count, max_depth


def generate_html(tree, domain):
    total_pages, ok_count, err_count, max_depth = _tree_stats(tree)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('output.html')

    html = template.render(
        domain=domain,
        tree=tree.to_dict(),
        total_pages=total_pages,
        ok_count=ok_count,
        err_count=err_count,
        max_depth=max_depth,
    )
    return html
