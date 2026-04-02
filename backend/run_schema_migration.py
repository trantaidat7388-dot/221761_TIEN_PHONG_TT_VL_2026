"""
Run one-off schema migration helpers without starting the API server.
Usage:
  c:/.../.venv/Scripts/python.exe backend/run_schema_migration.py
"""

from backend.app.main import (
    _dam_bao_cot_vai_tro_nguoi_dung,
    _dam_bao_schema_users_premium_token_google,
    _dam_bao_schema_conversion_history_token_fields,
    _dam_bao_schema_token_ledger_indexes,
    _dam_bao_schema_admin_audit_indexes,
    _tao_tai_khoan_admin_mac_dinh,
)


def run() -> None:
    _dam_bao_cot_vai_tro_nguoi_dung()
    _dam_bao_schema_users_premium_token_google()
    _dam_bao_schema_conversion_history_token_fields()
    _dam_bao_schema_token_ledger_indexes()
    _dam_bao_schema_admin_audit_indexes()
    _tao_tai_khoan_admin_mac_dinh()
    print("Schema migration helpers completed successfully.")


if __name__ == "__main__":
    run()
