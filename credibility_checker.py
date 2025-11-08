"""
Credibility Checker Module - Assess news source credibility
"""

import re
from datetime import datetime
from dateutil import parser as date_parser

# Domain reputation lists
WHITELIST_DOMAINS = [
    'bbc.com', 'bbc.co.uk', 'reuters.com', 'apnews.com', 'npr.org',
    'theguardian.com', 'nytimes.com', 'washingtonpost.com', 'wsj.com',
    'economist.com', 'ft.com', 'bloomberg.com', 'cnn.com', 'abcnews.go.com',
    'cbsnews.com', 'nbcnews.com', 'pbs.org', 'time.com', 'newsweek.com'
]

BLACKLIST_DOMAINS = [
    'fake-news.com', 'conspiracy-site.org', 'clickbait-news.net',
    'hoax-stories.com', 'unreliable-source.info', 'propaganda-daily.com'
]

# Suspicious patterns in domains
SUSPICIOUS_PATTERNS = [
    r'\.xyz$', r'\.tk$', r'\.ml$',  # Cheap TLDs often used for fake news
    r'\d{2,}',  # Multiple numbers in domain
    r'(fake|hoax|satire|parody)',  # Explicit fake news indicators
]

def check_credibility(article_dict, custom_blacklist=None):
    """
    Assess the credibility of a news article
    
    Args:
        article_dict (dict): Article data with metadata
        custom_blacklist (list, optional): Additional domains to flag as unreliable
        
    Returns:
        dict: Credibility score (0-10), flags, and color indicator
    """
    if custom_blacklist is None:
        custom_blacklist = BLACKLIST_DOMAINS
    else:
        custom_blacklist = BLACKLIST_DOMAINS + custom_blacklist
    
    # Extract metadata (handle both nested and flat structures)
    metadata = article_dict.get('metadata', article_dict)
    domain = metadata.get('domain', article_dict.get('domain', 'unknown'))
    author = metadata.get('author', 'Unknown')
    publish_date = metadata.get('publish_date', 'Unknown')
    title = metadata.get('title', '')
    
    score = 5  # Start with neutral score
    flags = []
    
    # 1. Domain reputation check (+/- 3 points)
    if any(trusted in domain for trusted in WHITELIST_DOMAINS):
        score += 3
        flags.append('✓ Reputable news source')
    elif any(untrusted in domain for untrusted in custom_blacklist):
        score -= 4
        flags.append('⚠ Domain on credibility watchlist')
    
    # 2. Domain pattern analysis (-2 points for suspicious)
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, domain, re.IGNORECASE):
            score -= 2
            flags.append('⚠ Suspicious domain pattern detected')
            break
    
    # 3. Author verification (+1 point)
    if author and author != 'Unknown' and author != 'Unknown Author':
        # Check if author name looks legitimate (has first and last name)
        if len(author.split()) >= 2 and not any(char.isdigit() for char in author):
            score += 1
            flags.append('✓ Author identified')
        else:
            flags.append('⚠ Questionable author attribution')
    else:
        score -= 1
        flags.append('⚠ No author information')
    
    # 4. Recency check (-1 per year old)
    try:
        if publish_date and publish_date not in ['Unknown', 'Unknown Date']:
            pub_date = date_parser.parse(publish_date)
            age_years = (datetime.now() - pub_date).days / 365
            
            if age_years > 1:
                score -= int(age_years)
                flags.append(f'⚠ Article is {int(age_years)} year(s) old')
            elif age_years < 0.1:  # Very recent (within ~36 days)
                score += 1
                flags.append('✓ Recent publication')
    except:
        flags.append('⚠ Unable to verify publication date')
    
    # 5. Title analysis (sensationalism check)
    sensational_indicators = [
        r'BREAKING[!:\s]', r'SHOCKING', r'UNBELIEVABLE', r'YOU WON\'?T BELIEVE',
        r'EXPOSED', r'CONSPIRACY', r'SECRET', r'REVEALED', r'\b[A-Z]{5,}\b'
    ]
    
    sensational_count = sum(1 for pattern in sensational_indicators 
                           if re.search(pattern, title, re.IGNORECASE))
    
    if sensational_count >= 2:
        score -= 2
        flags.append('⚠ Sensationalized headline detected')
    
    # 6. Multiple exclamation marks or question marks
    if title.count('!') > 1 or title.count('?') > 1:
        score -= 1
        flags.append('⚠ Excessive punctuation in title')
    
    # Normalize score to 0-10 range
    score = max(0, min(10, score))
    
    # Determine color indicator
    if score >= 7:
        color = 'green'
        risk_level = 'Low Risk'
    elif score >= 4:
        color = 'yellow'
        risk_level = 'Medium Risk'
    else:
        color = 'red'
        risk_level = 'High Risk'
    
    return {
        'score': round(score, 1),
        'flags': flags,
        'color': color,
        'risk_level': risk_level,
        'domain': domain,
        'details': {
            'domain_reputation': 'whitelisted' if any(t in domain for t in WHITELIST_DOMAINS) else 'unknown',
            'author_verified': author not in ['Unknown', 'Unknown Author'],
            'is_recent': age_years < 1 if 'age_years' in locals() else None
        }
    }

def batch_check_credibility(articles_list, custom_blacklist=None):
    """
    Check credibility for multiple articles
    
    Args:
        articles_list (list): List of article dictionaries
        custom_blacklist (list, optional): Custom blacklist domains
        
    Returns:
        dict: Mapping of article URLs to credibility results
    """
    results = {}
    
    for article in articles_list:
        url = article.get('url', '')
        if url:
            results[url] = check_credibility(article, custom_blacklist)
    
    return results

def generate_credibility_report(credibility_scores):
    """
    Generate summary report from credibility scores
    
    Args:
        credibility_scores (dict): Mapping of URLs to credibility results
        
    Returns:
        dict: Summary statistics
    """
    if not credibility_scores:
        return {
            'total': 0,
            'avg_score': 0,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0
        }
    
    scores = [v['score'] for v in credibility_scores.values()]
    
    return {
        'total': len(scores),
        'avg_score': round(sum(scores) / len(scores), 2),
        'high_risk': sum(1 for v in credibility_scores.values() if v['color'] == 'red'),
        'medium_risk': sum(1 for v in credibility_scores.values() if v['color'] == 'yellow'),
        'low_risk': sum(1 for v in credibility_scores.values() if v['color'] == 'green'),
        'most_credible': max(credibility_scores.items(), key=lambda x: x[1]['score'])[0],
        'least_credible': min(credibility_scores.items(), key=lambda x: x[1]['score'])[0]
    } 
