import requests

r = requests.post('http://localhost:8000/api/v1/auth/login',
    json={'username': 'admin', 'password': 'admin123'})
t = r.json()['token']
h = {'Authorization': f'Bearer {t}'}

for q in ['差旅报销流程', '财务报销管理制度', '政府采购法', '预算编制方法', '员工考勤制度']:
    r = requests.post('http://localhost:8000/api/v1/qa/ask',
        json={'question': q, 'kb_ids': [1, 2], 'session_id': 'demo'}, headers=h)
    print(f'{q}: {r.status_code}')

r = requests.get('http://localhost:8000/api/v1/dashboard/qa-stats', headers=h)
d = r.json()
print(f'\nTotal QA: {d["total_qa"]}')
for t in d['trend']:
    print(f'  {t["date"]}: {t["count"]} items')
