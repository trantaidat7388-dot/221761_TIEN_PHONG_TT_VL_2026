"""File upload/download router facade.

Aggregates conversion and template APIs under a single module name to match
recommended project structure without changing endpoint behavior.
"""

from fastapi import APIRouter

from . import chuyen_doi, templates

router = APIRouter()
router.include_router(chuyen_doi.router)
router.include_router(templates.router)
