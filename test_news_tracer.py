"""
Unit tests for Fake News Origin Tracer
Run with: python -m unittest test_news_tracer.py
"""

import unittest
from unittest.mock import patch, Mock
import networkx as nx
from datetime import datetime

# Import modules to test
from scraper import scrape_article_metadata, search_related_articles
from graph_builder import build_propagation_graph, trace_origin, calculate_edge_weight
from credibility_checker import check_credibility, batch_check_credibility, generate_credibility_report


class TestScraper(unittest.TestCase):
    """Test cases for scraper module"""
    
    @patch('scraper.requests.get')
    def test_scrape_article_metadata_success(self, mock_get):
        """Test successful article scraping"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
        <html>
            <head>
                <title>Test Article</title>
                <meta name="author" content="John Doe">
                <meta property="article:published_time" content="2024-01-15T10:00:00Z">
            </head>
            <body>
                <a href="https://external-source.com">External Link</a>
            </body>
        </html>
        '''
        mock_get.return_value = mock_response
        
        result = scrape_article_metadata("https://example.com/article")
        
        self.assertTrue(result['scrape_success'])
        self.assertEqual(result['title'], 'Test Article')
        self.assertEqual(result['author'], 'John Doe')
        self.assertIn('external-source.com', [s['domain'] for s in result['sources']])
    
    @patch('scraper.requests.get')
    def test_scrape_article_metadata_failure(self, mock_get):
        """Test scraping failure and fallback"""
        mock_get.side_effect = Exception("Connection failed")
        
        result = scrape_article_metadata("https://example.com/article")
        
        self.assertFalse(result['scrape_success'])
        self.assertIn('url', result)
        self.assertIn('domain', result)
    
    def test_search_related_articles(self):
        """Test searching for related articles"""
        result = search_related_articles("test news", num_results=5)
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertLessEqual(len(result), 5)
        self.assertIn('url', result[0])
        self.assertIn('domain', result[0])


class TestGraphBuilder(unittest.TestCase):
    """Test cases for graph builder module"""
    
    def setUp(self):
        """Set up test data"""
        self.test_articles = [
            {
                'url': 'https://example1.com/article1',
                'metadata': {
                    'title': 'Breaking: Major Event Happens',
                    'author': 'Reporter One',
                    'publish_date': '2024-01-15',
                    'domain': 'example1.com',
                    'sources': [{'url': 'https://example2.com/article2', 'domain': 'example2.com'}]
                },
                'domain': 'example1.com'
            },
            {
                'url': 'https://example2.com/article2',
                'metadata': {
                    'title': 'Major Event Confirmed',
                    'author': 'Reporter Two',
                    'publish_date': '2024-01-14',
                    'domain': 'example2.com',
                    'sources': []
                },
                'domain': 'example2.com'
            }
        ]
    
    def test_build_propagation_graph(self):
        """Test graph construction"""
        graph = build_propagation_graph(self.test_articles)
        
        self.assertIsInstance(graph, nx.DiGraph)
        self.assertEqual(len(graph.nodes()), 2)
        self.assertGreater(len(graph.edges()), 0)
    
    def test_calculate_edge_weight(self):
        """Test edge weight calculation"""
        source = {'domain': 'example.com', 'publish_date': '2024-01-15'}
        target = {'domain': 'other.com', 'publish_date': '2024-01-16'}
        
        weight = calculate_edge_weight(source, target)
        
        self.assertIsInstance(weight, float)
        self.assertGreater(weight, 0)
    
    def test_trace_origin(self):
        """Test origin tracing"""
        graph = build_propagation_graph(self.test_articles)
        result = trace_origin(graph, self.test_articles[0]['url'])
        
        self.assertIn('origin', result)
        self.assertIn('path', result)
        self.assertIn('summary', result)
        self.assertIsInstance(result['path'], list)


class TestCredibilityChecker(unittest.TestCase):
    """Test cases for credibility checker module"""
    
    def test_check_credibility_trusted_source(self):
        """Test credibility check for trusted source"""
        article = {
            'url': 'https://bbc.com/article',
            'metadata': {
                'domain': 'bbc.com',
                'author': 'John Smith',
                'publish_date': '2024-10-01',
                'title': 'Important News Update'
            }
        }
        
        result = check_credibility(article)
        
        self.assertGreater(result['score'], 6)
        self.assertEqual(result['color'], 'green')
        self.assertIn('flags', result)
    
    def test_check_credibility_suspicious_source(self):
        """Test credibility check for suspicious source"""
        article = {
            'url': 'https://fake-news.com/article',
            'metadata': {
                'domain': 'fake-news.com',
                'author': 'Unknown',
                'publish_date': '2020-01-01',
                'title': 'SHOCKING!!! BREAKING NEWS!!!'
            }
        }
        
        result = check_credibility(article)
        
        self.assertLess(result['score'], 5)
        self.assertEqual(result['color'], 'red')
        self.assertGreater(len(result['flags']), 0)
    
    def test_batch_check_credibility(self):
        """Test batch credibility checking"""
        articles = [
            {'url': 'https://bbc.com/article1', 'metadata': {'domain': 'bbc.com', 'author': 'Test', 'publish_date': '2024-01-01', 'title': 'News'}},
            {'url': 'https://example.com/article2', 'metadata': {'domain': 'example.com', 'author': 'Test', 'publish_date': '2024-01-01', 'title': 'News'}}
        ]
        
        result = batch_check_credibility(articles)
        
        self.assertEqual(len(result), 2)
        self.assertIn('https://bbc.com/article1', result)
        self.assertIn('score', result['https://bbc.com/article1'])
    
    def test_generate_credibility_report(self):
        """Test credibility report generation"""
        scores = {
            'url1': {'score': 8, 'color': 'green'},
            'url2': {'score': 4, 'color': 'yellow'},
            'url3': {'score': 2, 'color': 'red'}
        }
        
        report = generate_credibility_report(scores)
        
        self.assertEqual(report['total'], 3)
        self.assertAlmostEqual(report['avg_score'], 4.67, places=1)
        self.assertEqual(report['high_risk'], 1)
        self.assertEqual(report['low_risk'], 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def test_full_workflow(self):
        """Test complete trace workflow"""
        # Search for articles
        articles = search_related_articles("technology news", num_results=5)
        self.assertGreater(len(articles), 0)
        
        # Build graph
        graph = build_propagation_graph(articles)
        self.assertIsInstance(graph, nx.DiGraph)
        
        # Trace origin
        origin = trace_origin(graph, articles[0]['url'])
        self.assertIn('origin', origin)
        
        # Check credibility
        cred_scores = batch_check_credibility(articles)
        self.assertEqual(len(cred_scores), len(articles))
        
        # Generate report
        report = generate_credibility_report(cred_scores)
        self.assertGreater(report['total'], 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 
