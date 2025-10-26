"""Service layer exports."""

from . import cognitive as cognitive_module
from . import generation as generation_module
from . import pdf as pdf_module
from . import response as response_module
from . import retrieval as retrieval_module
from . import validation as validation_module
from .cognitive import BASELINE_TRAITS, derive_traits, init_profile, update_traits
from .generation import generate_question
from .pdf import process_pdf
from .response import (
    PersistenceError,
    QuestionNotFoundError,
    ResponseServiceError,
    OptionMismatchError,
    process_response,
)
from .retrieval import (
    add_to_chroma,
    flatten_documents,
    retrieve_context,
    retrieve_from_chroma,
)
from .validation import (
    ensure_valid_question,
    get_related_misconceptions,
    parse_question_payload,
)

generation_service = generation_module
retrieval_service = retrieval_module
validation_service = validation_module
cognitive_service = cognitive_module
response_service = response_module
pdf_service = pdf_module
cognitive = cognitive_module
generation = generation_module
retrieval = retrieval_module
validation = validation_module
response = response_module
pdf = pdf_module

__all__ = [
    "BASELINE_TRAITS",
    "derive_traits",
    "init_profile",
    "update_traits",
    "generate_question",
    "process_pdf",
    "PersistenceError",
    "QuestionNotFoundError",
    "ResponseServiceError",
    "OptionMismatchError",
    "process_response",
    "add_to_chroma",
    "flatten_documents",
    "retrieve_context",
    "retrieve_from_chroma",
    "ensure_valid_question",
    "get_related_misconceptions",
    "parse_question_payload",
    "generation_service",
    "retrieval_service",
    "validation_service",
    "cognitive_service",
    "response_service",
    "pdf_service",
    "cognitive",
    "generation",
    "retrieval",
    "validation",
    "response",
    "pdf",
]
