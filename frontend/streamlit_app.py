import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("API_BASE_URL", "https://hebrekraft-api.onrender.com").rstrip("/")

st.set_page_config(page_title='HebreKraft SaaS Sprint 3.0', layout='wide')
st.title('HebreKraft AI Marketing Operations')
st.caption('Sprint 3.0 SaaS MVP: brand profile, AI generation, scheduling, and LinkedIn OAuth foundation')

if 'token' not in st.session_state:
    st.session_state.token = ''
if 'org_id' not in st.session_state:
    st.session_state.org_id = None


def headers():
    return {'Authorization': f'Bearer {st.session_state.token}'} if st.session_state.token else {}


def api_post(path, payload):
    r = requests.post(f'{API}{path}', json=payload, headers=headers(), timeout=120)
    if r.status_code >= 400:
        st.error(r.text)
        return None
    return r.json()


def api_get(path):
    r = requests.get(f'{API}{path}', headers=headers(), timeout=120)
    if r.status_code >= 400:
        st.error(r.text)
        return None
    return r.json()


def api_put(path, payload):
    r = requests.put(f'{API}{path}', json=payload, headers=headers(), timeout=120)
    if r.status_code >= 400:
        st.error(r.text)
        return None
    return r.json()

with st.sidebar:
    st.header('Account')
    mode = st.radio('Mode', ['Login', 'Register'])
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    if mode == 'Register':
        full_name = st.text_input('Full name')
        organization_name = st.text_input('Organization name', value='HebreKraft')
        if st.button('Create account'):
            data = api_post('/api/auth/register', {'email': email, 'password': password, 'full_name': full_name, 'organization_name': organization_name})
            if data:
                st.session_state.token = data['access_token']
                st.success('Account created')
    else:
        if st.button('Login'):
            data = requests.post(
                f"{API}/api/auth/login",
                data={
                    "username": email,
                    "password": password
                },
                timeout=120
            ).json()

            if data:
                st.session_state.token = data['access_token']
                st.success('Logged in')

if not st.session_state.token:
    st.info('Register or login to continue.')
    st.stop()

orgs = api_get('/api/orgs/mine') or []
if orgs:
    labels = {f"{o['name']} ({o['role']})": o['organization_id'] for o in orgs}
    selected = st.sidebar.selectbox('Workspace', list(labels.keys()))
    st.session_state.org_id = labels[selected]
else:
    st.warning('No workspace found.')
    st.stop()

org_id = st.session_state.org_id

tab_brand, tab_generate, tab_posts, tab_linkedin = st.tabs(['Brand Profile', 'Generate Content', 'Posts & Schedule', 'LinkedIn'])

