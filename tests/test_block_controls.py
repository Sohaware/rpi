"""Regression checks for the shipped Blockly toolbox."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BlockControlsTests(unittest.TestCase):
    def test_blockly_run_explicitly_starts_after_stop(self):
        source = (ROOT / 'components/ide/blocks/index.php').read_text(encoding='utf-8')
        self.assertIn('unix:///run/codynick-script-control.sock', source)
        self.assertIn("control_script('start');", source)
        self.assertLess(source.index('file_put_contents($PYTHON_OUTPUT_FILE'), source.index("control_script('start');"))
        self.assertIn('Python saved and script started.', source)

    def test_blockly_stop_does_not_write_source(self):
        source = (ROOT / 'components/ide/blocks/index.php').read_text(encoding='utf-8')
        handler = source.split("if ($api === 'stop')", 1)[1].split("if ($api === 'run')", 1)[0]
        self.assertIn("control_script('stop');", handler)
        self.assertIn("'POST'", handler)
        self.assertNotIn('file_put_contents', handler)
        self.assertIn('id="blockStopBtn"', source)
        self.assertIn("postJson('?api=stop', {})", source)
        self.assertIn(':not(.stop-btn)', source)

    def test_tools_return_to_main_panel(self):
        for tool in ['code', 'blocks', 'dashboard', 'docs', 'teachers', 'gadget-tests']:
            source = (ROOT / f'components/ide/{tool}/index.php').read_text(encoding='utf-8')
            self.assertIn('href="/"', source, tool)
        source = (ROOT / 'components/simulator/app.js').read_text(encoding='utf-8')
        self.assertIn("mainPanelUrl.port = ''", source)
        launcher = (ROOT / 'components/ide/simulator/index.php').read_text(encoding='utf-8')
        self.assertIn("$_SERVER['HTTP_HOST']", launcher)
        self.assertNotIn("$_SERVER['SERVER_ADDR']", launcher)

    def test_categories(self):
        source = (ROOT / 'components/ide/blocks/index.php').read_text(encoding='utf-8')
        operators = source.split("name: 'Operators'", 1)[1].split("name: 'Control'", 1)[0]
        self.assertNotIn('controls_if', operators)
        for block in ['logic_compare', 'logic_operation', 'logic_negate', 'math_arithmetic']:
            self.assertIn(block, operators)
        control = source.split("name: 'Control'", 1)[1].split("name: 'Text'", 1)[0]
        for block in ['cn_wait', 'cn_forever', 'controls_if', 'controls_whileUntil', 'controls_repeat_ext']:
            self.assertIn(block, control)
        self.assertIn('hasElse: true', control)
        self.assertIn("MODE: 'WHILE'", control)
        self.assertIn("MODE: 'UNTIL'", control)
        self.assertIn('this.setColour(colour)', source)

    def test_main_menu_link(self):
        source = (ROOT / 'components/ide/index.php').read_text(encoding='utf-8')
        self.assertIn('href="/blocks/"', source)
        self.assertIn('Block Coding', source)
