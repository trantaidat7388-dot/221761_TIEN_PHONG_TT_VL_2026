import math
import re
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..config import TOKEN_MIN_COST, TOKEN_WORDS_PER_PAGE, TOKEN_WORDS_PER_UNIT


def tinh_token_tieu_hao_theo_so_trang(so_trang: int) -> int:
    if so_trang <= 0:
        so_trang = 1
    words_estimate = so_trang * TOKEN_WORDS_PER_PAGE
    token_cost = math.ceil(words_estimate / TOKEN_WORDS_PER_UNIT)
    return max(TOKEN_MIN_COST, token_cost)


def uoc_tinh_so_trang_tu_noi_dung_word(contents: bytes) -> int:
    try:
        with ZipFile(BytesIO(contents), "r") as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    except (BadZipFile, KeyError, ValueError):
        return 1

    text_nodes = re.findall(r"<w:t[^>]*>(.*?)</w:t>", doc_xml, flags=re.IGNORECASE | re.DOTALL)
    raw_text = " ".join(text_nodes)
    words = re.findall(r"[\w\-]+", raw_text, flags=re.UNICODE)
    if not words:
        return 1

    return max(1, math.ceil(len(words) / TOKEN_WORDS_PER_PAGE))


def ghi_ledger_token(
    db: Session,
    user_id: int,
    delta_token: int,
    balance_after: int,
    reason: str,
    job_id: str | None = None,
    meta_json: str | None = None,
) -> models.TokenLedger:
    entry = models.TokenLedger(
        user_id=user_id,
        delta_token=delta_token,
        balance_after=balance_after,
        reason=reason,
        job_id=job_id,
        meta_json=meta_json,
    )
    db.add(entry)
    return entry


def tru_token_cho_chuyen_doi(db: Session, user_id: int, so_trang_uoc_tinh: int, job_id: str) -> dict:
    token_cost = tinh_token_tieu_hao_theo_so_trang(so_trang_uoc_tinh)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Không tìm thấy người dùng")

    if user.token_balance < token_cost:
        raise HTTPException(
            status_code=402,
            detail=f"Không đủ token để chuyển đổi. Cần {token_cost} token, còn {user.token_balance} token",
        )

    user.token_balance -= token_cost
    ghi_ledger_token(
        db=db,
        user_id=user.id,
        delta_token=-token_cost,
        balance_after=user.token_balance,
        reason="convert_deduct",
        job_id=job_id,
        meta_json=f'{{"pages_count": {so_trang_uoc_tinh}}}',
    )
    db.commit()

    return {
        "pages_count": so_trang_uoc_tinh,
        "token_cost": token_cost,
        "balance_after": user.token_balance,
    }


def hoan_token_chuyen_doi(db: Session, user_id: int, token_cost: int, job_id: str, pages_count: int = 0) -> dict:
    if token_cost <= 0:
        return {"balance_after": None}

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return {"balance_after": None}

    user.token_balance += token_cost
    ghi_ledger_token(
        db=db,
        user_id=user.id,
        delta_token=token_cost,
        balance_after=user.token_balance,
        reason="refund",
        job_id=job_id,
        meta_json=f'{{"pages_count": {pages_count}}}',
    )
    db.commit()

    return {"balance_after": user.token_balance}
