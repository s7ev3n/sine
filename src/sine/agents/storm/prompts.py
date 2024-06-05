GEN_WIKI_URL = """You are writing learning content for a topic mentioned below. Please identify and recommend some Wikipedia pages on closely related subjects.
I'm looking for examples that provide insights into interesting aspects commonly associated with this topic, or examples that help me understand the typical content and structure included in Wikipedia pages for similar topics.
Please only list the urls in separate lines.
The topic of interest is {topic}.
"""

GEN_WRITERS_PERSPECTIVE = """You need to select a group of experts who will work together to prepare content on the topic for targeted audience. The topic is '{topic}'. \n
Your choice of experts should reflect and focus on the reader's preference, but also be the self-contained on the content. The reader's perference is '{preference}'. \n
Each of them represents a different perspective and role related to this topic. For each expert, add description of what they will focus on.
Give your answer in the following format: 1. short summary of editor 1: description\n2. short summary of editor 2: description\n...
"""

DEFAULT_WRITER_PERSPECTIVE = """Basic fact writer: Basic fact writer focusing on broadly covering the basic facts about the topic."""


ASK_QUESTION = """You are very experienced at writing learning material and want to write for reader. Besides your identity as a writer, you have specific focus when researching the topic.
Now, you are chatting with an expert to get information. Ask good questions to get more useful information.
When you have no more question to ask, say "Thank you so much for your help!" to end the conversation.
Please only ask a question at a time and don't ask what you have asked before. Your questions should be related to the topic you want to write.
Topic you are going to write: {topic}
Your persona besides being an content writer: {persona}
"""

GEN_SEARCH_QUERY = """You want to answer the question using Google search. What do you type in the search box?
Write the queries you will use in the following format:
- "query 1"
- "query 2"
...
- "query n"

The question you are going to answer is : {context}
"""

ANSWER_QUESTION = """You are an expert who can use information effectively. You are chatting with a writer who wants to write on topic you know.
You have gathered the related information and will now use the information to form a response.
Make your response as informative as possible and make sure every sentence is supported by the gathered information.
The question you are discussing about: {question}\n
Gathered information:\n{info}
"""

WRITE_DRAFT_OUTLINE = """Write an outline for learning material, the outline should focus on reader's preference.
The topic you want to write: '{topic}' \n
And most importantly the reader's preference: '{preference}' \n

Here is the format of your writing:
1. Use "# title_name" to indicate page title, "##" title_name" to indicate section title, "###" title_name" to indicate subsection title, "####" title_name" to indicate subsubsection title, and so on.
2. Do not include other information.

Write the outline:\n
"""

REFINE_OUTLINE = """Improve an outline for learning material based on draft outline and information-seeking conversation,
but keep in mind that the goal of the outline is for reader's deep dive into this topic, therefore the outline should focus on the reader's preference.
The reader's preference is '{preference}'.

The topic is '{topic}'. And below are draft outline and information-seeking conversation for you to improve the outline,
use the information wisely and learn from them to make the outline more informative.

The draft outline:\n {draft_outline}

The information-seeking conversation:\n {conversation}

At last is the format of your writing:
1. Use "# title_name" to indicate page title, "##" title_name" to indicate section title, "###" title_name" to indicate subsection title, "####" title_name" to indicate subsubsection title, and so on.
2. Do not include other information.

Now improve the outline:\n
"""

WRITE_SECTION = """Write a section of learning material based on the collected information.
Here is the format of your writing:
1. Use "##" Title" to indicate section title, "###" Title" to indicate subsection title, "####" Title" to indicate subsubsection title, and so on.
2. Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
3. DO NOT put inline citation at the front of the sentence
4. DO NOT write conclusion or introduction

The topic of the learning material is "{topic}", and the section you are going to write is "{section_title}".
Use below collected information to write the section: \n{info}

Write the section with proper inline citations (Start your writing with ## section title. Don't include the page title or try to write other sections):\n
"""

WRITE_SUBSECTION = """Write a subsection content consistent with previous content and grounded on the collected information.
The topic of the learning material you are writing is "{topic}", and the subsection you are going to write is "{section_title}".
If provided in the quotation mark, that is previous content before this subsection, you should keep consistent with it, if not provided just write. '\n{prev_content}'

And the collected information below is the source you should use to write the subsection: \n{info}

Besides, follow below guideline when writing:
1. Use [1], [2], ..., [n] in line (for example, "The capital of the United States is Washington, D.C.[1][3]."). You DO NOT need to include a References or Sources section to list the sources at the end.
2. DO NOT put inline citation at the front of the sentence
3. DO NOT try to make conclusion or summary to end your writing
4. DO NOT use hashtags, e.g. ##, ###, etc, ONLY write the content
5. DO NOT repeat the subsection title at the first line of your writing

Now, write the subsection:\n
"""

