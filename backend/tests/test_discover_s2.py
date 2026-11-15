import os
from pathlib import Path
from app.analysis.scanner import scan


def test_detects_cobol_and_language_percentages(tmp_path):
    (tmp_path/'program.cbl').write_text("       PROGRAM-ID. ACCOUNTING.\n       COPY CUSTOMER.\n       CALL 'CALCULATE'.\n")
    (tmp_path/'main.py').write_text('import os\n# TODO improve\ndef invoice(): pass\n')
    events=[]
    result=scan(tmp_path,events.append)
    assert result['schema_version']==2
    assert {'COBOL','Python'} <= set(result['language_bytes'])
    assert 99.9 <= sum(x['percent'] for x in result['language_breakdown']) <= 100.1
    assert any(s['name']=='ACCOUNTING' for s in result['symbols'])
    assert any(d['target']=='CUSTOMER' for d in result['dependencies'])
    assert any(f['evidence']['file']=='main.py' and f['line']==2 for f in result['findings'])
    assert events[-1]['percent']==100


def test_scanner_does_not_execute_untrusted_code(tmp_path):
    marker=tmp_path/'should_not_exist'
    (tmp_path/'malicious.py').write_text(f"__import__('pathlib').Path('{marker}').touch()")
    scan(tmp_path)
    assert not marker.exists()
