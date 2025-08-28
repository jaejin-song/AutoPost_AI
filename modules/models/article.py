from dataclasses import dataclass

@dataclass
class Article:
    title: str
    content: str
    url: str
    source: str
    subject: str
