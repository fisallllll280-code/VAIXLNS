import pathlib
import unittest
HTML=(pathlib.Path(__file__).resolve().parents[1]/"web/gov-sand-control-center/index.html").read_text(encoding="utf-8")
class TestGovSandUIContract(unittest.TestCase):
    def test_tabs(self):
        for name in ("control","finance","indexes","sand","proof"):
            self.assertIn('id="'+name+'"',HTML)
            self.assertIn('data-tab="'+name+'"',HTML)
    def test_no_network_or_storage(self):
        for key in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage"):
            self.assertNotIn(key,HTML)
    def test_claims_explicitly_denied(self):
        self.assertIn("0 ر.س",HTML)
        self.assertIn("غير متصل",HTML)
    def test_consent(self):
        self.assertIn('id="consent"',HTML)
        self.assertIn('consent").checked',HTML)

# Execute the actual page script with a minimal DOM to exercise user actions.
import json
import subprocess

NODE_HARNESS = r'''
const fs = require('node:fs');
const vm = require('node:vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const elements = {};
for (const [id, value] of Object.entries({amount:'300000', income:'8500', needs:'4500', debts:'3900', ...input.values})) {
  elements[id] = {value, textContent:'', replaceChildren(...nodes) { this.children = nodes; }, addEventListener(event, fn) { this[event] = fn; }};
}
elements.alloc = {textContent:'', replaceChildren(...nodes) { this.children = nodes; }};
elements.consent = {checked:input.consent};
elements.result = {textContent:''};
elements.calculate = {addEventListener(event, fn) { this[event] = fn; }};
const document = {getElementById: id => elements[id], querySelectorAll: () => [], createElement: () => ({})};
vm.runInNewContext(input.script, {document});
elements.calculate.click();
process.stdout.write(JSON.stringify({result:elements.result.textContent, allocation:elements.alloc.textContent}));
'''

class TestGovSandInputBehavior(unittest.TestCase):
    def run_page(self, values, consent=True):
        script = HTML.split('<script>', 1)[1].split('</script>', 1)[0]
        result = subprocess.run(['node', '-e', NODE_HARNESS], input=json.dumps({'script':script, 'values':values, 'consent':consent}), text=True, capture_output=True, check=True, timeout=5)
        return json.loads(result.stdout)

    def test_blank_and_whitespace_financial_fields_are_rejected(self):
        for field in ('income', 'needs', 'debts'):
            for value in ('', '   '):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.run_page({field:value})['result'], 'قيم غير صالحة')

    def test_blank_funding_amount_is_rejected(self):
        self.assertEqual(self.run_page({'amount':''})['allocation'], 'أدخل مبلغًا صالحًا')

    def test_explicit_zero_is_valid(self):
        self.assertIn('الفائض/العجز الافتراضي:', self.run_page({'income':'0','needs':'0','debts':'0'})['result'])

    def test_negative_nonfinite_and_text_inputs_are_rejected(self):
        for value in ('-1', 'Infinity', 'NaN', 'invalid'):
            with self.subTest(value=value):
                self.assertEqual(self.run_page({'income':value})['result'], 'قيم غير صالحة')

    def test_consent_and_valid_calculation(self):
        self.assertEqual(self.run_page({}, consent=False)['result'], 'لا تحليل دون اختيار طوعي.')
        self.assertIn('الفائض/العجز الافتراضي:', self.run_page({})['result'])

if __name__ == "__main__":
    unittest.main()
