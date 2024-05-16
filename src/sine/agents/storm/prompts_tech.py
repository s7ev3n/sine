# pre-defined perspective focus
FOCUS_THEORETICAL="""I focus on theoretical aspect of the technology. Given the topic my focus is deep understanding of the foundational theories and principles."""

FOCUS_ARCHITECT="""I focus on architect aspect of the technology. Given the topic my focus is the technical details, including architecture, design patterns, and implementation strategies."""

FOCUS_HISTORICAL="""I focus on historical aspect of the technology. Given the topic my focus is the origin and evolution of the technology or concept."""

FOCUS_PRACTICAL="""I focus on practical aspect of the technology. Given the topic my focus is hands-on code samples and tutorials."""

FOCUS_BEST_PRACTICE="""I focus on best practices of the technology. Given the topic my focus is what is the best practices using this technology in real projects."""

FOCUS_RESEARCH="""I focus on research aspect of the technology. Given the topic my focus is the latest research papers and findings in the field."""

FOCUS_EDU="""I focus on educational aspect of the technology. Given the topic my focus is the educational resources and tutorials available for learning."""

FOCUS_COMPARE="""I focus on comparison aspect of the technology. Given the topic my focus is the comparison with other similar technologies."""

FOCUS_FOUNDAMENTAL="""I focus on foundamental aspect of the technology. Given the topic my goal is to understand what the technology is."""

PREDEFINED_PERSPECTIVES = [FOCUS_FOUNDAMENTAL, FOCUS_THEORETICAL, FOCUS_ARCHITECT, FOCUS_HISTORICAL, FOCUS_PRACTICAL, FOCUS_BEST_PRACTICE, FOCUS_RESEARCH, FOCUS_EDU, FOCUS_COMPARE]

GEN_SEARCH_QUERY_ON_QUESION = """You want to answer the question using Google search. To answer the question, what do you type in the search box?
Write the most important queries you will use in the following format:
- "query 1"
- "query 2"
...
- "query 5"

The question you are going to answer is : {question}"""

ANSWER_QUESTION = """You are an expert who can use information effectively. You are chatting with a tech article writer who wants to write a tech article on topic you know.
You have gathered the related information and will now use the information to form a response.
Make your response as informative as possible and make sure every sentence is supported by the gathered information.
The quesiont you are discussing about: {question}\n
Gathered information:\n{context}
"""
