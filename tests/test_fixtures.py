from pathlib import Path
import yaml
from app.core import analyze_openapi

FIX=Path(__file__).parents[1]/"fixtures"

def test_strong_fixture_scores_higher_than_incomplete():
    weak=analyze_openapi(yaml.safe_load((FIX/"incomplete-api.yaml").read_text()))
    strong=analyze_openapi(yaml.safe_load((FIX/"strong-api.yaml").read_text()))
    assert strong["dx_score"] > weak["dx_score"]
    assert strong["critical_blockers"] <= weak["critical_blockers"]
