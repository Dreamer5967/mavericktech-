import subprocess
import sys
import tempfile
from pathlib import Path


ROOT=Path(__file__).resolve().parents[2]


def test_policy_runner_preserves_remote_posix_scenario_and_checkpoint_name():
    """The Windows builder must not rewrite a Linux remote path with backslashes."""
    with tempfile.TemporaryDirectory() as directory:
        directory=Path(directory)
        checkpoint=directory/'checkpoint.pt';checkpoint.write_bytes(b'non-secret-test-checkpoint')
        runner=directory/'policy.sh'
        command=[sys.executable,'-B','-m','p2.build_policy_pipeline_runner',
                 '--checkpoint',str(checkpoint),'--scenario','/workspace/aegis/scenarios/demo.sumocfg',
                 '--out',str(runner),'--seconds','30']
        completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True)
        assert 'Prepared read-only policy diagnostics runner' in completed.stdout
        script=runner.read_text(encoding='utf-8')
        assert "'--scenario','/workspace/aegis/scenarios/demo.sumocfg'" in script
        assert "checkpoint=model_dir/('mappo-'" in script
