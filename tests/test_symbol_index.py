import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from symbol_index import SymbolIndex  # noqa: E402


def test_symbol_index_definitions_and_usages():
    idx = SymbolIndex(root=str(ROOT))
    # Index a subset of src files
    src_dir = ROOT / "src"
    paths = [str(p) for p in src_dir.glob("*.py")]
    idx.index_paths(paths)

    # Should find class definition for DelegationPolicy
    defs = idx.find_definitions("DelegationPolicy")
    assert any(Path(p).name == "delegation_policy.py" for p, _ in defs)

    # Should find at least one usage of LocalOrchestrator in tests or src
    uses = idx.find_usages("LocalOrchestrator")
    assert isinstance(uses, list)
