import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel
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
                    model="llama3-70b-8192")

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

class AskUser(BaseModel):
    ask: str

def user_answer(state):
    pass


def generate_user_profile_question(state: State):
    gen_user_profile_chain = gen_user_profile | llm
    result = gen_user_profile_chain.invoke(state)
    return {"messages" : [result]}


def router(state: State):
    last_msg = state["messages"][-1]
    if "Thank you so much for your patience" in last_msg.content:
        last_msg.pretty_print()
        return END
    else:
        return "user_answer"


graph = StateGraph(state_schema=State)
graph.add_node("gen_question", generate_user_profile_question)
graph.add_node("user_answer", user_answer)
graph.add_edge(START , "gen_question")
graph.add_conditional_edges("gen_question", router)
graph.add_edge("user_answer", "gen_question")
memory = SqliteSaver.from_conn_string(":memory:")
g = graph.compile(checkpointer=memory, interrupt_before=["user_answer"])
config = {"configurable": {"thread_id": "1"}}
# img = g.get_graph().draw_png()

# events是一个迭代器，只有被取出的时候图才会开始执行，每次图执行到某个节点都需要新的state输入
# next(events)
for event in g.stream({"messages": [("user", user_question)]}, config, stream_mode="values"):
    event["messages"][-1].pretty_print()

user_answer = input("User: ")

g.update_state(config, {"messages": ("user", user_answer)}, as_node="user_answer")
events = g.stream(None, config, stream_mode="values")

for event in events:
    event["messages"][-1].pretty_print()