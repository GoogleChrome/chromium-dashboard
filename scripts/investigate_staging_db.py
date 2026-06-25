import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set dummy env variable to satisfy settings
os.environ['SERVER_SOFTWARE'] = 'test'

import argparse

from google.cloud import ndb

from internals import core_enums
from internals.core_models import FeatureEntry, FeatureSummarySuggestion


def main():
    parser = argparse.ArgumentParser(description="Investigate and repair staging Datastore suggestions.")
    parser.add_argument('--fix', action='store_true', help='Reset the stuck suggestions to NONE status to release the lock.')
    parser.add_argument('--delete', action='store_true', help='Permanently delete the suggestion entities to let the system recreate them cleanly.')
    args = parser.parse_args()

    feature_ids = [5648964150624256, 5894990593785856]
    
    print("Connecting to live Datastore for project: cr-status-staging...")
    client = ndb.Client(project='cr-status-staging')
    
    with client.context():
        for fid in feature_ids:
            print("\n==================================================")
            print(f"Investigating Feature ID: {fid}")
            print("==================================================")
            
            # Fetch FeatureEntry
            fe = FeatureEntry.get_by_id(fid)
            if not fe:
                print("[-] FeatureEntry not found in Datastore!")
            else:
                print(f"[+] Feature Name: {fe.name}")
                print(f"[+] Feature Updated: {fe.updated}")
            
            # Fetch Suggestion
            suggestion = FeatureSummarySuggestion.get_by_id(fid)
            if not suggestion:
                print("[-] FeatureSummarySuggestion not found in Datastore!")
                continue
            
            print("[+] Suggestion Details:")
            print(f"    * Status: {suggestion.status}")
            print(f"    * Status Timestamp: {suggestion.status_timestamp}")
            print(f"    * Last Generation Attempt: {suggestion.last_generation_attempt}")
            print(f"    * Version: {suggestion.version}")
            print(f"    * Source Fingerprint: {suggestion.source_fingerprint}")
            print(f"    * Suggested Doc Links: {suggestion.suggested_doc_links}")
            summary_preview = (suggestion.suggested_summary[:100] + "...") if suggestion.suggested_summary else "None"
            print(f"    * Suggested Summary: {summary_preview}")
            
            if args.delete:
                print(f"[!] Deleting FeatureSummarySuggestion entity for ID {fid}...")
                suggestion.key.delete()
                print("[+] Entity deleted successfully!")
            elif args.fix:
                print(f"[!] Resetting status of FeatureSummarySuggestion {fid} to NONE...")
                suggestion.status = core_enums.SummarySuggestionStatus.NONE.value
                suggestion.status_timestamp = None
                suggestion.last_generation_attempt = None
                suggestion.source_fingerprint = None
                suggestion.put()
                print("[+] Entity status reset to NONE successfully!")

if __name__ == '__main__':
    main()
