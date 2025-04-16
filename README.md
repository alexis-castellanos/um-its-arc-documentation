# University of Michigan ARC Documentation Scraper

This project contains tools to scrape, process, and organize the University of Michigan Advanced Research Computing (ARC) documentation for offline use and analysis.

## Overview

The project consists of two main Python scripts:

1. **umich-arc-scraper.py**: Crawls the UMich ARC documentation website and saves all pages to JSON files.
2. **umich-arc-processor.py**: Processes the scraped data into a structured format, generates HTML versions, and extracts a knowledge base.

## Requirements

- Python 3.8+
- Required packages:
  - requests
  - beautifulsoup4
  - markdown
  - networkx
  - matplotlib

Install dependencies:

```bash
pip install requests beautifulsoup4 markdown networkx matplotlib
```

## Usage

### Step 1: Scrape the Documentation

```bash
python umich-arc-scraper.py
```

This will:
- Start crawling from https://documentation.its.umich.edu/advanced-research-computing
- Visit all linked pages within the documentation site
- Save each page as a JSON file in the `umich_arc_docs` directory
- Create a link map and index for all scraped pages

The scraper performs the following:
- Respects server load by waiting between requests
- Follows only links within the documentation site
- Saves progress periodically in case of interruption
- Logs all activity to a log file for monitoring

### Step 2: Process the Scraped Data

```bash
python umich-arc-processor.py
```

This will:
- Load all scraped pages from the `umich_arc_docs` directory
- Categorize pages based on URL structure
- Build a graph representing the link structure
- Generate HTML versions of all pages in the `umich_arc_processed/html` directory
- Extract a knowledge base with services, resources, and FAQ items
- Create visualizations of the documentation structure

## Output

The scripts produce the following outputs:

### Scraper Output (`umich_arc_docs/`)

- JSON files for each scraped page including:
  - Page title
  - URL
  - Text content
  - Outgoing links
- `link_map.json`: Map of links between pages
- `visited_urls.json`: List of all visited URLs
- `index.json`: Index of all scraped pages

### Processor Output (`umich_arc_processed/`)

- `categories.json`: Pages categorized by URL structure
- `link_graph.json`: Graph data representing the link structure
- `knowledge_base.json`: Extracted information about services, resources, and FAQs
- `graph_visualization.png`: Visualization of the link structure

### HTML Output (`umich_arc_processed/html/`)

- HTML files for each page with:
  - Formatted content
  - Navigation links
  - Source information
- `index.html`: Index of all pages organized by category

## Customization

You can customize the behavior of the scripts by modifying the constants at the top of each file:

### Scraper Customization

- `BASE_URL`: Starting URL for the scraper
- `OUTPUT_DIR`: Directory to save scraped data
- `DELAY`: Delay between requests in seconds
- `MAX_PAGES`: Maximum number of pages to scrape

### Processor Customization

- `INPUT_DIR`: Directory containing scraped data
- `OUTPUT_DIR`: Directory to save processed data

## Notes

- The scraper respects the server by including a delay between requests.
- The processor requires matplotlib for visualization, which can be removed if not needed.
- HTML generation uses a simple template that can be customized for your needs.

## Future Improvements

Potential enhancements to consider:

1. Add command-line arguments for customization
2. Implement more sophisticated text extraction and processing
3. Create a full-text search index
4. Add support for downloading images and other assets
5. Improve the knowledge base extraction with NLP techniques
6. Generate a PDF version of the entire documentation

## License

This project is for educational and research purposes only. Please respect the University of Michigan's terms of service when using these tools.