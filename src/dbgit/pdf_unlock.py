"""암호로 보호된 PDF를 열어 암호 없이 저장할 수 있도록 바이트를 변환합니다."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader, PdfWriter


class PdfPasswordError(ValueError):
    """암호가 틀리거나 PDF를 열 수 없을 때."""


def strip_pdf_encryption(pdf_bytes: bytes, password: str) -> bytes:
    """
    사용자가 알고 있는 열람 암호로 PDF를 연 뒤, 동일 내용의 비암호화 PDF 바이트를 반환합니다.

    - DRM 우회·제3자 문서 무단 복호화 용도가 아닌, 본인 소유/권한 문서 처리를 전제로 합니다.
    """
    reader = PdfReader(BytesIO(pdf_bytes), strict=False)

    if reader.is_encrypted:
        pwd = password or ""
        # decrypt returns 0 on failure for user password in many builds; 1/2 success
        ok = reader.decrypt(pwd)
        if ok == 0:
            raise PdfPasswordError("PDF 암호가 올바르지 않거나 이 파일 형식을 지원하지 않습니다.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # 메타데이터 등 복사 (실패해도 본문만으로 충분한 경우가 많음)
    if reader.metadata:
        try:
            writer.add_metadata(reader.metadata)
        except Exception:
            pass

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
