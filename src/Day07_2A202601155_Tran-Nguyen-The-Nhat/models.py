"""Dữ liệu đầu vào chuẩn cho bài Lab 07 cá nhân."""

from dataclasses import dataclass, field


@dataclass
class Document:
    """Một văn bản cùng metadata dùng cho retrieval."""

    id: str
    content: str
    metadata: dict = field(default_factory=dict)
