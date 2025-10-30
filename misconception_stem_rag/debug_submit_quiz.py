import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
EMAIL = f"debugtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
PASSWORD = "debugpass123"
PDF_PATH = r"c:\Users\suhas\OneDrive\Desktop\project\Misconception-driven-STEM-question-generation-platform\misconception_stem_rag\data\pdfs\068c259d_organic chemistry.pdf"

async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        # register
        print('Registering...')
        r = await client.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PASSWORD, "name": "Debug User"})
        print('register', r.status_code)
        # login
        r = await client.post(f"{BASE_URL}/auth/login", data={"username": EMAIL, "password": PASSWORD})
        print('login', r.status_code)
        token = r.json().get('access_token')
        headers = {"Authorization": f"Bearer {token}"}
        # upload pdf
        print('Uploading PDF...')
        files = {'file': open(PDF_PATH, 'rb')}
        r = await client.post(f"{BASE_URL}/pdf-v2/upload", headers=headers, files=files)
        print('upload', r.status_code, r.text[:200])
        sid = r.json().get('session_id')
        print('session', sid)
        # fetch topics from response
        topics = r.json().get('topics', [])
        # select first 2 topics
        selected = [t['title'] for t in topics[:2]] if topics else ['Topic 1']
        print('selecting topics', selected)
        r = await client.patch(f"{BASE_URL}/pdf-v2/sessions/{sid}/select-topics", headers=headers, json=selected)
        print('select topics', r.status_code)
        # generate questions
        payload = {"session_id": sid, "selected_topics": selected, "num_questions_per_topic": 2}
        r = await client.post(f"{BASE_URL}/pdf-v2/sessions/{sid}/generate-questions", headers=headers, json=payload)
        print('generate questions', r.status_code)
        questions = r.json().get('questions', [])
        print('got', len(questions), 'questions')
        # prepare responses: pick correct answer for first half, wrong for others
        responses = []
        for q in questions:
            qnum = q.get('question_number')
            opts = q.get('options', [])
            correct = next((o for o in opts if o.get('type') == 'correct'), opts[0])
            wrong = next((o for o in opts if o.get('type') != 'correct'), opts[0])
            # alternate
            if qnum % 2 == 0:
                sel = wrong.get('text')
                conf = 0.3
                reason = 'I guessed'
            else:
                sel = correct.get('text')
                conf = 0.9
                reason = 'I reasoned through'
            responses.append({
                'question_number': qnum,
                'selected_answer': sel,
                'confidence': conf,
                'reasoning': reason
            })
        # submit quiz
        r = await client.post(f"{BASE_URL}/pdf-v2/sessions/{sid}/submit-quiz", headers=headers, json={'session_id': sid, 'responses': responses})
        print('submit', r.status_code)
        # Print updated_traits if present
        try:
            sr = r.json()
            print('updated_traits in response:', sr.get('updated_traits'))
        except Exception:
            print(r.text[:1000])

        # Fetch updated user profile
        ur = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        print('\nUser profile after submit:')
        print(ur.json())

if __name__ == '__main__':
    asyncio.run(main())
