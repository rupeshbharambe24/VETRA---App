from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel

from .traits import TraitResult, TraitSection


class Report(BaseModel):
    metadata: Dict[str, Any]
    traits: List[TraitResult]


SECTION_ORDER = [
    TraitSection.STRENGTH,
    TraitSection.RUMP,
    TraitSection.FEET_LEG,
    TraitSection.UDDER,
    TraitSection.GENERAL,
]


def group_traits(traits: List[TraitResult]):
    grouped = {sec: [] for sec in SECTION_ORDER}
    for t in traits:
        grouped.setdefault(t.section, []).append(t)
    return grouped


def render_html_report(traits: List[TraitResult], metadata: Dict[str, Any]) -> str:
    grouped = group_traits(traits)
    rows = []
    for section in SECTION_ORDER:
        items = grouped.get(section, [])
        if not items:
            continue
        rows.append(f"<tr><th colspan='4' style='text-align:left;background:#f0f4ff;padding:8px'>{section.value}</th></tr>")
        for t in items:
            measure = "-" if t.measurement_cm is None else f"{t.measurement_cm:.1f} cm"
            rows.append(
                "<tr>"
                f"<td style='padding:6px;border:1px solid #ddd'>{t.name}</td>"
                f"<td style='padding:6px;border:1px solid #ddd;text-align:center'>{t.score}</td>"
                f"<td style='padding:6px;border:1px solid #ddd;text-align:center'>{measure}</td>"
                f"<td style='padding:6px;border:1px solid #ddd'>{t.view or ''}</td>"
                "</tr>"
            )
    meta_html = "".join(
        f"<div><strong>{k.replace('_',' ').title()}:</strong> {v}</div>" for k, v in metadata.items() if v
    )
    table_html = "<table style='width:100%;border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px'>" \
                 "<thead><tr>" \
                 "<th style='padding:6px;border:1px solid #ddd'>Trait</th>" \
                 "<th style='padding:6px;border:1px solid #ddd'>Score (1-9)</th>" \
                 "<th style='padding:6px;border:1px solid #ddd'>Measurement</th>" \
                 "<th style='padding:6px;border:1px solid #ddd'>View</th>" \
                 "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    return (
        "<html><body>"
        "<h2 style='font-family:Arial,sans-serif'>NDDB ATC Report</h2>"
        f"{meta_html}"
        f"{table_html}"
        "</body></html>"
    )
