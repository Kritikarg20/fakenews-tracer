"""
Graph Builder Module - Construct and analyze propagation networks
"""

import networkx as nx
from difflib import SequenceMatcher
from datetime import datetime
from dateutil import parser as date_parser

def build_propagation_graph(articles_list):
    """
    Build a directed graph showing how news propagated between sources
    
    Args:
        articles_list (list): List of article dictionaries with metadata
        
    Returns:
        networkx.DiGraph: Directed graph with articles as nodes and propagation as edges
    """
    G = nx.DiGraph()
    
    # Add nodes for each article
    for article in articles_list:
        url = article.get('url', '')
        metadata = article.get('metadata', article)  # Handle both formats
        
        G.add_node(url,
                   title=metadata.get('title', 'Unknown'),
                   author=metadata.get('author', 'Unknown'),
                   publish_date=metadata.get('publish_date', 'Unknown'),
                   domain=metadata.get('domain', article.get('domain', 'Unknown')),
                   sources=metadata.get('sources', []))
    
    # Create edges based on relationships
    nodes_list = list(G.nodes(data=True))
    
    for i, (url1, data1) in enumerate(nodes_list):
        for j, (url2, data2) in enumerate(nodes_list):
            if i == j:
                continue
            
            # Check if article 1 links to article 2
            sources1 = data1.get('sources', [])
            for source in sources1:
                if url2 in source.get('url', '') or data2['domain'] in source.get('domain', ''):
                    weight = calculate_edge_weight(data1, data2)
                    G.add_edge(url1, url2, weight=weight, relationship='citation')
            
            # Check title similarity (potential propagation without direct citation)
            title1 = data1.get('title', '')
            title2 = data2.get('title', '')
            similarity = SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
            
            if similarity > 0.7:  # 70% similarity threshold
                # Determine direction based on publish date
                date1 = parse_date_safe(data1.get('publish_date', ''))
                date2 = parse_date_safe(data2.get('publish_date', ''))
                
                if date1 and date2:
                    if date1 < date2:
                        # Article 1 published before Article 2
                        weight = calculate_edge_weight(data1, data2)
                        if not G.has_edge(url1, url2):  # Don't override citation edges
                            G.add_edge(url1, url2, weight=weight, relationship='similarity')
                    elif date2 < date1:
                        weight = calculate_edge_weight(data2, data1)
                        if not G.has_edge(url2, url1):
                            G.add_edge(url2, url1, weight=weight, relationship='similarity')
    
    return G

def calculate_edge_weight(source_data, target_data):
    """
    Calculate edge weight based on recency and other factors
    
    Args:
        source_data (dict): Source node data
        target_data (dict): Target node data
        
    Returns:
        float: Edge weight (higher = stronger connection)
    """
    weight = 1.0
    
    # Increase weight for newer articles (recency bonus)
    target_date = parse_date_safe(target_data.get('publish_date', ''))
    if target_date:
        days_old = (datetime.now() - target_date).days
        if days_old < 7:
            weight += 2.0
        elif days_old < 30:
            weight += 1.0
        elif days_old < 90:
            weight += 0.5
    
    # Increase weight if same domain (internal propagation)
    if source_data.get('domain') == target_data.get('domain'):
        weight += 0.5
    
    return weight

def parse_date_safe(date_string):
    """
    Safely parse date string
    
    Args:
        date_string (str): Date string to parse
        
    Returns:
        datetime or None: Parsed datetime object or None if parsing fails
    """
    try:
        if date_string and date_string != 'Unknown' and date_string != 'Unknown Date':
            return date_parser.parse(date_string)
    except:
        pass
    return None

def trace_origin(graph, start_url):
    """
    Trace the origin of a news story using graph analysis
    
    Args:
        graph (networkx.DiGraph): The propagation graph
        start_url (str): Starting URL for tracing
        
    Returns:
        dict: Origin information including root node and propagation path
    """
    if not graph.nodes():
        return {
            'origin': None,
            'path': [],
            'summary': 'No data available for tracing'
        }
    
    # Find the potential origin node (oldest article with lowest in-degree)
    origin_candidates = []
    
    for node in graph.nodes():
        node_data = graph.nodes[node]
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)
        publish_date = parse_date_safe(node_data.get('publish_date', ''))
        
        # Origin candidates: old articles that cite few sources but are cited by many
        score = out_degree - in_degree
        if publish_date:
            days_old = (datetime.now() - publish_date).days
            score += days_old / 10  # Older = higher score
        
        origin_candidates.append({
            'node': node,
            'score': score,
            'date': publish_date,
            'domain': node_data.get('domain', 'Unknown')
        })
    
    # Sort by score (highest first)
    origin_candidates.sort(key=lambda x: x['score'], reverse=True)
    
    if not origin_candidates:
        return {
            'origin': start_url,
            'path': [start_url],
            'summary': 'Unable to determine origin'
        }
    
    origin_node = origin_candidates[0]['node']
    origin_domain = origin_candidates[0]['domain']
    
    # Find propagation path from origin to other nodes
    path = [origin_node]
    propagated_to = []
    
    # Use BFS to find all nodes reachable from origin
    if origin_node in graph:
        try:
            descendants = nx.descendants(graph, origin_node)
            propagated_to = list(descendants)
        except:
            propagated_to = []
    
    # Count mainstream vs alternative sources
    mainstream_domains = ['bbc.com', 'cnn.com', 'reuters.com', 'apnews.com', 
                          'nytimes.com', 'washingtonpost.com', 'theguardian.com']
    mainstream_count = sum(1 for url in propagated_to 
                          if any(domain in graph.nodes[url].get('domain', '') 
                                for domain in mainstream_domains))
    
    # Generate summary
    summary = f"Story originated on {origin_domain}"
    if propagated_to:
        summary += f", then spread to {len(propagated_to)} other sources"
        if mainstream_count > 0:
            summary += f" (including {mainstream_count} mainstream outlets)"
    else:
        summary += " (no clear propagation detected)"
    
    return {
        'origin': origin_node,
        'origin_domain': origin_domain,
        'path': path + propagated_to[:5],  # Limit path display
        'summary': summary,
        'total_propagation': len(propagated_to),
        'mainstream_coverage': mainstream_count
    }  
