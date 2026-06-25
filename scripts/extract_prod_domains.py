# -*- coding: utf-8 -*-
"""Extracts and analyzes all unique domains used in explainer_links and spec_link from public production API, stripping XSSI prefix."""

import json
import requests
from urllib.parse import urlparse
from collections import Counter

def main():
    api_url = "https://www.chromestatus.com/api/v0/features"
    print(f"Fetching features from public production API: {api_url}...")
    
    try:
        resp = requests.get(api_url, timeout=30)
        print(f"HTTP Status: {resp.status_code}")
        print(f"Content Type: {resp.headers.get('Content-Type')}")
        print(f"Response Length: {len(resp.text)} characters")
        
        if resp.status_code != 200:
            print(f"Failed to fetch features: HTTP {resp.status_code}")
            return
            
        text = resp.text.strip()
        
        # Strip XSSI prefix if present
        if text.startswith(")]}'"):
            print("Detected XSSI protection prefix. Stripping...")
            parts = text.split('\n', 1)
            if len(parts) > 1:
                text = parts[1].strip()
            else:
                text = text[4:].strip()
                
        try:
            data = json.loads(text)
        except Exception as json_err:
            print(f"JSON Parsing Error: {json_err}")
            print("First 500 characters of response:")
            print(resp.text[:500])
            return
        
        # Handle both list and dict-wrapped-list formats
        features = data
        if isinstance(data, dict) and "features" in data:
            features = data["features"]
            
        if not isinstance(features, list):
            print(f"Unexpected API response format: {type(data)}")
            return
            
        print(f"Successfully fetched {len(features)} features from production.")
        
        domains = Counter()
        explainer_count = 0
        spec_count = 0
        
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
                            domains[parsed.netloc.lower()] += 1
                            explainer_count += 1
                    except Exception:
                        pass
            
            # 2. Process spec link
            spec = f.get('spec_link')
            if spec:
                try:
                    parsed = urlparse(spec.strip())
                    if parsed.netloc:
                        domains[parsed.netloc.lower()] += 1
                        spec_count += 1
                except Exception:
                    pass
                    
        print("\n--- Domain Extraction Results (Production Live Data) ---")
        print(f"Total explainer links processed: {explainer_count}")
        print(f"Total spec links processed: {spec_count}")
        print(f"Total unique domains found: {len(domains)}")
        print("\nDomains sorted by frequency:")
        for domain, freq in domains.most_common():
            print(f"  {domain}: {freq}")
            
    except Exception as e:
        print(f"Error executing API fetch: {e}")

if __name__ == '__main__':
    main()
