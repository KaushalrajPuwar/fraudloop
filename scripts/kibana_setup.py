"""Provision the Kibana index pattern and FraudLoop dashboard.

Kibana has no declarative config file, so the dashboard is created through
its saved-objects API. Safe to re-run: every object is written with
overwrite=true.

    python scripts/kibana_setup.py --url http://localhost:5601
"""

from __future__ import annotations

import argparse
import json
import time

import httpx

INDEX_PATTERN_ID = "fl-logs"
DASHBOARD_ID = "fl-dashboard"
VERSION = "8.15.3"


def _layer(columns: dict, column_order: list[str]) -> dict:
    return {
        "formBased": {
            "layers": {
                "layer1": {
                    "columns": columns,
                    "columnOrder": column_order,
                    "incompleteColumns": {},
                }
            }
        }
    }


def _count_column() -> dict:
    return {
        "label": "Count",
        "dataType": "number",
        "operationType": "count",
        "sourceField": "___records___",
        "isBucketed": False,
        "params": {"format": {"id": "number"}},
    }


def _date_column() -> dict:
    return {
        "label": "Time",
        "dataType": "date",
        "operationType": "date_histogram",
        "sourceField": "ts",
        "isBucketed": True,
        "params": {"interval": "auto", "includeEmptyRows": True},
    }


def _terms_column(field: str, label: str) -> dict:
    return {
        "label": label,
        "dataType": "string",
        "operationType": "terms",
        "sourceField": field,
        "isBucketed": True,
        "params": {
            "size": 6,
            "orderBy": {"type": "column", "columnId": "count"},
            "orderDirection": "desc",
            "otherBucket": False,
            "missingBucket": False,
        },
    }


def _average_column(field: str, label: str) -> dict:
    return {
        "label": label,
        "dataType": "number",
        "operationType": "average",
        "sourceField": field,
        "isBucketed": False,
        "params": {"format": {"id": "number", "params": {"decimals": 2}}},
    }


