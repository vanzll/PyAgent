---
name: pdf-extract
description: Inspect parsed PDF text and extracted tables from supporting documents
---

# PDF Extract Skill

Use this skill when PDFs provide supporting context or contain tables worth joining with uploaded data.

After activation:

- Use `list_pdf_documents()` to inspect parsed PDF status.
- Use `get_pdf_text(name)` for extracted text.
- Use `get_pdf_tables(name)` for extracted tables as pandas DataFrames.

If a PDF has `status == 'error'`, treat it as unsupported in this run and continue with the remaining inputs.
