#!/usr/bin/env python
"""
University of Michigan ARC Documentation Processor

This script processes the scraped content from the ARC documentation site
and organizes it into a more usable structure.
"""

import os
import json
import re
import logging
from collections import defaultdict
import markdown
import networkx as nx
import matplotlib.pyplot as plt
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arc_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_DIR = "umich_arc_docs"
OUTPUT_DIR = "umich_arc_processed"
HTML_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "html")


class ARCDocProcessor:
    """Processor for University of Michigan ARC Documentation."""
    
    def __init__(self, input_dir=INPUT_DIR, output_dir=OUTPUT_DIR):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.html_output_dir = os.path.join(output_dir, "html")
        self.pages = {}
        self.categories = defaultdict(list)
        self.graph = nx.DiGraph()
        
        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.html_output_dir, exist_ok=True)
        
    def load_data(self):
        """Load all scraped pages."""
        logger.info("Loading scraped data")
        
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.json') and filename != 'index.json' and filename != 'link_map.json' and filename != 'visited_urls.json':
                file_path = os.path.join(self.input_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        page_data = json.load(f)
                        self.pages[page_data['url']] = page_data
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {e}")
                    
        logger.info(f"Loaded {len(self.pages)} pages")
        
    def categorize_pages(self):
        """Categorize pages based on URL structure."""
        logger.info("Categorizing pages")
        
        for url, page in self.pages.items():
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) > 0:
                category = path_parts[0] if path_parts[0] else "root"
                self.categories[category].append(url)
            else:
                self.categories["root"].append(url)
                
        # Save categories
        with open(os.path.join(self.output_dir, 'categories.json'), 'w', encoding='utf-8') as f:
            json.dump(dict(self.categories), f, indent=2)
            
        logger.info(f"Categorized pages into {len(self.categories)} categories")
        
    def build_link_graph(self):
        """Build a graph representing the link structure."""
        logger.info("Building link graph")
        
        # Add all pages as nodes
        for url in self.pages:
            self.graph.add_node(url, title=self.pages[url]['title'])
            
        # Add links as edges
        for url, page in self.pages.items():
            for link in page['links']:
                link_url = link['url']
                if link_url in self.pages:  # Only add edges to pages we've scraped
                    self.graph.add_edge(url, link_url, text=link['text'])
                    
        logger.info(f"Graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
        # Save graph data
        graph_data = {
            'nodes': [{'id': node, 'title': self.graph.nodes[node]['title']} for node in self.graph.nodes],
            'edges': [{'source': u, 'target': v, 'text': self.graph.edges[u, v]['text']} for u, v in self.graph.edges]
        }
        
        with open(os.path.join(self.output_dir, 'link_graph.json'), 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2)
            
    def visualize_graph(self):
        """Create a visualization of the link graph."""
        try:
            logger.info("Creating graph visualization")
            
            # Only visualize if the graph is not too large
            if self.graph.number_of_nodes() > 100:
                logger.warning("Graph too large to visualize effectively")
                return
                
            plt.figure(figsize=(20, 20))
            pos = nx.spring_layout(self.graph)
            nx.draw(
                self.graph, 
                pos, 
                with_labels=False, 
                node_size=50, 
                alpha=0.6, 
                arrows=True
            )
            
            # Save visualization
            plt.savefig(os.path.join(self.output_dir, 'graph_visualization.png'), dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info("Graph visualization created")
        except Exception as e:
            logger.error(f"Error creating graph visualization: {e}")
            
    def generate_html(self):
        """Generate HTML versions of the pages."""
        logger.info("Generating HTML versions")
        
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{ 
            background-color: #00274c; 
            color: white;
            padding: 10px 20px;
            margin-bottom: 20px;
        }}
        h1 {{ margin-top: 0; }}
        .content {{ padding: 0 20px; }}
        .links {{ 
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 20px;
        }}
        .links h2 {{ color: #00274c; }}
        .links ul {{ padding-left: 20px; }}
        footer {{ 
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
            color: #666;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>{title}</h1>
    </header>
    <div class="content">
        {content}
        
        <div class="links">
            <h2>Related Pages</h2>
            <ul>
                {links}
            </ul>
        </div>
    </div>
    <footer>
        <p>Source: <a href="{url}">{url}</a></p>
        <p>Generated from University of Michigan Advanced Research Computing Documentation</p>
    </footer>
</body>
</html>
"""
        
        for url, page in self.pages.items():
            try:
                # Create a safe filename
                parsed_url = urlparse(url)
                filename = parsed_url.path.replace('/', '_')
                if parsed_url.query:
                    filename += '_' + parsed_url.query.replace('=', '_')
                filename = re.sub(r'[^\w\-.]', '_', filename)
                if not filename:
                    filename = 'index'
                filename += '.html'
                
                # Convert content to HTML using Markdown as a helper
                content_html = markdown.markdown(page['content'].replace('\n', '\n\n'))
                
                # Format links
                links_html = ""
                for link in page['links']:
                    if link['url'] in self.pages:  # Only include links to pages we've scraped
                        links_html += f'<li><a href="{os.path.basename(self.get_html_filename(link["url"]))}">{link["text"]}</a></li>\n'
                
                # Fill in template
                html_content = html_template.format(
                    title=page['title'],
                    content=content_html,
                    links=links_html,
                    url=url
                )
                
                # Save HTML file
                with open(os.path.join(self.html_output_dir, filename), 'w', encoding='utf-8') as f:
                    f.write(html_content)
                    
            except Exception as e:
                logger.error(f"Error generating HTML for {url}: {e}")
                
        logger.info(f"Generated HTML versions for {len(self.pages)} pages")
        
        # Create index.html
        self.create_html_index()
        
    def get_html_filename(self, url):
        """Generate HTML filename for a URL."""
        parsed_url = urlparse(url)
        filename = parsed_url.path.replace('/', '_')
        if parsed_url.query:
            filename += '_' + parsed_url.query.replace('=', '_')
        filename = re.sub(r'[^\w\-.]', '_', filename)
        if not filename:
            filename = 'index'
        return filename + '.html'
        
    def create_html_index(self):
        """Create an HTML index of all pages."""
        logger.info("Creating HTML index")
        
        categories_html = ""
        for category, urls in self.categories.items():
            if urls:  # Skip empty categories
                categories_html += f'<h2>{category.capitalize()}</h2>\n<ul>\n'
                for url in urls:
                    if url in self.pages:
                        categories_html += f'<li><a href="{self.get_html_filename(url)}">{self.pages[url]["title"]}</a></li>\n'
                categories_html += '</ul>\n'
        
        index_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>University of Michigan ARC Documentation Index</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{ 
            background-color: #00274c; 
            color: white;
            padding: 10px 20px;
            margin-bottom: 20px;
        }}
        h1 {{ margin-top: 0; }}
        h2 {{ color: #00274c; }}
        .content {{ padding: 0 20px; }}
        ul {{ padding-left: 20px; }}
        footer {{ 
            margin-top: 30px;
            border-top: 1px solid #ccc;
            padding-top: 10px;
            color: #666;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <header>
        <h1>University of Michigan ARC Documentation Index</h1>
    </header>
    <div class="content">
        <p>This is an index of all scraped pages from the University of Michigan Advanced Research Computing documentation.</p>
        
        {categories_html}
        
    </div>
    <footer>
        <p>Generated from University of Michigan Advanced Research Computing Documentation</p>
    </footer>
</body>
</html>
"""
        
        with open(os.path.join(self.html_output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
            
        logger.info("HTML index created")
        
    def extract_knowledge_base(self):
        """Extract a structured knowledge base from the content."""
        logger.info("Extracting knowledge base")
        
        # Create a simple knowledge base with key topics
        knowledge_base = {
            "topics": {},
            "services": {},
            "resources": {},
            "faq": []
        }
        
        # Extract services
        service_patterns = [
            r"(Great Lakes|Armis2|Lighthouse)\s+is\s+([^\.]+)",
            r"(Turbo|Locker|Data Den)\s+is\s+([^\.]+)"
        ]
        
        for url, page in self.pages.items():
            content = page['content']
            
            # Extract services
            for pattern in service_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    service_name = match[0].strip()
                    service_desc = match[1].strip()
                    if service_name not in knowledge_base["services"]:
                        knowledge_base["services"][service_name] = {
                            "description": service_desc,
                            "mentions": [url]
                        }
                    else:
                        knowledge_base["services"][service_name]["mentions"].append(url)
                        
            # Extract FAQ items
            if "?" in content:
                paragraphs = content.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if "?" in para and i < len(paragraphs) - 1:
                        question = para.strip()
                        # Check if this is likely a question
                        if question.endswith('?') and len(question) < 200:
                            answer = paragraphs[i+1].strip()
                            knowledge_base["faq"].append({
                                "question": question,
                                "answer": answer,
                                "source": url
                            })
                            
        # Save knowledge base
        with open(os.path.join(self.output_dir, 'knowledge_base.json'), 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2)
            
        logger.info(f"Knowledge base extracted with {len(knowledge_base['services'])} services and {len(knowledge_base['faq'])} FAQ items")
        
    def run(self):
        """Run the full processing pipeline."""
        try:
            logger.info("Starting processing")
            self.load_data()
            self.categorize_pages()
            self.build_link_graph()
            self.visualize_graph()
            self.generate_html()
            
            # Skip knowledge base extraction for now since it's causing issues
            # We'll add it back later
            # self.extract_knowledge_base()
            logger.info("Processing completed successfully")
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            raise


if __name__ == "__main__":
    processor = ARCDocProcessor()
    processor.run()