def _lens(panel_id: str, title: str, columns: dict, order: list[str], series: dict) -> dict:
    return {
        "type": "lens",
        "id": panel_id,
        "attributes": {
            "title": title,
            "visualizationType": "lnsXY",
            "state": {
                "visualization": {
                    "legend": {"isVisible": True, "position": "right"},
                    "valueLabels": "hide",
                    "fittingFunction": "linear",
                    "axisTitlesVisibilitySettings": {
                        "x": False, "yLeft": True, "yRight": True
                    },
                    "tickLabelsVisibilitySettings": {
                        "x": True, "yLeft": True, "yRight": True
                    },
                    "gridlinesVisibilitySettings": {
                        "x": True, "yLeft": True, "yRight": True
                    },
                    "layers": [series],
                    "preferredSeriesType": series["seriesType"],
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": _layer(columns, order),
                "internalReferences": [],
                "adHocDataViews": {},
            },
        },
        # References live on the saved-object envelope, not inside attributes:
        # the lens mapping is strict and rejects an attributes.references key.
        "references": [
            {
                "name": "indexpattern-datasource-layer-layer1",
                "type": "index-pattern",
                "id": INDEX_PATTERN_ID,
            }
        ],
    }


def build_objects() -> list[dict]:
    """The index pattern, three Lens panels, and the dashboard that holds them."""
    index_pattern = {
        "type": "index-pattern",
        "id": INDEX_PATTERN_ID,
        "attributes": {
            "title": "fraudloop-*",
            "timeFieldName": "ts",
            "fields": "[]",
        },
    }

    traffic = _lens(
        "fl-traffic",
        "Scored transactions over time",
        {
            "date": _date_column(),
            "count": _count_column(),
            "decision": _terms_column("decision", "Decision"),
        },
        ["date", "count", "decision"],
        {
            "layerId": "layer1",
            "layerType": "data",
            "seriesType": "bar_stacked",
            "xAccessor": "date",
            "splitAccessor": "decision",
            "accessors": ["count"],
            "showGridlines": False,
        },
    )

    decisions = _lens(
        "fl-decisions",
        "Decision split",
        {
            "count": _count_column(),
            "decision": _terms_column("decision", "Decision"),
        },
        ["count", "decision"],
        {
            "layerId": "layer1",
            "layerType": "data",
            "seriesType": "bar_horizontal",
            "xAccessor": "decision",
            "accessors": ["count"],
            "showGridlines": False,
        },
    )

    latency = _lens(
        "fl-latency",
        "Mean scoring latency",
        {
            "date": _date_column(),
            "latency": _average_column("latency_ms", "Latency (ms)"),
        },
        ["date", "latency"],
        {
            "layerId": "layer1",
            "layerType": "data",
            "seriesType": "line",
            "xAccessor": "date",
            "accessors": ["latency"],
            "showGridlines": False,
        },
    )

    panels = [
        {"panel": traffic, "x": 0, "y": 0, "w": 32, "h": 15, "index": "p1"},
        {"panel": decisions, "x": 32, "y": 0, "w": 16, "h": 15, "index": "p2"},
        {"panel": latency, "x": 0, "y": 15, "w": 48, "h": 15, "index": "p3"},
    ]

    panels_json = json.dumps(
        [
            {
                "version": VERSION,
                "type": "lens",
                "gridData": {"x": p["x"], "y": p["y"], "w": p["w"], "h": p["h"], "i": p["index"]},
                "panelIndex": p["index"],
                "embeddableConfig": {"enhancements": {}},
                "panelRefName": f"panel_{p['index']}",
            }
            for p in panels
        ]
    )

    dashboard = {
        "type": "dashboard",
        "id": DASHBOARD_ID,
        "attributes": {
            "title": "FraudLoop",
            "description": "Live fraud scoring activity: traffic, decisions, and latency.",
            "panelsJSON": panels_json,
            "optionsJSON": json.dumps(
                {
                    "useMargins": True,
                    "syncColors": False,
                    "syncCursor": True,
                    "syncTooltips": False,
                    "hidePanelTitles": False,
                }
            ),
            "version": 1,
            "timeRestore": True,
            "timeFrom": "now-24h",
            "timeTo": "now",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps(
                    {"query": {"query": "", "language": "kuery"}, "filter": []}
                )
            },
        },
        "references": [
            {"name": f"panel_{p['index']}", "type": "lens", "id": p["panel"]["id"]}
            for p in panels
        ],
    }

    return [index_pattern, traffic, decisions, latency, dashboard]


def wait_for_kibana(base_url: str, timeout: int = 180) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/api/status", timeout=5.0)
            if response.status_code == 200 and response.json().get("status", {}).get("overall", {}).get("level") == "available":
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    raise SystemExit(f"Kibana did not become available at {base_url} within {timeout}s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision Kibana objects.")
    parser.add_argument("--url", default="http://localhost:5601")
    parser.add_argument("--no-wait", action="store_true")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    if not args.no_wait:
        wait_for_kibana(base)

    failures = 0
    for obj in build_objects():
        url = f"{base}/api/saved_objects/{obj['type']}/{obj['id']}?overwrite=true"
        try:
            response = httpx.post(url, json={"attributes": obj["attributes"],
                                             "references": obj.get("references", [])},
                                  headers={"kbn-xsrf": "true"}, timeout=30.0)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {obj['type']}/{obj['id']}: {exc}")
            failures += 1
            continue

        if response.status_code in (200, 201):
            print(f"  ok    {obj['type']}/{obj['id']}")
        else:
            print(f"  FAIL  {obj['type']}/{obj['id']}: {response.status_code} {response.text[:200]}")
            failures += 1

    if failures:
        print(f"\n{failures} object(s) failed")
        return 1

    print(f"\ndashboard ready: {base}/app/dashboards#/view/{DASHBOARD_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