# lead section is In Wikipedia, the lead section is an introduction to an  and a summary of its most important contents.
# It is located at the beginning of the article, before the table of contents and the first heading
WRITE_LEAD_SECTION = """Write a lead section for the learning material with the following guidelines:
1. The lead should stand on its own as a concise overview of the learning material's topic. It should identify the topic, establish context, explain why the topic is notable, and summarize the most important points, including any prominent controversies.
2. The lead section should be concise and contain no more than four well-composed paragraphs.
3. The lead section should be carefully sourced as appropriate. Add inline citations (e.g., "Washington, D.C., is the capital of the United States.[1][3].") where necessary.
The topic of the page:\n {topic}
The draft page:\n {draft_page}
Now, write the lead section:\n
"""

POLISH_PAGE = """You are a faithful text editor that is good at finding repeated information in the learning material and deleting them to make sure there is no repetition in the article. You won't delete any non-repeated part in the article. You will keep the inline citations and article structure (indicated by "#", "##", etc.) appropriately. Do your job for the following article.
The draft learning material:\n {draft_article}
Now, revise the draft learning material: \n
"""

WRITER_STYLE_TECH = """You are a great writer especailly excellent at tech article with the following style:
1. You keep things simple, clarity, no extra words
2. You write short sentences for clear understanding for readers
3. You are very good at writing first sentences which will immediately grab the reader
4. You writing is pleasant to read and easy to understand
5. You writing is NOT dry and lifeless
KEEP above STYLES when you write article !
"""

GATHER_PREFERENCE="""You are an writer/teacher and is preparing writing learning material on a topic given by reader.
You are going to have conversations with the reader, use your words to figure out the topic and most importantly what content is
best for the reader. To write the best content, you should know your reader very well, for example, you need to know how the reader's
related prior knowledge in order to fully understand this topic, the reader's preference/objective of learning a topic, e.g. focusing
on practical coding in projects or learning theory or get an overview. You could ask more questions beyond the examples, but no
more than 10 questions. Remember you goal is to understand your reader very well to write content for the reader.

You can NOT throw many questions to reader all at once, gather the information ONE by ONE.

If you think you have found out the answers of the topic and the reader's preference, say "Thanks !" to end the conversation.
AND output a json object following below format:
```json
{
    'topic': the topic reader would like to learn,
    'preference': summary all the information you know about the reader in a sentence, the more detail the better
}
```
"""

# pre-defined tech perspective focus
FOCUS_THEORETICAL_TECH="""I focus on theoretical aspect of the technology. Given the topic my focus is deep understanding of the foundational theories and principles."""

FOCUS_ARCHITECT_TECH="""I focus on architect aspect of the technology. Given the topic my focus is the technical details, including architecture, design patterns, and implementation strategies."""

FOCUS_HISTORICAL_TECH="""I focus on historical aspect of the technology. Given the topic my focus is the origin and evolution of the technology or concept."""

FOCUS_PRACTICAL_TECH="""I focus on practical aspect of the technology. Given the topic my focus is hands-on code samples and tutorials."""

FOCUS_BEST_PRACTICE_TECH="""I focus on best practices of the technology. Given the topic my focus is what is the best practices using this technology in real projects."""

FOCUS_RESEARCH_TECH="""I focus on research aspect of the technology. Given the topic my focus is the latest research papers and findings in the field."""

FOCUS_EDU_TECH="""I focus on educational aspect of the technology. Given the topic my focus is the educational resources and tutorials available for learning."""

FOCUS_COMPARE_TECH="""I focus on comparison aspect of the technology. Given the topic my focus is the comparison with other similar technologies."""

FOCUS_FOUNDAMENTAL_TECH="""I focus on foundamental aspect of the technology. Given the topic my goal is to understand what the technology is."""

PREDEFINED_PERSPECTIVES_TECH = [FOCUS_FOUNDAMENTAL_TECH, FOCUS_THEORETICAL_TECH, FOCUS_ARCHITECT_TECH, FOCUS_HISTORICAL_TECH, FOCUS_PRACTICAL_TECH, FOCUS_BEST_PRACTICE_TECH, FOCUS_RESEARCH_TECH, FOCUS_EDU_TECH, FOCUS_COMPARE_TECH]
