"""JOCKY compiler tests — Compiler integration"""
import pytest
from compiler.compiler import JockyCompiler

VALID_SCRIPT = '''
investigation "Enterprise Sweep" {
    collect system_info
    collect processes
    collect network_connections
    collect persistence
    analyze processes
    analyze network_connections
    filter processes where cpu > 10
    filter network_connections where port in [4444, 1337]
    generate timeline
    generate report
}
'''

INVALID_SCRIPT = '''
investigation "Bad Script" {
    collect unknown_target
}
'''

FILTER_SCRIPT = '''
host "HOST-001" {
    collect processes
    filter processes where cpu > 50
    generate report
}
'''


def test_validate_valid_script():
    compiler = JockyCompiler()
    result = compiler.validate(VALID_SCRIPT)
    assert result['valid'] is True
    assert len(result['errors']) == 0
    assert len(result['steps']) >= 3


def test_validate_invalid_script():
    compiler = JockyCompiler()
    result = compiler.validate(INVALID_SCRIPT)
    assert result['valid'] is False


def test_compile_produces_ir():
    compiler = JockyCompiler()
    result = compiler.compile(VALID_SCRIPT)
    assert result['success'] is True
    assert result['ir'] is not None
    assert result['ir_node_count'] > 0


def test_compile_ir_has_operations():
    compiler = JockyCompiler()
    result = compiler.compile(VALID_SCRIPT)
    ir = result['ir']
    assert 'scopes' in ir
    assert len(ir['scopes']) > 0
    scope = ir['scopes'][0]
    ops = [op['op'] for op in scope['operations']]
    assert 'COLLECT' in ops
    assert 'ANALYZE' in ops
    assert 'FILTER' in ops


def test_build_standard_profile():
    compiler = JockyCompiler()
    result = compiler.build(VALID_SCRIPT, profile='forensic_standard')
    assert result['success'] is True
    assert result['sha256'] is not None
    assert result['profile'] == 'forensic_standard'


def test_build_variant_profile():
    compiler = JockyCompiler()
    result = compiler.build(VALID_SCRIPT, profile='forensic_variant')
    assert result['success'] is True
    assert len(result['transformations']) > 0


def test_two_builds_different_hashes():
    """Core SIH requirement: same source → different build hashes."""
    compiler = JockyCompiler()
    build_a = compiler.build(VALID_SCRIPT, profile='forensic_standard')
    build_b = compiler.build(VALID_SCRIPT, profile='forensic_variant')
    assert build_a['sha256'] != build_b['sha256']


def test_host_block_parsing():
    compiler = JockyCompiler()
    result = compiler.compile(FILTER_SCRIPT)
    assert result['success'] is True
    ir = result['ir']
    scope = ir['scopes'][0]
    assert scope['scope_type'] == 'host'
    assert scope['name'] == 'HOST-001'


def test_compile_time_under_500ms():
    import time
    compiler = JockyCompiler()
    t0 = time.time()
    compiler.build(VALID_SCRIPT, profile='forensic_standard')
    elapsed = (time.time() - t0) * 1000
    assert elapsed < 500, f"Build took {elapsed:.0f}ms > 500ms limit"
