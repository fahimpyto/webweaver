from urllib.parse import urlparse


EMOJI_MAP = {
    'home': '\U0001f3e0', '': '\U0001f3e0',
    'about': '\U0001f464', 'profile': '\U0001f464', 'bio': '\U0001f464',
    'blog': '\U0001f4dd', 'news': '\U0001f4f0', 'articles': '\U0001f4dd', 'posts': '\U0001f4dd',
    'contact': '\U0001f4e7', 'support': '\U0001f4e7', 'help': '\U0001f4e7',
    'product': '\U0001f6d2', 'shop': '\U0001f6d2', 'store': '\U0001f6d2', 'pricing': '\U0001f4b0',
    'service': '\U0001f4bc', 'solution': '\U0001f4bc',
    'faq': '\u2753', 'faqs': '\u2753',
    'login': '\U0001f510', 'signup': '\u270d\ufe0f', 'register': '\u270d\ufe0f', 'auth': '\U0001f510',
    'team': '\U0001f465', 'staff': '\U0001f465',
    'project': '\U0001f6e0\ufe0f', 'portfolio': '\U0001f6e0\ufe0f', 'work': '\U0001f6e0\ufe0f',
    'privacy': '\U0001f512', 'terms': '\U0001f4cb', 'legal': '\U0001f4dc',
    'doc': '\U0001f4da', 'documentation': '\U0001f4da', 'guide': '\U0001f4da', 'tutorial': '\U0001f4da',
    'event': '\U0001f4c5', 'calendar': '\U0001f4c5',
    'gallery': '\U0001f5bc\ufe0f', 'photo': '\U0001f5bc\ufe0f', 'image': '\U0001f5bc\ufe0f',
    'video': '\U0001f3ac',
    'career': '\U0001f4bc', 'job': '\U0001f4bc', 'join': '\U0001f4bc',
    'status': '\U0001f4ca', 'analytic': '\U0001f4ca', 'report': '\U0001f4ca',
    'search': '\U0001f50d',
    'dashboard': '\U0001f4cb', 'panel': '\U0001f4cb',
    'setting': '\u2699\ufe0f', 'config': '\u2699\ufe0f',
}


def get_emoji(path):
    for key, emoji in EMOJI_MAP.items():
        if key in path.lower():
            return emoji
    return '\U0001f4c4'


def title_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    if not path:
        return 'Homepage'
    name = path.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
    return name or 'Homepage'


class PageNode:
    def __init__(self, url, title='', depth=0):
        self.url = url
        self.title = title
        self.depth = depth
        self.emoji = '\U0001f4c4'
        self.children = []
        self.crawled = True

    def add_child(self, node):
        self.children.append(node)

    @property
    def path(self):
        return urlparse(self.url).path or '/'

    @property
    def child_count(self):
        return len(self.children)

    def to_dict(self):
        return {
            'url': self.url,
            'title': self.title or title_from_url(self.url),
            'path': self.path,
            'depth': self.depth,
            'emoji': self.emoji,
            'child_count': self.child_count,
            'crawled': self.crawled,
            'children': [c.to_dict() for c in self.children],
        }


def _find_path_parent(url, all_urls, start_url):
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split('/') if p]

    url_set = frozenset(all_urls)

    for i in range(len(parts) - 1, 0, -1):
        parent_path = '/' + '/'.join(parts[:i])
        for pu in url_set:
            pu_parsed = urlparse(pu)
            if (pu_parsed.path.rstrip('/') or '/') == parent_path:
                return pu

    return start_url


def build_tree(pages, start_url):
    all_urls = {start_url}
    for url, data in pages.items():
        all_urls.add(url)
        for link in data.get('links', []):
            all_urls.add(link)

    sorted_urls = sorted(all_urls, key=lambda u: len(urlparse(u).path.split('/')))

    root = PageNode(
        start_url,
        pages.get(start_url, {}).get('title', 'Homepage'),
        depth=0,
    )
    root.emoji = '\U0001f3e0'
    root.crawled = start_url in pages or True
    all_nodes = {start_url: root}

    for url in sorted_urls:
        if url == start_url:
            continue

        parsed = urlparse(url)
        is_crawled = url in pages

        title = pages[url].get('title', '') if is_crawled else ''
        if not title:
            title = title_from_url(url)

        parent_url = _find_path_parent(url, all_urls, start_url)
        parent = all_nodes.get(parent_url, root)

        node = PageNode(url, title, depth=parent.depth + 1)
        node.emoji = get_emoji(parsed.path)
        node.crawled = is_crawled
        parent.add_child(node)
        all_nodes[url] = node

    return root
