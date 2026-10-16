"""Explicit-invocation VAIXLNS text model gateway MCP server."""
from __future__ import annotations
import json, os, urllib.error, urllib.parse, urllib.request
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("VAIXLNS Model Gateway (explicit invocation only)")
MAX_PROMPT_CHARS = 40000
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 60
PROVIDERS = {
 "openai": {"key_env":"OPENAI_API_KEY","model_env":"VAIXLNS_MODEL_OPENAI","endpoint":"https://api.openai.com/v1/chat/completions","kind":"compatible"},
 "claude": {"key_env":"ANTHROPIC_API_KEY","model_env":"VAIXLNS_MODEL_CLAUDE","endpoint":"https://api.anthropic.com/v1/messages","kind":"anthropic"},
 "gemini": {"key_env":"GEMINI_API_KEY","model_env":"VAIXLNS_MODEL_GEMINI","endpoint":"https://generativelanguage.googleapis.com/v1beta/models/","kind":"gemini"},
 "grok": {"key_env":"XAI_API_KEY","model_env":"VAIXLNS_MODEL_GROK","endpoint":"https://api.x.ai/v1/chat/completions","kind":"compatible"},
 "mistral": {"key_env":"MISTRAL_API_KEY","model_env":"VAIXLNS_MODEL_MISTRAL","endpoint":"https://api.mistral.ai/v1/chat/completions","kind":"compatible"},
}
class GatewayError(ValueError):
 """Safe gateway error that avoids exposing provider response bodies."""
class _NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
  return None

def _configuration(provider: str):
 key=provider.strip().lower()
 if key not in PROVIDERS: raise GatewayError("Unsupported provider: choose openai, claude, gemini, grok, or mistral.")
 cfg=PROVIDERS[key]; secret=os.environ.get(cfg["key_env"],"").strip(); model=os.environ.get(cfg["model_env"],"").strip()
 if not secret: raise GatewayError("Missing provider credential environment variable: "+cfg["key_env"])
 if not model: raise GatewayError("Missing provider model environment variable: "+cfg["model_env"])
 return key,cfg,secret,model

@mcp.tool()
def list_model_providers() -> dict[str, Any]:
 """List configured providers without revealing credential values or making network calls."""
 rows=[]
 for name,cfg in PROVIDERS.items():
  has_key=bool(os.environ.get(cfg["key_env"],"").strip()); has_model=bool(os.environ.get(cfg["model_env"],"").strip())
  rows.append({"provider":name,"configured":has_key and has_model,"credential_present":has_key,"model_configured":has_model,"credential_env":cfg["key_env"],"model_env":cfg["model_env"],"status":"CONFIGURED" if has_key and has_model else "MISSING_CONFIGURATION","live_connectivity_verified":False})
 return {"status":"PARTIAL","providers":rows,"note":"Configuration presence is not proof of API connectivity."}

def _invoke(provider: str, prompt: str, max_output_tokens: int) -> dict[str, Any]:
 name,cfg,secret,model=_configuration(provider); kind=cfg["kind"]
 headers={"Content-Type":"application/json","Accept":"application/json"}
 if kind=="anthropic":
  headers.update({"x-api-key":secret,"anthropic-version":"2023-06-01"})
  url=cfg["endpoint"]; body={"model":model,"max_tokens":max_output_tokens,"messages":[{"role":"user","content":prompt}]}
 elif kind=="gemini":
  headers["x-goog-api-key"]=secret; url=cfg["endpoint"]+urllib.parse.quote(model,safe="")+":generateContent"
  body={"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":max_output_tokens}}
 else:
  headers["Authorization"]="Bearer "+secret; url=cfg["endpoint"]
  body={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":max_output_tokens}
 req=urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode(),headers=headers,method="POST")
 try:
  with urllib.request.build_opener(_NoRedirect()).open(req,timeout=TIMEOUT_SECONDS) as response:
   raw=response.read(MAX_RESPONSE_BYTES+1)
  if len(raw)>MAX_RESPONSE_BYTES: raise GatewayError("Provider response exceeded the size limit.")
  data=json.loads(raw.decode("utf-8"))
 except urllib.error.HTTPError as exc: raise GatewayError("Provider returned HTTP "+str(exc.code)+" ("+name+"); response body withheld.") from None
 except urllib.error.URLError: raise GatewayError("Provider connection failed ("+name+").") from None
 except (TimeoutError,OSError): raise GatewayError("Provider request timed out or failed ("+name+").") from None
 except (UnicodeDecodeError,json.JSONDecodeError): raise GatewayError("Provider returned invalid JSON ("+name+").") from None
 try:
  if kind=="anthropic": text="\n".join(x["text"] for x in data["content"] if x.get("type")=="text" and isinstance(x.get("text"),str))
  elif kind=="gemini": text="\n".join(p["text"] for c in data["candidates"] for p in c.get("content",{}).get("parts",[]) if isinstance(p.get("text"),str))
  else: text=data["choices"][0]["message"]["content"]
 except (KeyError,IndexError,TypeError): raise GatewayError("Provider response failed the expected text contract ("+name+").") from None
 if not isinstance(text,str) or not text.strip(): raise GatewayError("Provider returned no text output ("+name+").")
 return {"status":"RESPONSE_RECEIVED","provider":name,"model":model,"text":text,"execution_state":"NOT_INDEPENDENTLY_VERIFIED","tool_execution_performed":False,"canonical_write_performed":False}

@mcp.tool()
def invoke_model(provider: str, prompt: str, max_output_tokens: int=2048) -> dict[str, Any]:
 """Explicitly call one provider for one text prompt; no tool calls or automatic routing."""
 if not isinstance(prompt,str) or not prompt.strip(): raise GatewayError("A non-empty prompt is required.")
 if len(prompt)>MAX_PROMPT_CHARS: raise GatewayError("Prompt exceeds the 40000-character limit.")
 if not isinstance(max_output_tokens,int) or isinstance(max_output_tokens,bool) or not 1<=max_output_tokens<=8192: raise GatewayError("max_output_tokens must be an integer from 1 to 8192.")
 return _invoke(provider,prompt,max_output_tokens)

if __name__=="__main__": mcp.run(transport="stdio")
