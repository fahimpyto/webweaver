import os
from jinja2 import Environment, FileSystemLoader


TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


def generate_html(tree, domain, pages_count, max_depth):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('output.html')

    stats = {
        'pages': pages_count,
        'depth': max_depth,
    }

    html = template.render(
        domain=domain,
        tree=tree.to_dict(),
        stats=stats,
    )
    return html
