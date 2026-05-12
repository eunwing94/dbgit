"""pdf_unlock 모듈 테스트."""

from __future__ import annotations

from io import BytesIO

import pytest
from pypdf import PdfWriter

from dbgit.pdf_unlock import PdfPasswordError, strip_pdf_encryption


def _make_encrypted_pdf(user_password: str) -> bytes:
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    w.encrypt(user_password=user_password, owner_password=None)
    buf = BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_strip_pdf_encryption_removes_password() -> None:
    raw = _make_encrypted_pdf("secret123")
    unlocked = strip_pdf_encryption(raw, "secret123")

    from pypdf import PdfReader

    r = PdfReader(BytesIO(unlocked))
    assert not r.is_encrypted
    assert len(r.pages) == 1


def test_wrong_password_raises() -> None:
    raw = _make_encrypted_pdf("right")
    with pytest.raises(PdfPasswordError):
        strip_pdf_encryption(raw, "wrong")
