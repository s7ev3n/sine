<h1 align="center">
  <img src=".assets/sine.png" alt="sine logo" style="height: 1em;">  Sine
</h1>

<h3 align="center">
    Sine is a personal AI mentor. 
</h3>


## Overview
Sine currently has two agents:

- [ReAct](https://react-lm.github.io/): A general agent has reasoning capability.
- [STORM](https://github.com/stanford-oval/storm): A writer agent which could write wiki style long article.

## Get started

### Environment
We use [rye](https://rye-up.com) as python package manager, install it by `curl -sSf https://rye-up.com/get | bash`, and simply `rye sync` to install the dependencies.

Next, apply large language model apis, rename env file (`mv .env.example .env`), and replace `API_KEY`s in your local `.env` file. Currently support models: `groq`, `glm-4`, and `moonshot` which all provide free api calls.

### Run STORM Agent

STORM agent has a simple streamlit ui, start the ui:
`streamlit run app/storm_streamlit.py` and open the link in the broswer.

## Credits
Thanks to [Lagent](https://github.com/InternLM/lagent).

---
<span style="color: gray">
*Sine is my personal wish to have an AI working for me, more than just a chatbot. It knows me, it understands me, it solves my question, it gives me feedback, it helps me grow, it makes me get better.
</span>