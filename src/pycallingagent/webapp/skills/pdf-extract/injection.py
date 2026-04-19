from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def list_pdf_documents():
    docs = _ns().get("pdf_documents", {})
    return {
        name: {
            "status": document.get("status", "unknown"),
            "pages": len(document.get("pages", [])),
            "tables": len(document.get("tables", [])),
        }
        for name, document in docs.items()
    }


def get_pdf_text(name: str):
    return _ns().get("pdf_documents", {}).get(name, {}).get("text", "")


def get_pdf_tables(name: str):
    tables = _ns().get("pdf_documents", {}).get(name, {}).get("tables", [])
    return [table["dataframe"] for table in tables]


__exports__ = [
    Function(list_pdf_documents),
    Function(get_pdf_text),
    Function(get_pdf_tables),
]
