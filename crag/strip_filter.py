from langchain_openai import ChatOpenAI
from prompts import STRIP_FILTER_BOT_SYSTEM_PROMPT
from pydantic import BaseModel
from uuid import uuid4 as getId

class StripFilterationDetail(BaseModel):
    id:str
    keep:bool

class FilterResponse(BaseModel):
    filters: list[StripFilterationDetail]

stripping_bot = ChatOpenAI(
    model="gpt-5-nano",

)

struct_stripping_bot = stripping_bot.with_structured_output(FilterResponse, strict=True)
    

def filter_strips(strips:list[str], query: str)->list[str]:
    
    strips_dict = {str(getId()):s for s in strips}
    
    res:FilterResponse = struct_stripping_bot.invoke([
    (
        "system",
        STRIP_FILTER_BOT_SYSTEM_PROMPT,
    ),
    ("human", f"""given query: {query}
given texts: {"\n".join([f"\nstrip id:{_id}\nstrip text:{_text}" for _id,_text in strips_dict.items()])}
"""),
    ])
    return [ strips_dict[_s.id] for _s in res.filters if _s.keep]