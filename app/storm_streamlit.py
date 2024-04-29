import threading
import time

import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit.runtime.scriptrunner import (add_script_run_ctx,
                                            get_script_run_ctx)

from sine.agents.storm.storm_agent import STORM, STORMConfig
from sine.common.logger import LOG_FILE_PATH, logger

st.set_page_config(
     page_title='sine',
     initial_sidebar_state="collapsed",
)

class DisplayLogs:
    def __init__(self):
        self.displayed_logs = None
        self.running = True
        self.log_file = self.open_log()

    def open_log(self):
        try:
            self.log_file = open(LOG_FILE_PATH)
        except FileNotFoundError:
            print("Log file not found.")

        return self.log_file

    def close_log(self):
        self.running = False
        self.log_file.close()

    def update_log(self):
        tmp_log = self.log_file.read()
        if self.displayed_logs != tmp_log:
            self.displayed_logs = tmp_log

    def run(self):
        while self.running:
            self.update_log()
            time.sleep(0.1)


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
        st.write('topic_input_value', topic_input_value)
        if topic_input_value is None:
            st.error("Please enter a topic of interest")
        topic_of_interest = topic_input_value


    # run storm agent
    if topic_of_interest != '':
        topic = topic_of_interest.lower().strip().replace(' ', '_')

        # init storm agent thread
        cfg = STORMConfig(topic = topic_of_interest)
        storm_agent = STORM(cfg)
        storm_agent.init()
        storm_thread = threading.Thread(target=storm_agent.run_storm_pipeline)

        # init log thread
        disp_log = DisplayLogs()
        log_thread = threading.Thread(target=disp_log.run)

        storm_thread.start()
        log_thread.start()

        with st.expander("INFO"):
            if disp_log.displayed_logs is not None:
                st.write(disp_log.displayed_logs)



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
