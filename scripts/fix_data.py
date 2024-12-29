#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Google Inc. All Rights Reserved.


from internals import metrics_models

# Pre-fetch all histograms to avoid redundant calls
allCssPropertyHistograms = metrics_models.CssPropertyHistogram.get_all()
allFeatureObserverHistograms = metrics_models.FeatureObserverHistogram.get_all()

def CorrectCSSPropertyName(bucket_id):
    """Fetch the correct CSS property name based on the bucket_id."""
    return allCssPropertyHistograms.get(bucket_id, None)

def CorrectFeaturePropertyName(bucket_id):
    """Fetch the correct Feature property name based on the bucket_id."""
    return allFeatureObserverHistograms.get(bucket_id, None)

def FetchAllCSSPropertiesWithError(bucket_id=None):
    """Fetch all CSS properties with 'ERROR' property name."""
    q = metrics_models.StableInstance.query()
    if bucket_id:
        q = q.filter(metrics_models.StableInstance.bucket_id == bucket_id)
    q = q.filter(metrics_models.StableInstance.property_name == 'ERROR')

    props = q.fetch(None)

    # Exclude bucket 1 as it represents total pages visited
    props = [p for p in props if p.bucket_id > 1]

    return props

def FetchAllFeaturesWithError(bucket_id=None):
    """Fetch all features with 'ERROR' property name."""
    q = metrics_models.FeatureObserver.query()
    if bucket_id:
        q = q.filter(metrics_models.FeatureObserver.bucket_id == bucket_id)
    q = q.filter(metrics_models.FeatureObserver.property_name == 'ERROR')

    return q.fetch(None)

def fix_up(props, corrector_func):
    """
    Correct the property names for the given properties using a corrector function.

    Args:
        props (list): List of properties to correct.
        corrector_func (function): Function to get the correct property name.
    """
    need_correcting = {}

    # Determine corrections needed
    for p in props:
        correct_name = corrector_func(p.bucket_id)
        if correct_name is not None:
            need_correcting[p.bucket_id] = correct_name

    # Apply corrections
    for p in props:
        if p.bucket_id in need_correcting:
            new_name = need_correcting[p.bucket_id]
            print(f"Updating bucket_id {p.bucket_id}: '{p.property_name}' -> '{new_name}'")
            p.property_name = new_name
            try:
                # Uncomment this line to persist changes to the database
                # p.put()
                pass
            except Exception as e:
                print(f"Error updating property {p.bucket_id}: {e}")

def main():
    """Main execution flow."""
    print("Fetching features with 'ERROR'...")
    props = FetchAllFeaturesWithError()
    print(f"Found {len(props)} features tagged 'ERROR'.")
    fix_up(props, corrector_func=CorrectFeaturePropertyName)

    print("Fetching CSS properties with 'ERROR'...")
    css_props = FetchAllCSSPropertiesWithError()
    print(f"Found {len(css_props)} CSS properties tagged 'ERROR'.")
    fix_up(css_props, corrector_func=CorrectCSSPropertyName)

    print("Processing complete.")

if __name__ == "__main__":
    main()
