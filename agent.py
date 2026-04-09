# agent.py
from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class EventCandidate(BaseModel):
    title: str
    start_iso: Optional[str] = Field(None, description="ISO 8601 start")
    end_iso: Optional[str] = Field(None, description="ISO 8601 end")
    location: Optional[str] = None
    online_link: Optional[str] = None
    organizer: Optional[str] = None
    source_message_id: str
    confidence: float = 0.0
    reasons: Optional[List[str]] = None

parser = PydanticOutputParser(pydantic_object=EventCandidate)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system",
         "Extract meeting/event details from the email text. "
         "Return only the JSON in the specified schema. "
         "Prefer explicit dates/times; if only date, set start_iso with best guess at 09:00 local, 1hr duration."),
        ("human",
         "Schema:\n{format_instructions}\n\n"
         "Email Subject: {subject}\n\n"
         "Email Body:\n{body}\n\n"
         "Email Metadata:\n{meta}\n"
         "Return ONLY the JSON.")
    ]
).partial(format_instructions=parser.get_format_instructions())

def extract_event(email_subject: str, email_body: str, meta: str, source_message_id: str) -> EventCandidate:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    msg = _PROMPT.format_messages(subject=email_subject, body=email_body, meta=meta)
    raw = llm.invoke(msg)
    candidate = parser.parse(raw.content)
    candidate.source_message_id = source_message_id
    return candidate