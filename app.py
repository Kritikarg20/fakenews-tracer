"""
Fake News Origin Tracer - Flask Application
Main entry point for the web application
"""

from flask import Flask, render_template, request, jsonify
from scraper import scrape_article_metadata, search_related_articles
from graph_builder import build_propagation_graph, trace_origin
from credibility_checker import check_credibility
import json
import traceback

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main page with input form"""
    return render_template('index.html')

@app.route('/trace', methods=['POST'])
def trace_news():
    """
    Main route to trace news propagation
    Accepts URL or keyword and returns analysis
    """
    try:
        input_data = request.form.get('input_data', '').strip()
        input_type = request.form.get('input_type', 'url')
        
        if not input_data:
            return jsonify({'error': 'Please provide a URL or keyword'}), 400
        
        # Step 1: Search for related articles
        print(f"Searching for articles related to: {input_data}")
        articles = search_related_articles(input_data, num_results=10)
        
        if not articles:
            return jsonify({'error': 'No articles found. Try a different query.'}), 404
        
        # Step 2: Build propagation graph
        print(f"Building graph with {len(articles)} articles...")
        graph = build_propagation_graph(articles)
        
        # Step 3: Trace origin
        print("Tracing origin...")
        origin_path = trace_origin(graph, articles[0]['url'])
        
        # Step 4: Check credibility for all articles
        print("Checking credibility...")
        credibility_scores = {}
        for article in articles:
            cred_result = check_credibility(article)
            credibility_scores[article['url']] = cred_result
        
        # Step 5: Prepare data for visualization
        graph_data = {
            'nodes': [],
            'links': []
        }
        
        # Add nodes
        for node in graph.nodes():
            node_data = graph.nodes[node]
            cred = credibility_scores.get(node, {'score': 5, 'color': 'yellow'})
            graph_data['nodes'].append({
                'id': node,
                'domain': node_data.get('domain', 'Unknown'),
                'title': node_data.get('title', 'Unknown'),
                'author': node_data.get('author', 'Unknown'),
                'date': node_data.get('publish_date', 'Unknown'),
                'credibility': cred['score'],
                'color': cred['color'],
                'flags': cred.get('flags', [])
            })
        
        # Add edges
        for edge in graph.edges(data=True):
            graph_data['links'].append({
                'source': edge[0],
                'target': edge[1],
                'weight': edge[2].get('weight', 1)
            })
        
        # Generate summary report
        origin_node = origin_path['origin'] if origin_path else 'Unknown'
        summary = {
            'total_articles': len(articles),
            'origin': origin_node,
            'origin_summary': origin_path.get('summary', 'Unable to trace origin'),
            'avg_credibility': sum(c['score'] for c in credibility_scores.values()) / len(credibility_scores) if credibility_scores else 0,
            'high_risk_count': sum(1 for c in credibility_scores.values() if c['color'] == 'red'),
            'path_length': len(origin_path.get('path', []))
        }
        
        return jsonify({
            'success': True,
            'graph': graph_data,
            'origin_path': origin_path,
            'credibility_scores': credibility_scores,
            'summary': summary
        })
        
    except Exception as e:
        print(f"Error in trace_news: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.route('/api/test', methods=['GET'])
def api_test():
    """Test endpoint for API functionality"""
    test_url = "https://www.bbc.com/news/technology"
    try:
        metadata = scrape_article_metadata(test_url)
        return jsonify({
            'status': 'success',
            'test_url': test_url,
            'metadata': metadata
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Fake News Origin Tracer...")
    print("Access the app at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 
