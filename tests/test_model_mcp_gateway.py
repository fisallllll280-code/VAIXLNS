"""Contract tests for the isolated model gateway."""
import json, os, unittest
from unittest.mock import MagicMock, patch
from tools.model_mcp.server import GatewayError, _configuration, invoke_model, list_model_providers

class ModelGatewayTests(unittest.TestCase):
 def test_inventory_never_returns_secret(self):
  with patch.dict(os.environ,{"OPENAI_API_KEY":"do-not-return","VAIXLNS_MODEL_OPENAI":"test-model"},clear=True):
   result=list_model_providers()
  self.assertTrue(result["providers"][0]["configured"])
  self.assertNotIn("do-not-return",json.dumps(result))
  self.assertFalse(result["providers"][0]["live_connectivity_verified"])
 def test_missing_key_fails_closed(self):
  with patch.dict(os.environ,{"VAIXLNS_MODEL_OPENAI":"test-model"},clear=True):
   with self.assertRaisesRegex(GatewayError,"OPENAI_API_KEY"): _configuration("openai")
 def test_unknown_provider_fails_closed(self):
  with self.assertRaisesRegex(GatewayError,"Unsupported provider"): _configuration("nope")
 def test_prompt_limit_before_network(self):
  with patch("tools.model_mcp.server.urllib.request.build_opener") as opener:
   with self.assertRaisesRegex(GatewayError,"40000-character"): invoke_model("openai","x"*40001)
   opener.assert_not_called()
 def test_mocked_openai_response(self):
  response=MagicMock(); response.__enter__.return_value.read.return_value=json.dumps({"choices":[{"message":{"content":"mocked answer"}}]}).encode()
  with patch.dict(os.environ,{"OPENAI_API_KEY":"test-secret","VAIXLNS_MODEL_OPENAI":"test-model"},clear=True), patch("tools.model_mcp.server.urllib.request.build_opener") as opener:
   opener.return_value.open.return_value=response
   result=invoke_model("openai","test prompt")
  self.assertEqual(result["text"],"mocked answer")
  self.assertFalse(result["tool_execution_performed"])
  self.assertEqual(opener.return_value.open.call_args.args[0].get_header("Authorization"),"Bearer test-secret")
 def test_model_id_required(self):
  with patch.dict(os.environ,{"OPENAI_API_KEY":"secret"},clear=True):
   with self.assertRaisesRegex(GatewayError,"VAIXLNS_MODEL_OPENAI"): invoke_model("openai","test")

if __name__=="__main__": unittest.main()
