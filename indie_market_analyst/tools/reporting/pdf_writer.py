"""Render HTML (Jinja2) → PDF (WeasyPrint)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from agents import function_tool
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

_TEMPLATES_DIR = (
    Path(__file__).resolve().parents[2] / "skills" / "report_writer" / "templates"
)


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(enabled_extensions=("html", "j2")),
    )


class PdfArtifact(BaseModel):
    path: str
    template: str
    bytes: int


@function_tool(strict_mode=False)
def render_pdf_report(
    template: str, context: dict[str, Any], out_dir: str = "runs",
    filename: str | None = None,
) -> PdfArtifact:
    """Render a Jinja2 template (e.g. ``eod_report.html.j2``) to PDF via WeasyPrint.

    ``context`` must be a plain JSON-serializable dict with the keys the template
    expects (see ``skills/report_writer/templates/eod_report.html.j2``).
    """
    from weasyprint import HTML  # local import — WeasyPrint is heavy

    tpl = _env().get_template(template)
    html = tpl.render(**context)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    name = filename or f"report_{uuid.uuid4().hex[:8]}.pdf"
    path = str(Path(out_dir) / name)
    HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(path)
    return PdfArtifact(path=path, template=template, bytes=Path(path).stat().st_size)


TOOLS = [render_pdf_report]
