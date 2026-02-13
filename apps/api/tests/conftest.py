import pytest
import json
import openai
import sys
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "invoices"

def _content_getter(args, kwargs):
	prompt = ""
	if len(args) > 0 and isinstance(args[0], list):
		for msg in args[0]:
			if isinstance(msg, dict) and "content" in msg:
				prompt += msg["content"]
	if "invoice" in prompt.lower():
		return (FIXTURE_DIR / "invoice_expected.json").read_text(encoding="utf-8")
	return (FIXTURE_DIR / "proposal_expected.json").read_text(encoding="utf-8")

class _Msg:
	def __init__(self, content): self.content = content
class _Choice:
	def __init__(self, content): self.message = _Msg(content)
class _ChatCompletions:
	def __init__(self, content_getter): self._get = content_getter
	async def create(self, *args, **kwargs):
		if kwargs.get("response_format", {}).get("type") == "json_object":
			content = self._get(args, kwargs)
		else:
			content = "PROFESSIONAL_TEXT_STUB"
		return type("Resp", (), {"choices": [_Choice(content)]})()
class _Chat:
	def __init__(self, content_getter): self.completions = _ChatCompletions(content_getter)
class FakeOpenAI:
	def __init__(self, *a, **kw):
		self.chat = _Chat(_content_getter)
		self.responses = self
		self._get = _content_getter
	def create(self, *args, **kwargs):
		content = self._get(args, kwargs)
		return type("Resp", (), {"output_text": content})()

@pytest.fixture(autouse=True)
def patch_openai_everywhere(monkeypatch):
	# Patch openai.OpenAI and openai.AsyncOpenAI globally
	monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
	monkeypatch.setattr(openai, "AsyncOpenAI", FakeOpenAI)
	# Patch all app.* modules' OpenAI/AsyncOpenAI symbols
	for mod in list(sys.modules.values()):
		if not hasattr(mod, "__name__") or not mod.__name__.startswith("app."):
			continue
		for attr in ("OpenAI", "AsyncOpenAI"):
			if hasattr(mod, attr):
				monkeypatch.setattr(mod, attr, FakeOpenAI)
		# Patch .client if it looks like an OpenAI client
		if hasattr(mod, "client"):
			c = getattr(mod, "client")
			if hasattr(c, "chat") and hasattr(c, "responses"):
				monkeypatch.setattr(mod, "client", FakeOpenAI())

@pytest.fixture(scope="function")
def client():
	# Import app.main only after patching OpenAI
	from fastapi.testclient import TestClient
	import app.main
	return TestClient(app.main.app)
import os
# Set test environment variables before app import
os.environ["DEMO_PASSWORD"] = "demo2026"
os.environ["ADMIN_PASSWORD"] = "admin2026"
os.environ["OPENAI_API_KEY"] = "dummy"
