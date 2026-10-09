import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

from tools.sovereign_console.server import ConsoleHandler


class SovereignConsoleHttpTests(unittest.TestCase):
    def test_local_http_bridge_serves_state_and_executes_allow_list_command(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ConsoleHandler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urlopen(base + "/api/state", timeout=3) as response:
                self.assertEqual(response.status, 200)
                state = json.loads(response.read().decode("utf-8"))
            self.assertEqual(state["system"], "VAIXLNS")
            self.assertEqual(state["index_id"], "Ω.000")
            self.assertGreater(state["agent_count"], 0)

            body = json.dumps({"command": "status"}).encode("utf-8")
            request = Request(
                base + "/api/command",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=3) as response:
                self.assertEqual(response.status, 200)
                result = json.loads(response.read().decode("utf-8"))
            self.assertTrue(result["ok"], result.get("lines"))
            self.assertEqual(result["event"]["sequence"], 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_http_bridge_rejects_untrusted_origin(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), ConsoleHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            body = json.dumps({"command": "status"}).encode("utf-8")
            request = Request(
                base + "/api/command",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Origin": "https://example.invalid",
                },
                method="POST",
            )
            with self.assertRaises(Exception) as context:
                urlopen(request, timeout=3)
            self.assertIn("403", str(context.exception))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
