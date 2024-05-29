import streamlit as st
import db
import my_openai

st.set_page_config(page_title="Insight Pulse", page_icon="🦊", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #34355d, #34355d);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 设置侧边栏的背景颜色 */
    .stSidebar {
        background-color: #34355d;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 修改主标题的字体颜色 */
    .css-2trqyj {color: #ffffff;}

    /* 修改子标题的字体颜色 */
    .css-1s0hp0k {color: #c0c0c0;}

    /* 如果无法找到正确的类名，请使用更一般的选择器 */
    h1 {color: #ffffff;} /* 修改所有 h1 标签的字体颜色 */
    h2 {color: #ffffff;} /* 修改所有 h2 标签的字体颜色 */
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 设置侧边栏的字体颜色为红色 */
    .stSidebar .css-1d391kg, .stSidebar .css-1d391kg .st-bx {
        color: #ffffff;
    }

    /* 设置主屏幕的字体颜色为黑色 */
    .stApp, .stApp .css-1pxd2l5 {
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)


def select_interview() -> int:
    if 'selected_interview' not in st.session_state or not st.session_state['selected_interview']:
        return 0
    return st.session_state['selected_interview']


def chat_box(interviews: list[db.InterviewData]):
    sentences = []
    for interview in interviews:
        for sentence in interview.sentences:
            sentences.append(sentence.origin_sentence)
    st.sidebar.header("Chat Box")
    result = ''
    q1, q2, q3 = 'What additional interview questions should be asked?', 'What steps should be taken next to improve the product?', 'What are the most important suggestions?'
    if st.sidebar.button(q1, key="chat_button_1"):
        result = my_openai.get_chatbox_resp(sentences, q1)
    if st.sidebar.button(q2, key="chat_button_2"):
        result = my_openai.get_chatbox_resp(sentences, q2)
    if st.sidebar.button(q3, key="chat_button_3"):
        result = my_openai.get_chatbox_resp(sentences, q3)
    q = st.sidebar.text_input("Input your question")
    if st.sidebar.button('Submit'):
        result = my_openai.get_chatbox_resp(sentences, q)
    st.sidebar.write(result)
    return


def display_data_by_interview(interview_id: int):
    interview = db.get_interview_data(interview_id)
    st.header('Interview Detail')

    st.subheader('Interview Info')
    st.write(f"Interview ID: {interview_id} | Duration: {interview.duration} | Start Time: {interview.create_time}")
    st.divider()

    st.subheader('Interview Summary')
    st.write(interview.summary)
    st.divider()

    st.subheader('Sentences')
    for sentence in interview.sentences:
        st.write(f"Sentence ID: {sentence.id} | Role: {sentence.role} | Duration: {sentence.duration} | Start Time: {sentence.create_time.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Original Sentence: {sentence.origin_sentence}")
        st.write(f"Key Words: {sentence.ai_sentence}")
        st.write("")


def display_interview_dimension(interview_id: int):
    if st.sidebar.button("Return", key='goback_project'):
        st.session_state['selected_interview'] = 0
        st.experimental_rerun()
    st.sidebar.title("Interview Selection")
    selected_project_id = st.session_state.get('selected_project', 0)  # 使用get方法，默认为0
    interviews = db.get_all_interview(selected_project_id)
    interview_options = {f"ID {interview.id} - {interview.create_time.strftime('%Y-%m-%d')}": interview.id for interview in interviews}
    default_idx = 0
    for idx, (key, value) in enumerate(interview_options.items()):
        if value == interview_id:
            default_idx = idx
            break
    selected_interview = st.sidebar.radio("Choose a project:", list(interview_options.keys()), index=default_idx, format_func=lambda x: x)

    if interview_options[selected_interview] != interview_id:
        st.session_state['selected_interview'] = interview_options[selected_interview]
        st.experimental_rerun()
    display_data_by_interview(interview_options[selected_interview])


def display_data_by_project(project_id: int, interviews: list[db.InterviewData]):
    labels = {}
    # 聚合标签数据
    for interview in interviews:
        for sentence in interview.sentences:
            if sentence.label not in labels:
                labels[sentence.label] = []
            labels[sentence.label].append(sentence)
    # 展示
    st.subheader('Label Group')
    for label, sentences in labels.items():
        with st.expander(label):
            st.subheader("Label:")
            st.write(label)
            st.divider()
            st.subheader("Label Summary: ")
            # 实时调用openai处理
            st.write(my_openai.get_tag_summary(sentences))
            st.divider()
            st.subheader("Sentences：")
            for sentence in sentences:
                sentence_display = f"{sentence.role}: {sentence.ai_sentence} -- {sentence.create_time.strftime('%Y-%m-%d %H:%M:%S')}"
                st.text(sentence_display)
    st.divider()

    st.subheader("Interview List")
    for interview in interviews:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Interview ID: {interview.id} | Duration: {interview.duration} | Start Time: {interview.create_time.strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            if st.button("Interview Detail", key=interview.id):  # 为每个面试添加详情按钮，注意key的设置避免重复
                st.session_state['selected_interview'] = interview.id
                st.session_state['selected_project'] = project_id
                st.experimental_rerun()


def display_project_dimension():
    st.title("🦊 Insight Pulse")
    st.subheader("Product Introduction")
    st.write(
        "👋 Insightpulse is a software and hardware integrated AI assistant designed for user interviews. The hardware aids user researchers by providing real-time feedback during the interview process, including content summaries, follow-up question suggestions, and time tracking. After the interview, users can quickly access the project and interview records, along with valuable insights, through this website.")
    st.divider()
    st.sidebar.title("Project Selection")
    projects = db.get_all_projects()
    project_options = {}
    # 这里写死了一个project_name列表，务必保证db中有id为0、1、2的三个project，实际应该只有注释掉的代码
    for proj in projects:
        # project_options = {f"ID {proj['project_id']} - {proj['create_time'].strftime('%Y-%m-%d')}": proj['project_id'] for proj in projects}
        if proj['project_id'] == 0:
            project_options['Customer Relationship Management'] = proj['project_id']
        elif proj['project_id'] == 1:
            project_options['Assistance for the disabled'] = proj['project_id']
        elif proj['project_id'] == 2:
            project_options['Educational product iteration'] = proj['project_id']
        else:
            continue
    selected_project_id = st.session_state.get('selected_project', 0)  # 使用get方法，默认为0
    default_idx = 0

    if selected_project_id != 0:
        for idx, (key, value) in enumerate(project_options.items()):
            if value == selected_project_id:  # 直接比较值
                default_idx = idx
                break
    selected_project = st.sidebar.radio("Choose a project:", list(project_options.keys()), index=default_idx, format_func=lambda x: x)  # todo：改project name
    if project_options[selected_project] != selected_project_id:
        st.session_state['selected_project'] = project_options[selected_project]
        st.experimental_rerun()
    project_id = project_options[selected_project]
    interviews = db.get_project_data(project_id)
    chat_box(interviews)
    display_data_by_project(project_id, interviews)


if __name__ == "__main__":
    interview_id = select_interview()
    if interview_id == 0:
        display_project_dimension()
    else:
        display_interview_dimension(interview_id)
