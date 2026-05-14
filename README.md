# WaveWeaver

WaveWeaver is a website hierarchy crawler that crawls any website and generates an interactive visual sitemap. It helps with SEO site diagnostics by analyzing page structure, load times, and SEO data.

## What It Does

- Crawls websites starting from any URL
- Extracts all internal links and builds a hierarchical tree
- Generates an interactive HTML visualization (CrawlMap)
- Collects SEO data: title, meta description, H1/H2 counts, images, internal/external links
- Measures page load time and page size
- Reports HTTP status codes and errors

## Purpose

WaveWeaver is designed for SEO specialists, web developers, and site owners who need to:
- Visualize website structure and navigation flow
- Identify broken links and error pages
- Analyze SEO elements across pages
- Understand site depth and architecture
- Audit page performance metrics

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd waveweaver
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

Run the crawler:
```bash
python main.py
```

The tool will prompt you for:
1. **URL to crawl** - Enter the website URL (e.g., example.com)
2. **Max pages** - Enter a number to limit pages, or press Enter for unlimited

Example:
```
Enter URL to crawl: https://example.com
Max pages (Enter for unlimited): 50
```

Once complete, an HTML file will be generated in the `output/` folder. Open it in your browser to view the interactive sitemap.

## Output

The generated HTML file includes:
- Interactive tree visualization with pan and zoom
- Click nodes to expand/collapse children
- Click nodes to view detailed SEO information
- Statistics: total pages, successful/failed crawls, average load time

## Requirements

- Python 3.8+
- Playwright
- BeautifulSoup4
- lxml
- Jinja2

## License

MIT