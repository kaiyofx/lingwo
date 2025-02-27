from chromadb import Settings, HttpClient
import streamlit as st
st.set_page_config(page_title='Лингво', layout='wide', page_icon='./favicon.png')
if 'essay_status' not in st.session_state:
    st.session_state['essay_status'] = 'wait'
if 'selected_themes' not in st.session_state or len(st.session_state['selected_themes']) == 0:
    st.session_state['selected_themes'] = 'Духовно-нравственные ориентиры в жизни человека\nСемья, общество, Отечество в жизни человека\nПрирода и культура в жизни человека'


client = HttpClient(host='chroma', port= 8000, settings=Settings(anonymized_telemetry=False))
st.session_state['themes_collection'] = client.get_or_create_collection(name='themes')

st.navigation([
    st.Page(page='nav/essay.py', title='Итоговое сочинение', icon='🎭'),
    st.Page(page='nav/interview.py', title='Устное собеседование', icon='🎧')
]).run()