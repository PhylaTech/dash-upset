"""Generate the docs example datasets embedded across the docs site.

Builds a set of curated UpSet example datasets with Python (the authoritative
data layer), serializes each to its canonical model (set names + totals +
exclusive intersections), and writes them to ``docs/data/examples.js`` as
``window.DASH_UPSET_DATASETS``. The Examples gallery, the Example detail pages,
and the Component Explorer all read this one file; the explorer's client-side
renderer (``docs/assets/upset.js``) does only display math on these models, so
Python stays the source of truth for the data itself.

The docs site is served statically from ``docs/`` (no build at deploy time), so
run this locally and commit its output. Re-run after editing the datasets:

    pixi run python scripts/build_docs_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

from dash_upset import from_counts
from dash_upset.data import UpSetData

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "data" / "examples.js"


def model(data: UpSetData) -> dict:
    return {
        "setNames": list(data.set_names),
        "setSizes": list(data.set_sizes),
        "total": data.total_size,
        "intersections": [
            {"sets": list(entry.sets), "size": entry.size} for entry in data.intersections
        ],
    }


# Each dataset gives the exclusive (distinct) intersection sizes. from_counts
# derives the set totals. Categories mirror the home-page audience split.
DATASETS = [
    {
        "id": "movie-genres",
        "title": "Movie genres",
        "category": "general",
        "featured": True,
        "complexity": 1,
        "tags": ["counts", "3 sets"],
        "summary": "Films tagged with one or more of three genres, and how the "
        "tags overlap. The quick-start example.",
        "counts": {
            "Action": 320,
            "Comedy": 290,
            "Drama": 410,
            "Action&Comedy": 84,
            "Action&Drama": 120,
            "Comedy&Drama": 96,
            "Action&Comedy&Drama": 40,
        },
    },
    {
        "id": "survey-tools",
        "title": "Survey: tools people use",
        "category": "general",
        "featured": True,
        "complexity": 1,
        "tags": ["survey", "multi-select"],
        "summary": "A multi-select survey question -- which data tools respondents "
        "use -- is a natural set-intersection problem.",
        "counts": {
            "Python": 210,
            "R": 90,
            "SQL": 140,
            "Excel": 180,
            "Python&SQL": 160,
            "Python&Excel": 70,
            "SQL&Excel": 95,
            "Python&R": 65,
            "Python&SQL&Excel": 120,
            "Python&R&SQL": 55,
            "Python&R&SQL&Excel": 40,
        },
    },
    {
        "id": "de-genes",
        "title": "Differentially expressed genes",
        "category": "bioinformatics",
        "featured": True,
        "complexity": 2,
        "tags": ["genomics", "4 conditions"],
        "summary": "Genes called differentially expressed across four treatment "
        "conditions -- UpSet's origin use case.",
        "counts": {
            "DrugA": 610,
            "DrugB": 540,
            "Hypoxia": 720,
            "Serum": 480,
            "DrugA&DrugB": 220,
            "DrugA&Hypoxia": 180,
            "DrugB&Hypoxia": 150,
            "Hypoxia&Serum": 260,
            "DrugA&Serum": 90,
            "DrugB&Serum": 110,
            "DrugA&DrugB&Hypoxia": 130,
            "DrugA&Hypoxia&Serum": 75,
            "DrugA&DrugB&Hypoxia&Serum": 60,
        },
    },
    {
        "id": "variant-callers",
        "title": "Variant caller concordance",
        "category": "bioinformatics",
        "featured": False,
        "complexity": 3,
        "tags": ["genomics", "concordance"],
        "summary": "Which variants each caller reports, and where they agree -- "
        "the concordance question every variant pipeline asks.",
        "counts": {
            "GATK": 1200,
            "DeepVariant": 1100,
            "FreeBayes": 1400,
            "Strelka": 980,
            "GATK&DeepVariant": 3200,
            "GATK&FreeBayes": 640,
            "DeepVariant&FreeBayes": 720,
            "GATK&Strelka": 410,
            "DeepVariant&Strelka": 380,
            "FreeBayes&Strelka": 300,
            "GATK&DeepVariant&FreeBayes": 2100,
            "GATK&DeepVariant&Strelka": 1500,
            "GATK&DeepVariant&FreeBayes&Strelka": 8600,
        },
    },
    {
        "id": "model-errors",
        "title": "Model error sets",
        "category": "data-science",
        "featured": True,
        "complexity": 2,
        "tags": ["ml", "error analysis"],
        "summary": "Test examples each model gets wrong. The shared core is the "
        "hard set; the private slivers are model-specific weaknesses.",
        "counts": {
            "ResNet": 140,
            "ViT": 120,
            "XGBoost": 260,
            "ResNet&ViT": 210,
            "ResNet&XGBoost": 70,
            "ViT&XGBoost": 85,
            "ResNet&ViT&XGBoost": 180,
        },
    },
    {
        "id": "feature-cooccurrence",
        "title": "Feature co-occurrence",
        "category": "data-science",
        "featured": False,
        "complexity": 2,
        "tags": ["features", "cohorts"],
        "summary": "Which optional profile fields users fill in together -- "
        "co-occurrence that drives cohorting and imputation.",
        "counts": {
            "Bio": 900,
            "Avatar": 1200,
            "Location": 1500,
            "Website": 300,
            "Bio&Avatar": 800,
            "Avatar&Location": 1100,
            "Bio&Location": 600,
            "Bio&Avatar&Location": 720,
            "Bio&Avatar&Website": 210,
            "Bio&Avatar&Location&Website": 260,
        },
    },
]


def build() -> None:
    out = []
    for spec in DATASETS:
        data = from_counts(spec["counts"])
        out.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "category": spec["category"],
                "featured": spec["featured"],
                "complexity": spec["complexity"],
                "tags": spec["tags"],
                "summary": spec["summary"],
                "nSets": len(data.set_names),
                "nIntersections": len(data.intersections),
                "total": data.total_size,
                "model": model(data),
                "counts": spec["counts"],
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "/* Generated by scripts/build_docs_data.py -- do not edit by hand. */\n"
        "window.DASH_UPSET_DATASETS = " + json.dumps(out, separators=(",", ":")) + ";\n"
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(out)} datasets)")


if __name__ == "__main__":
    build()
