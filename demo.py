"""
Demo Script for Fake News Origin Tracer
Demonstrates the complete workflow with sample data
"""

import time
from scraper import search_related_articles
from graph_builder import build_propagation_graph, trace_origin
from credibility_checker import batch_check_credibility, generate_credibility_report, check_credibility

def print_separator():
    print("\n" + "="*70 + "\n")

def demo_trace_workflow():
    """
    Complete demonstration of the news tracing workflow
    """
    print("🔍 FAKE NEWS ORIGIN TRACER - DEMO")
    print_separator()
    
    # Demo URL
    demo_query = "artificial intelligence breakthrough"
    print(f"📰 Demo Query: '{demo_query}'")
    print_separator()
    
    # Step 1: Search for related articles
    print("STEP 1: Searching for related articles...")
    start_time = time.time()
    
    articles = search_related_articles(demo_query, num_results=10)
    
    search_time = time.time() - start_time
    print(f"✓ Found {len(articles)} articles in {search_time:.2f} seconds")
    
    # Display sample articles
    print("\nSample Articles Found:")
    for i, article in enumerate(articles[:3], 1):
        metadata = article.get('metadata', article)
        print(f"  {i}. {metadata.get('title', 'Unknown')[:60]}...")
        print(f"     Domain: {metadata.get('domain', 'Unknown')}")
        print(f"     Date: {metadata.get('publish_date', 'Unknown')}")
    
    print_separator()
    
    # Step 2: Build propagation graph
    print("STEP 2: Building propagation network...")
    start_time = time.time()
    
    graph = build_propagation_graph(articles)
    
    graph_time = time.time() - start_time
    print(f"✓ Graph constructed in {graph_time:.2f} seconds")
    print(f"  Nodes (articles): {graph.number_of_nodes()}")
    print(f"  Edges (connections): {graph.number_of_edges()}")
    
    print_separator()
    
    # Step 3: Trace origin
    print("STEP 3: Tracing news origin...")
    start_time = time.time()
    
    origin_result = trace_origin(graph, articles[0]['url'])
    
    trace_time = time.time() - start_time
    print(f"✓ Origin traced in {trace_time:.2f} seconds")
    print(f"\n📍 Origin Analysis:")
    print(f"  Origin Domain: {origin_result.get('origin_domain', 'Unknown')}")
    print(f"  Propagation: {origin_result.get('total_propagation', 0)} sources")
    print(f"  Mainstream Coverage: {origin_result.get('mainstream_coverage', 0)} outlets")
    print(f"\n  Summary: {origin_result.get('summary', 'No summary available')}")
    
    print_separator()
    
    # Step 4: Check credibility
    print("STEP 4: Assessing credibility...")
    start_time = time.time()
    
    credibility_scores = batch_check_credibility(articles)
    
    cred_time = time.time() - start_time
    print(f"✓ Credibility assessed in {cred_time:.2f} seconds")
    
    # Generate report
    report = generate_credibility_report(credibility_scores)
    
    print(f"\n📊 Credibility Report:")
    print(f"  Total Sources Analyzed: {report['total']}")
    print(f"  Average Credibility Score: {report['avg_score']:.1f}/10")
    print(f"  High Credibility (Green): {report['low_risk']} sources")
    print(f"  Medium Credibility (Yellow): {report['medium_risk']} sources")
    print(f"  Low Credibility (Red): {report['high_risk']} sources")
    
    # Show detailed scores for top 3
    print("\n  Top 3 Sources by Credibility:")
    sorted_scores = sorted(credibility_scores.items(), key=lambda x: x[1]['score'], reverse=True)
    for i, (url, score_data) in enumerate(sorted_scores[:3], 1):
        print(f"    {i}. Score: {score_data['score']:.1f}/10 - {score_data['domain']}")
        print(f"       Risk Level: {score_data['risk_level']}")
        if score_data['flags']:
            print(f"       Flags: {score_data['flags'][0]}")
    
    print_separator()
    
    # Performance summary
    total_time = search_time + graph_time + trace_time + cred_time
    print("⚡ PERFORMANCE METRICS:")
    print(f"  Total Processing Time: {total_time:.2f} seconds")
    print(f"  Articles Processed: {len(articles)}")
    print(f"  Processing Speed: {len(articles)/total_time:.1f} articles/second")
    
    print_separator()
    print("✅ DEMO COMPLETED SUCCESSFULLY")
    print("\nTo see the full visualization, run: python app.py")
    print("Then visit: http://localhost:5000")
    print_separator()

if __name__ == "__main__":
    demo_trace_workflow() 
