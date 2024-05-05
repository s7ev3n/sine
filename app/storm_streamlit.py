import threading
import time

import streamlit as st
import streamlit_shadcn_ui as ui
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import \
    get_script_run_ctx

from sine.agents.storm.storm_agent import STORM, STORMConfig, STORMStatus
from sine.common.logger import LOG_FILE_PATH, logger

st.set_page_config(
     page_title='sine',
     initial_sidebar_state="collapsed",
)

load_dotenv()
class DisplayLogs:
    def __init__(self):
        self.displayed_logs = ''
        self.running = True
        self.log_file = self.open_log()

    def open_log(self):
        try:
            log_file = open(LOG_FILE_PATH)
        except FileNotFoundError:
            print("Log file not found.")
            return None

        return log_file

    def update_log(self):
        try:
            new_log = self.log_file.read()
            if new_log:
                self.displayed_logs += new_log
        except Exception as e:
            print(f"Error reading log file: {e}")
            return None

    def close_log(self):
        self.running = False
        if self.log_file:
            self.log_file.close()

    def run(self):
        while self.running:
            self.update_log()
            time.sleep(0.1)

def log_ui(disp_log, storm_agent):
    with st.expander("LOGGING"):
        placeholder = st.empty()
        while storm_agent.state == STORMStatus.RUNNING:
            log = disp_log.displayed_logs
            if log != '':
                placeholder.code(log)
            time.sleep(0.1)

        disp_log.close_log()

def article_ui(topic_of_interest, article_md_str):
    with st.expander(f"{topic_of_interest}"):
        st.markdown(article_md_str)

def main():
    st.markdown("""
                <div style="text-align: center;">
                    <h3>Sine: AI agent that help you learn about any topic <b>in-depth</b>.</h3>
                </div>
                """, unsafe_allow_html=True)

    topic_of_interest = ''

    with ui.card(key="topic_input"):
        ui.element("span", children=["What is on your mind ?"], className="flex justify-center text-black-400 text-lg font-medium m-3", key="label1")
        ui.element("input", key="topic", type='text', placeholder="Tell me your topic of interest")

    clicked = ui.button("Submit", key="clk_btn", className="text-align-center bg-blue-500 text-white")


    if clicked:
        topic_input_value = st.session_state["topic_input"]
        if topic_input_value is None:
            st.error("Please enter a topic of interest")
        topic_of_interest = topic_input_value


    # run storm agent
    if topic_of_interest != '':
        # init storm agent thread
        cfg = STORMConfig(topic = topic_of_interest)
        storm_agent = STORM(cfg)
        storm_agent.init()
        storm_thread = threading.Thread(target=storm_agent.run_storm_pipeline)

        # init log thread
        disp_log = DisplayLogs()
        log_thread = threading.Thread(target=disp_log.run)
        ctx = get_script_run_ctx()
        add_script_run_ctx(log_thread, ctx)

        # start storm pipeline and logging
        storm_thread.start()
        log_thread.start()

        # display log using a while loop
        log_ui(disp_log, storm_agent)

        # display the final article
        article_ui(topic_of_interest, storm_agent.final_article)

    # display_featured_article()


def display_featured_article():
    col1, col2 = st.columns(2)

    # col1
    col1.markdown("""
    ### How to get over the fears of being judged by others ?
    #### Introduction
    The fear of being judged by others is a common psychological phenomenon that can significantly impact an individual's social interactions and well-being. This fear, often referred to as fear of negative evaluation (FNE) or fear of failure, is defined as "apprehension about others' evaluations, distress over negative evaluations by others, and the expectation that others would evaluate one negatively"[5]. Understanding the underlying mechanisms of this fear and exploring effective strategies to overcome it are essential for enhancing one's social life and self-esteem.
    """)


    col2.markdown("""
    ### How to get over the fears of being judged by others ?
    #### Introduction
    The fear of being judged by others is a common psychological phenomenon that can significantly impact an individual's social interactions and well-being. This fear, often referred to as fear of negative evaluation (FNE) or fear of failure, is defined as "apprehension about others' evaluations, distress over negative evaluations by others, and the expectation that others would evaluate one negatively"[5]. Understanding the underlying mechanisms of this fear and exploring effective strategies to overcome it are essential for enhancing one's social life and self-esteem.
    """)



main()
