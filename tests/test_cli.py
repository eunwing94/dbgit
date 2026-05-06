from unittest.mock import MagicMock, patch

from dbgit.cli import main
from dbgit.compare import ProcDefinition


def _fake_defs():
    p = ProcDefinition(
        object_id=9,
        schema_name="dbo",
        name="x",
        definition="x",
        normalized_definition="x",
    )
    return {"PRD": p, "STG": p}


@patch("dbgit.cli.compare_across_envs")
@patch("dbgit.cli.load_env_config")
@patch("dbgit.cli.os.path.exists", return_value=False)
def test_cli_json_output(mock_exists, mock_load_env, mock_compare, capsys):
    mock_load_env.return_value = MagicMock()
    mock_compare.return_value = _fake_defs()

    code = main(["dbo.x", "--envs", "PRD,STG", "--baseline", "PRD", "--output", "json"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"baseline"' in out
