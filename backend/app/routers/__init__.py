"""Khai báo export các module router của API."""

from . import admin_routes, auth_routes, base, chuyen_doi, file_upload, templates

__all__ = [
    "admin_routes",
    "auth_routes",
    "base",
    "chuyen_doi",
    "file_upload",
    "templates",
]
