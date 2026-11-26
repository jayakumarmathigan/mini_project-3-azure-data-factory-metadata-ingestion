"""Static checks on the ADF JSON, control file and sample data.

These do not run the pipelines. That needs Azure.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADF = ROOT / "adf"
FOLDERS = {"DatasetReference": "dataset", "PipelineReference": "pipeline",
           "LinkedServiceReference": "linkedService"}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def resources(folder):
    return {p.stem: load(p) for p in (ADF / folder).glob("*.json")}


def walk(node):
    """Yield every dictionary nested inside node."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def test_resource_names_match_file_names():
    files = list(ADF.rglob("*.json"))
    assert files
    for path in files:
        assert load(path)["name"] == path.stem, path


def test_references_exist_and_parameters_match():
    for path in ADF.rglob("*.json"):
        for node in walk(load(path)):
            kind = node.get("type")
            if "referenceName" not in node or kind not in FOLDERS:
                continue
            target = ADF / FOLDERS[kind] / f"{node['referenceName']}.json"
            assert target.exists(), f"{path.name} -> {target.name}"
            if kind == "DatasetReference":
                needed = load(target)["properties"].get("parameters", {})
                assert set(node.get("parameters", {})) == set(needed), path.name


def test_child_pipeline_gets_all_parameters():
    pipelines = resources("pipeline")
    calls = [n for n in walk(pipelines) if n.get("type") == "ExecutePipeline"]
    assert calls
    for call in calls:
        settings = call["typeProperties"]
        child = pipelines[settings["pipeline"]["referenceName"]]["properties"]
        assert set(settings["parameters"]) == set(child["parameters"])


def test_activity_dependencies_exist():
    for name, pipeline in resources("pipeline").items():
        activities = pipeline["properties"]["activities"]
        names = {a["name"] for a in activities}
        for activity in activities:
            for dependency in activity["dependsOn"]:
                assert dependency["activity"] in names, name


def test_control_file_and_sample_data():
    config = load(ROOT / "config" / "ingestion_config.json")
    entities = [item["entity"] for item in config]
    assert len(entities) == len(set(entities))
    for item in config:
        assert set(item) == {"entity", "fileName", "enabled"}
        assert isinstance(item["enabled"], bool)
        if item["enabled"]:
            path = ROOT / "data" / "sample" / item["fileName"]
            with open(path, newline="", encoding="utf-8") as f:
                assert list(csv.DictReader(f)), f"{path.name} has no rows"


def test_trigger_is_stopped():
    for trigger in resources("trigger").values():
        assert trigger["properties"]["runtimeState"] == "Stopped"


def test_linked_services_hold_no_credentials():
    banned = {"accountKey", "sasUri", "sasToken", "connectionString",
              "password", "servicePrincipalKey", "encryptedCredential"}
    for service in resources("linkedService").values():
        for node in walk(service):
            assert not banned & set(node)