with tab_brand:
    st.subheader('Brand Profile')
    existing = api_get(f'/api/orgs/{org_id}/brand') or {}
    company_name = st.text_input('Company name', value=existing.get('company_name', 'HebreKraft'))
    industry = st.text_input('Industry', value=existing.get('industry', 'Data & AI Professional Services'))
    target_audience = st.text_area('Target audience', value=existing.get('target_audience', 'SMBs, startups, and enterprises across Africa and the Middle East'))
    services = st.text_area('Services / Products', value=existing.get('services', 'Data strategy, business intelligence, AI automation, Agentic AI workflows, social media automation'))
    brand_voice = st.text_input('Brand voice', value=existing.get('brand_voice', 'professional, executive-friendly, clear, commercially strong'))
    brand_colors = st.text_input('Brand colors', value=existing.get('brand_colors', '#0B1220,#1F6FEB,#FFFFFF'))
    positioning = st.text_area('Positioning statement', value=existing.get('positioning_statement', 'HebreKraft helps organizations move from AI experiments to measurable business outcomes.'))
    focus = st.text_area('Topics to focus, comma-separated', value=', '.join(existing.get('topics_to_focus', ['Data and AI', 'Agentic AI', 'Business Intelligence', 'Automation'])))
    avoid = st.text_area('Topics to avoid, comma-separated', value=', '.join(existing.get('topics_to_avoid', ['fake statistics', 'overpromising', 'generic AI hype'])))
    hashtags = st.text_input('Preferred hashtags, comma-separated', value=', '.join(existing.get('preferred_hashtags', ['#DataAI', '#AgenticAI', '#BusinessIntelligence', '#Automation'])))
    forbidden = st.text_input('Forbidden words, comma-separated', value=', '.join(existing.get('forbidden_words', ['unlock the power'])))
    post_time = st.text_input('Default daily post time HH:MM', value=existing.get('default_post_time', '09:00'))
    timezone = st.text_input('Timezone', value=existing.get('timezone', 'Asia/Dubai'))
    if st.button('Save Brand Profile'):
        payload = {
            'company_name': company_name,
            'industry': industry,
            'target_audience': target_audience,
            'services': services,
            'brand_voice': brand_voice,
            'brand_colors': brand_colors,
            'positioning_statement': positioning,
            'topics_to_focus': [x.strip() for x in focus.split(',') if x.strip()],
            'topics_to_avoid': [x.strip() for x in avoid.split(',') if x.strip()],
            'preferred_hashtags': [x.strip() for x in hashtags.split(',') if x.strip()],
            'forbidden_words': [x.strip() for x in forbidden.split(',') if x.strip()],
            'default_post_time': post_time,
            'timezone': timezone,
        }
        data = api_put(f'/api/orgs/{org_id}/brand', payload)
        if data:
            st.success('Brand profile saved')

with tab_generate:
    st.subheader('Generate LinkedIn Post')
    topic = st.text_input('Post topic', value='From AI pilots to business outcomes')
    extra_focus = st.text_input('Extra focus topics, comma-separated')
    extra_avoid = st.text_input('Extra avoid topics, comma-separated')
    if st.button('Generate with Gemini + ChatGPT'):
        payload = {
            'organization_id': org_id,
            'topic': topic,
            'extra_focus': [x.strip() for x in extra_focus.split(',') if x.strip()],
            'extra_avoid': [x.strip() for x in extra_avoid.split(',') if x.strip()],
        }
        data = api_post('/api/content/generate', payload)
        if data:
            st.success('Post generated and saved')
            st.markdown(f"### {data['title']}")
            st.write(data['content'])
            st.json(data.get('ai_metadata', {}))

with tab_posts:
    st.subheader('Generated Posts')
    posts = api_get(f'/api/content/org/{org_id}/posts') or []
    for p in posts:
        with st.expander(f"#{p['id']} — {p['title']} — {p['status']}"):
            st.write(p['content'])
            st.caption(f"Topic: {p.get('topic')} | Scheduled: {p.get('scheduled_time')}")
            scheduled_time = st.text_input(f'Schedule time for post {p["id"]}', value=p.get('scheduled_time') or '2026-06-12T09:00:00+04:00', key=f'sch_{p["id"]}')
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Schedule', key=f'schedule_{p["id"]}'):
                    res = api_post('/api/content/schedule', {'post_id': p['id'], 'scheduled_time': scheduled_time})
                    if res:
                        st.success('Scheduled')
            with col2:
                if st.button('Publish Now to LinkedIn', key=f'publish_{p["id"]}'):
                    res = api_post(f'/api/linkedin/publish/{p["id"]}', {})
                    if res:
                        st.success('Publish request sent')
                        st.json(res)

with tab_linkedin:
    st.subheader('LinkedIn Connection')
    status = api_get(f'/api/linkedin/org/{org_id}/status') or {}
    st.write(status)
    if st.button('Connect LinkedIn'):
        data = api_get(f'/api/linkedin/connect/{org_id}')
        if data:
            st.link_button('Open LinkedIn Authorization', data['authorization_url'])
            st.info('After authorization, LinkedIn will redirect back to the backend callback URL.')
