"""Debug script to see what search results we're getting"""
from ddgs import DDGS

queries = [
    "how much does a latest bmw 5 series cost? how can i lease it?",
    "BMW 5 series 2024 price",
    "BMW 5 series cost lease 2024",
    "2024 BMW 5 series MSRP starting price"
]

for query in queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print('='*80)
    
    ddgs = DDGS()
    results = list(ddgs.text(query, max_results=5))
    
    print(f"Found {len(results)} results\n")
    
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.get('title', 'No title')}")
        print(f"   URL: {r.get('href', 'No URL')}")
        print(f"   {r.get('body', 'No description')[:200]}...")
        print()
