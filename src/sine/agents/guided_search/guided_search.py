import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from sine.agents.guided_search.prompts import GET_USER_PROFILE
from typing import Annotated, List

from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage
from langgraph.checkpoint.sqlite import SqliteSaver


def init_new_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"), 
                    model="llama3-groq-70b-8192-tool-use-preview")

llm = init_new_llm()
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


user_question = "I want to know how much js basics should master to move on to typescript and nodejs ?"
gen_user_profile = ChatPromptTemplate.from_messages([
    (
        "system",
        GET_USER_PROFILE
    ),
    MessagesPlaceholder(variable_name="messages", optional=True),
])

def generate_user_profile_question(state: State):
    gen_user_profile_chain = gen_user_profile | llm
    result = gen_user_profile_chain.invoke(state)
    print(f"AI: {result.content}")
    return {"message" : [result]}

def human_node(state: State):
    user_input = input("User: ")
    return {"messages" : [HumanMessage(content=user_input)]}

def end_user_profile_cond(state: State):
    last_msg = state["messages"][-1].content
    if "Thank you so much for your patience" in last_msg:
        print(last_msg)
        return END
    else:
        return "gen_question"

graph = StateGraph(state_schema=State)
graph.add_node("gen_question", generate_user_profile_question)
graph.add_node("human_answer", human_node)
graph.add_edge(START , "gen_question")
graph.add_edge("gen_question", "human_answer")
graph.add_conditional_edges("human_answer", end_user_profile_cond)
memory = SqliteSaver.from_conn_string(":memory:")
g = graph.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "1"}}
# img = g.get_graph().draw_png()

init_state = {
    "messages": [
        HumanMessage(
            content=f"{user_question}?",
        )
    ],
}
print(init_state)


for step in g.stream(init_state, config):
    print(step)
    # name = next(iter(step))
    # print(name)
    # print("-- ", str(step[name]["messages"])[:300])
    # if END in step:
    #     final_step = step
        

