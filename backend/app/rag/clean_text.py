import re
import unicodedata
from langchain_core.documents import Document


def clean_text(documents: list[Document]) -> list[Document]:
    result = []
    for doc in documents:
        new_page_content = clean_rag_text(doc.page_content)
        doc.page_content = new_page_content

        result.append(doc)
    
    return result


def clean_rag_text(text: str) -> str:
    """
    清洗rag文本
    """
    text = text.replace("\x00", "")

    text = unicodedata.normalize(
        "NFKC",
        text
    )

    text = re.sub(
        r"[\x01-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()