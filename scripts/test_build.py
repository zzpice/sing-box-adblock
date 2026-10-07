import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build

class FilterBuild(unittest.TestCase):
    def test_allowlist_normalizes_and_rejects_rule_injection(self):
        self.assertEqual(build.allowlist('# comment\nEXAMPLE.COM.\nexample.com\n例子.中国'), ['example.com','xn--fsqu00a.xn--fiqs8s'])
        for value in ['example.com/path', '@@||example.com^', 'https://example.com', '*.example.com', 'example.com another.com']:
            with self.assertRaises(ValueError): build.allowlist(value)
    def test_upstream_failure_closes_before_conversion(self):
        for source in ['<html>error</html>', '||example.com^']:
            with self.assertRaises(ValueError): build.prepare(source,'')
        self.assertIn('@@||allowed.example^',build.prepare('||blocked.example^','allowed.example',min_rules=1))
    def test_revision_changes_even_when_compiled_bytes_do_not(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'allowlist.txt').write_text('')
            (root/'adblock.srs').write_bytes(b'SRS-same')
            (root/'upstream-revision.txt').write_text('a'*40+'\n')
            def convert(args, **kwargs): Path(args[args.index('--output')+1]).write_bytes(b'SRS-same')
            with patch('build.subprocess.run',side_effect=convert):
                build.build('sing-box','||example.com^\n'*10000,'b'*40,root)
            self.assertEqual((root/'adblock.srs').read_bytes(),b'SRS-same')
            self.assertEqual((root/'upstream-revision.txt').read_text(),'b'*40+'\n')
    def test_converter_failure_preserves_artifact_and_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'allowlist.txt').write_text('')
            for name in ['adblock.srs','upstream-revision.txt']: (root/name).write_bytes(b'previous')
            with patch('build.subprocess.run',side_effect=build.subprocess.CalledProcessError(1,'sing-box')):
                with self.assertRaises(build.subprocess.CalledProcessError): build.build('sing-box','||example.com^\n'*10000,'b'*40,root)
            for name in ['adblock.srs','upstream-revision.txt']: self.assertEqual((root/name).read_bytes(),b'previous')

if __name__ == '__main__': unittest.main()
