import requests, json
url = 'https://d9ym4p48160x5.cloudfront.net/api/query/generate'
headers = {'X-API-Key': 'dwp-cmg-sec-key-7d9a1f8c', 'Content-Type': 'application/json'}
query = """Please explain the following case calculations in plain English. Remember: use ONLY the exact figures from the data below. Do NOT recalculate or verify any numbers.
Also, please provide a detailed explanation of the rules for calculating Ongoing Maintenance (OGM).

Case Data:
{"masterCaseId": "123", "nrpGrossWeeklyIncome": 500, "cases": [{"calculations": {"totalMonthly": 100}}]}"""

payload = {'model': 'qwen_14b_tuned', 'query': query, 'use_rag': True}
r = requests.post(url, headers=headers, json=payload)
print(r.json()['response'])
