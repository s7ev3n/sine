FIND_RELATED_TOPIC = """I'm writing a Wikipedia-like content for a topic mentioned below. Please identify and recommend some Wikipedia pages on closely related subjects.
I'm looking for examples that provide insights into interesting aspects commonly associated with this topic, or examples that help me understand the typical content and structure included in Wikipedia pages for similar topics.
Please only list the urls in separate lines.
The topic of interest is {topic}.
"""

GENERATE_WRITERS_PERSPECTIVE = """You need to select a group of Wikipedia editors who will work together to create a comprehensive article on the topic. Each of them represents a different perspective, role, or affiliation related to this topic. You can use other Wikipedia pages of related topics for inspiration. For each editor, add description of what they will focus on.
Give your answer in the following format: 1. short summary of editor 1: description\n2. short summary of editor 2: description\n...

Wiki page outlines of related topics for inspiration: {info}
"""

DEFAULT_WRITER_PERSPECTIVE = """Basic fact writer: Basic fact writer focusing on broadly covering the basic facts about the topic."""


ASK_QUESTION = """You are an experienced Wikipedia writer and want to edit a specific page. Besides your identity as a Wikipedia writer, you have specific focus when researching the topic.
Now, you are chatting with an expert to get information. Ask good questions to get more useful information.
When you have no more question to ask, say "Thank you so much for your help!" to end the conversation.
Please only ask a question at a time and don't ask what you have asked before. Your questions should be related to the topic you want to write.
Topic you are going to write: {topic}
Your persona besides being a Wikipedia writer: {persona}
"""

GEN_SEARCH_QUERY = """You want to answer the question using Google search. What do you type in the search box?
Write the queries you will use in the following format:
- query 1
- query 2
...
- query n

Topic you are discussing about: {topic}
"""

ANSWER_QUESTION = """You are an expert who can use information effectively. You are chatting with a Wikipedia writer who wants to write a Wikipedia page on topic you know.
You have gathered the related information and will now use the information to form a response.
Make your response as informative as possible and make sure every sentence is supported by the gathered information.
Topic you are discussing about: {topic}
Gathered information:\n{info}
"""

WRITE_DRAFT_OUTLINE = """Write an outline for a Wikipedia page.
Here is the format of your writing:
1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
2. Do not include other information.
The topic you want to write: {topic}\n
Write the Wikipedia page outline:\n
"""

REFINE_OUTLINE = """Improve an outline for a Wikipedia page. You already have a draft outline that covers the general information. Now you want to improve it based on the information learned from an information-seeking conversation to make it more informative.
Here is the format of your writing:
1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
2. Do not include other information.
The topic you want to write: {topic}
Conversation history:\n {converation}
Draft outline:\n {draft_outline}
Write the Wikipedia page outline (Use "#" Title" to indicate section title, "##" Title" to indication subsection title, ...):\n
"""

WRITE_SECTION = """Write a Wikipedia section based on the collected information.
Here is the format of your writing:
1. Use "#" Title" to indicate section title, "##" Title" to indicate subsection title, "###" Title" to indicate subsubsection title, and so on.
2. Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
The collected information: {info}
The topic of the page: {topic}
The section you need to write: {section_title}
Write the section with proper inline citations (Start your writing with # section title. Don't include the page tile or try to write other sections):\n
"""
