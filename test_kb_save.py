#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_ingest import data_ingest_manager

# Test KB article data
test_article = {
    'title': 'Test KB Article',
    'problem': 'Test problem description',
    'root_cause': 'Test root cause',
    'solution': 'Test solution steps',
    'prevention': 'Test prevention',
    'tags': 'test, kb, article',
    'source_incidents': 5,
    'filters': {
        'priority': 'P4',
        'category': 'Password Reset',
        'cluster': 'Password Reset'
    }
}

print(f"MongoDB available: {data_ingest_manager.is_available()}")
print(f"Attempting to save test article...")

try:
    success = data_ingest_manager.save_kb_article(test_article)
    print(f"Save result: {success}")
    
    if success:
        print("✅ Test article saved successfully!")
    else:
        print("❌ Failed to save test article")
        
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")