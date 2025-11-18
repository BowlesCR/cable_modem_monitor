import requests

***REMOVED*** This should be flagged - no timeout
requests.get("http://example.com")

***REMOVED*** This should be flagged - no timeout
requests.get("http://example.com", headers={"User-Agent": "test"})

***REMOVED*** This should NOT be flagged - has timeout
requests.get("http://example.com", timeout=30)

***REMOVED*** This should NOT be flagged - has timeout
requests.get("http://example.com", headers={"User-Agent": "test"}, timeout=5)
