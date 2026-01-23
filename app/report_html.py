from __future__ import annotations
from jinja2 import Environment
from jinja2 import FileSystemLoader
import os

def write_report_html(template_dir: str, template_name: str, out_path: str, context: dict) -> None:
    template_dir = os.path.abspath(template_dir)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True
    )
    template = env.get_template(template_name)
    html = template.render(**context)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
