"""Stub dashboard routes — module referenced by main.py but not yet implemented."""
from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def configure(**kwargs):
    """Accept and ignore configuration until dashboard is implemented."""
    pass
