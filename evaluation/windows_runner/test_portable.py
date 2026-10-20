from dataclasses import FrozenInstanceError, replace
import pytest

from models import Code, ExecutionFailure, Request, StagedInput
from policy import TEST_LIMITS
import runner


def request():
    return Request('C:\\test\\python.exe', ('worker.py',), 'C:\\test', (),
                   StagedInput(1, 0, '0'*64, 'a', 's'), TEST_LIMITS)


@pytest.mark.parametrize('field', ['input_bytes','stdout_bytes','stderr_bytes','combined_bytes','chunk_bytes',
                                  'wall_ms','cleanup_ms','process_memory','job_memory','processes'])
@pytest.mark.parametrize('value', [0, -1, True, 2**64, 1.5])
def test_invalid_limits(field, value):
    result = runner.run_bounded_worker(replace(request(), limits=replace(TEST_LIMITS, **{field:value})))
    assert isinstance(result, ExecutionFailure)
    assert result.issues[0].code == Code.INVALID
    assert result.evidence.root_pid is None


def test_capability_does_not_launch(monkeypatch):
    monkeypatch.setattr(runner, 'supported', lambda: False)
    result = runner.run_bounded_worker(request())
    assert result.issues[0].code == Code.CAPABILITY
    assert not hasattr(result, 'stdout')
    assert result.diagnostic_prefixes_usable is False
    with pytest.raises(FrozenInstanceError):
        result.evidence = None


@pytest.mark.parametrize('change', [dict(executable='python'),dict(argv=['bad']),
    dict(environment=(('A','a'),('a','b'))),dict(environment=(('A=B','x'),)),dict(cwd='relative')])
def test_invalid_request(change):
    assert not runner.validate(replace(request(), **change))


def test_policy_valid():
    assert runner.validate(request())
