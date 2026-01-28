#!/usr/bin/env python
import sqlite3
import json
import os

# Use the correct database path
db_path = os.path.expanduser("~/.sageframe/sageframe.db")
print(f"Database path: {db_path}")

if not os.path.exists(db_path):
    print(f"✗ Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get the latest extraction result
cursor.execute("""
    SELECT id, mode, provider, raw_text, structured_fields 
    FROM extraction_results 
    ORDER BY id DESC 
    LIMIT 1
""")

result = cursor.fetchone()

if result:
    print(f'\n✓ Result ID: {result["id"]}')
    print(f'✓ Mode: {result["mode"]}')
    print(f'✓ Provider: {result["provider"]}')
    raw_text = result["raw_text"]
    print(f'✓ Raw text length: {len(raw_text) if raw_text else 0} chars')
    
    if raw_text:
        print(f'\n📄 Extracted Text (first 500 chars):')
        print(f'{"=" * 70}')
        print(raw_text[:500])
        print(f'{"=" * 70}')
    else:
        print("\n⚠ No raw text extracted!")
    
    structured = result["structured_fields"]
    if structured:
        print(f'\n📊 Structured Fields:')
        print(f'{"=" * 70}')
        try:
            fields = json.loads(structured)
            for key, value in fields.items():
                print(f'  {key}: {value}')
        except:
            print(f'  {structured}')
    else:
        print("\n⚠ No structured fields extracted!")
else:
    print('✗ No extraction results found')

conn.close()
