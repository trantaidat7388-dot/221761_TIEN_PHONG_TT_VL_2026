import re
import urllib.request
import json
from ..config import SEPAY_API_KEY, NAME_WEB, SECRET_XOR_KEY


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def encode_payment_id(p_id: int) -> str:
    """Mã hóa ID hóa đơn bằng toán tử XOR."""
    return hex(p_id ^ SECRET_XOR_KEY)[2:].upper()

def decode_payment_id(hex_str: str) -> int:
    """Giải mã ID hóa đơn từ chuỗi Hex."""
    try:
        return int(hex_str, 16) ^ SECRET_XOR_KEY
    except ValueError:
        return 0

def get_sepay_transactions():
    """Gọi SePay API lấy danh sách giao dịch gần nhất."""
    if not SEPAY_API_KEY:
        return []
    url = "https://my.sepay.vn/userapi/transactions/list"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {SEPAY_API_KEY}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("transactions", [])
    except Exception:
        return []


def check_payment_status(payment_id: int, expected_amount_vnd: int) -> tuple[bool, str]:
    """Kiểm tra đối soát trạng thái nạp tiền.
    Trả về (True, transaction_id) nếu thành công."""
    target_hex = encode_payment_id(payment_id)
    prefix = re.escape(NAME_WEB) + r"\s*NAPTOKEN"
    pattern = rf"{prefix}([A-Fa-f0-9]+)"

    transactions = get_sepay_transactions()

    for tx in transactions:
        # SePay có thể trả về 'transaction_content' hoặc 'content', tùy version API, ta lấy cả 2
        content = str(tx.get('transaction_content', tx.get('content', '')) or '')
        amount_in = _to_float(tx.get('amount_in', tx.get('amount', 0)))

        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            found_hex = match.group(1).upper()
            if found_hex == target_hex and amount_in >= expected_amount_vnd:
                return True, str(tx.get('id'))

    return False, ""
