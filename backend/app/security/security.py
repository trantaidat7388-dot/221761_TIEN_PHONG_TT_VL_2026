"""Security facade module.

Keeps authentication and token-related helpers under app/security for
clearer structure, while delegating to the existing implementation.
"""

from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    oauth2_scheme,
    bam_mat_khau,
    lay_nguoi_dung_hien_tai,
    tao_access_token,
    xac_minh_mat_khau,
    yeu_cau_quyen_admin,
)

__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "ALGORITHM",
    "oauth2_scheme",
    "bam_mat_khau",
    "lay_nguoi_dung_hien_tai",
    "tao_access_token",
    "xac_minh_mat_khau",
    "yeu_cau_quyen_admin",
]
