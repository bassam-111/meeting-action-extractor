from pathlib import Path

from action_extractor import extract_actions


def test_extract_actions_from_sample_notes():
    sample_notes = Path(__file__).resolve().parents[1] / "sample_notes.txt"
    actions = extract_actions(sample_notes.read_text(encoding="utf-8"))

    assert len(actions) == 6
    assert actions[0] == {
        "task": "Share the updated onboarding checklist with the client success team",
        "owner": "Ayesha",
        "due": "2026-11-06",
        "priority": "Medium",
    }
    assert actions[1]["priority"] == "High"
    assert actions[4]["priority"] == "Low"
    assert actions[5]["owner"] == "Unassigned"
