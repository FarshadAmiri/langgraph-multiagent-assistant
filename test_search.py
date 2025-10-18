from ddgs import DDGS

ddgs = DDGS()
results = list(ddgs.text('BMW 5 series price 2024', max_results=5))
print(f'Found {len(results)} results')
for i, r in enumerate(results[:3], 1):
    print(f"{i}. {r.get('title', 'No title')}")
    print(f"   {r.get('body', '')[:100]}...")
