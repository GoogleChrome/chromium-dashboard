# -*- coding: utf-8 -*-
"""Extracts and analyzes all unique domains across the entire production database by paginating if needed."""

import json
import requests
from urllib.parse import urlparse
from collections import Counter

def main():
    # The main public endpoint that returns all features is /api/v0/features
    # Let's check if we can fetch all features or if we need to paginate.
    # In Chromestatus, the public endpoint /api/v0/features?num=2000 or similar can be used to fetch all.
    # Let's try fetching with a high limit, or paginate if the API supports it.
    api_url = "https://www.chromestatus.com/api/v0/features?num=5000"
    print(f"Fetching all features from public production API: {api_url}...")
    
    try:
        resp = requests.get(api_url, timeout=60)
        print(f"HTTP Status: {resp.status_code}")
        print(f"Response Length: {len(resp.text)} characters")
        
        text = resp.text.strip()
        if text.startswith(")]}'"):
            parts = text.split('\n', 1)
            if len(parts) > 1:
                text = parts[1].strip()
            else:
                text = text[4:].strip()
                
        data = json.loads(text)
        
        features = data
        if isinstance(data, dict) and "features" in data:
            features = data["features"]
            
        if not isinstance(features, list):
            print(f"Unexpected API response format: {type(data)}")
            return
            
        print(f"Successfully fetched {len(features)} features from production.")
        
        spec_domains = Counter()
        explainer_domains = Counter()
        
        for f in features:
            # 1. Process explainer links
            explainers = f.get('explainer_links') or []
            resources = f.get('resources') or {}
            if isinstance(resources, dict) and 'explainers' in resources:
                explainers.extend(resources['explainers'] or [])
                
            for link in explainers:
                if link:
                    try:
                        parsed = urlparse(link.strip())
                        if parsed.netloc:
                            explainer_domains[parsed.netloc.lower()] += 1
                    except Exception:
                        pass
            
            # 2. Process spec link
            spec = f.get('spec_link')
            if spec:
                try:
                    parsed = urlparse(spec.strip())
                    if parsed.netloc:
                        spec_domains[parsed.netloc.lower()] += 1
                except Exception:
                    pass
                    
        print("\n--- Spec Link Domains (All Production Features) ---")
        for domain, freq in spec_domains.most_common():
            print(f"  {domain}: {freq}")
            
        print("\n--- Explainer Link Domains (All Production Features) ---")
        for domain, freq in explainer_domains.most_common():
            print(f"  {domain}: {freq}")
            
    except Exception as e:
        print(f"Error executing API fetch: {e}")

if __name__ == '__main__':
    main()
