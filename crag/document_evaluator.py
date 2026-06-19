from langchain_anthropic import ChatAnthropic
from utils.prompts import DOCUMENT_EVALUATOR_SYSTEM_PROMPT
from pydantic import BaseModel, Field, field_validator
from configs import IS_SIMULATION
from langchain_core.documents import Document
from uuid import UUID
from utils.message import print_done_string_message, print_inprocess_string_message
import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("anthropic_key_loaded_not_set.")

class Evaluation(BaseModel):
    id:str = Field(
        ..., 
        description="The unique session ID. This MUST be a valid 36-character UUID string (e.g., '123e4567-e89b-12d3-a456-426614174000')."
    )
    score:int
    
    @field_validator('id')
    def check_uuid_format(cls, value: str) -> str:
        try:
            parsed_uuid = UUID(value)
            return str(parsed_uuid)
        except ValueError:
            raise ValueError("The provided ID is not a valid UUID string.")


class EvaluationResponse(BaseModel):
    scores: list[Evaluation]


document_evaluator = ChatAnthropic(
                api_key=ANTHROPIC_API_KEY,
                model="claude-haiku-4-5"
            )

struct_document_evaluator = document_evaluator.with_structured_output(EvaluationResponse, strict=True)

def score_document(documents:list[Document], query: str):
    if IS_SIMULATION:
        return [ Evaluation(id=d.id, score=8) for d in documents]
    
    print_inprocess_string_message("evaluation","Evaluating collected information")
    
    res:EvaluationResponse = struct_document_evaluator.invoke([
    (
        "system",
        DOCUMENT_EVALUATOR_SYSTEM_PROMPT,
    ),
    ("human", f"""given query: {query}
given texts: {"\n".join([f"\n{d.id}\ndocument page_content:{d.page_content}" for d in documents])}
"""),
    ], config={"metadata": {"source": "document_evaluator"}, "callbacks":[]})
    
    print_done_string_message("evaluation","Information evaluated!")
    
    return res.scores