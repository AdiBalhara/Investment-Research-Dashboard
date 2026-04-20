import sys
sys.path.append('/app')

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain import agents
from app.research.tools.stock_data import get_stock_data
from app.research.tools.news_search import search_news
from app.research.tools.vector_search import search_financial_documents
from app.config import get_settings

settings = get_settings()
llm = ChatGroq(model='llama-3.1-8b-instant', api_key=settings.GROQ_API_KEY, temperature=0.0, max_tokens=800)

prompt = ChatPromptTemplate.from_messages([
    ('system', 'You are a financial research assistant. Use tools to gather factual data before answering.'),
    ('human', 'TOOLS\n------\n{tools}\n\nRESPONSE FORMAT INSTRUCTIONS\n----------------------------\nIf you need to call a tool, respond with a JSON code snippet formatted as:\n```\n{{\n  "action": string,\n  "action_input": string\n}}\n```\nIf you are done, respond with a JSON code snippet formatted as:\n```\n{{\n  "action": "Final Answer",\n  "action_input": {{\n    "query": string,\n    "confidence": number,\n    "sections": [ ... ],\n    "reasoning": string\n  }}\n}}\n```\nOnly respond with the JSON snippet and nothing else.\n\nUSER\'S INPUT\n--------------------\n{input}\n\nTOOLS AVAILABLE: {tool_names}'),
    MessagesPlaceholder(variable_name='agent_scratchpad'),
])

print('Prompt input vars:', prompt.input_variables)

tools = [get_stock_data, search_news, search_financial_documents]
agent = agents.create_json_chat_agent(llm, tools, prompt)
executor = agents.AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5, return_intermediate_steps=True, handle_parsing_errors=True)
res = executor.invoke({'input': 'Summarize Apple stock and recent news.'})
print('result type', type(res))
print('keys', list(res.keys()))
print('output type', type(res.get('output')))
print('output repr', repr(res.get('output'))[:1000])
print('intermediate steps count', len(res.get('intermediate_steps')))
print('intermediate steps', res.get('intermediate_steps'))
