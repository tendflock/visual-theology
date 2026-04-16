"""LLM client abstraction for sermon_analyzer and sermon_coach_agent.

LLMClient is a Protocol. Production code uses AnthropicClient. Tests use
CannedLLMClient to pin LLM outputs without making real API calls.
"""

from __future__ import annotations
import hashlib
import json
from typing import Protocol, Optional, Iterator


class LLMClient(Protocol):
    """Structural interface any LLM client must satisfy."""
    def call(self, prompt: str, schema: dict, **kwargs) -> dict: ...
    def stream_message(self, system: str, messages: list, tools: list,
                       max_tokens: int = 4096) -> Iterator[dict]: ...


class CannedLLMClient:
    """Test double. Returns pre-registered responses keyed by prompt or hash prefix."""

    def __init__(self, fixtures: dict):
        self.fixtures = dict(fixtures)

    def call(self, prompt: str, schema: Optional[dict] = None, **kwargs) -> dict:
        if prompt in self.fixtures:
            return self.fixtures[prompt]
        key = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if key in self.fixtures:
            return self.fixtures[key]
        return {'error': f'no canned response for prompt hash {key}'}

    def stream_message(self, system: str, messages: list, tools: list,
                       max_tokens: int = 4096) -> Iterator[dict]:
        yield {'type': 'text_delta', 'text': 'canned streaming response'}
        yield {'type': 'message_complete',
               'usage': {'input_tokens': 0, 'output_tokens': 0},
               'stop_reason': 'end_turn', 'content': []}


class AnthropicClient:
    """Real client using the anthropic SDK. Opus 4.6 by default.

    The anthropic package is imported lazily inside _get_client() so that tests
    and code paths that never invoke the real API don't require the SDK to be
    installed at import time.
    """

    def __init__(self, api_key: str, model: str = 'claude-opus-4-6'):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def call(self, prompt: str, schema: dict, *,
             max_tokens: int = 4096,
             system: Optional[str] = None,
             track_usage: bool = True) -> dict:
        """Call the model with a tool-use-enforced schema.

        Returns {output: dict, input_tokens: int, output_tokens: int, model: str}.
        On error, returns {error: str}.
        """
        try:
            client = self._get_client()
        except Exception as e:
            return {'error': f'sdk_import_failed: {type(e).__name__}: {e}'}
        try:
            messages = [{'role': 'user', 'content': prompt}]
            tools = [{
                'name': 'emit_review',
                'description': 'Emit the structured sermon review following the schema.',
                'input_schema': schema,
            }]
            kwargs = dict(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                tools=tools,
                tool_choice={'type': 'tool', 'name': 'emit_review'},
            )
            if system:
                kwargs['system'] = system
            response = client.messages.create(**kwargs)
        except Exception as e:
            return {'error': f'{type(e).__name__}: {e}'}

        tool_block = None
        for block in response.content:
            if getattr(block, 'type', None) == 'tool_use':
                tool_block = block
                break
        if tool_block is None:
            return {'error': 'no tool_use block in response'}

        return {
            'output': tool_block.input,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'model': self.model,
        }

    def stream_message(self, system: str, messages: list, tools: list,
                       max_tokens: int = 4096) -> Iterator[dict]:
        """Stream a single model turn. Caller owns the tool-use loop."""
        try:
            client = self._get_client()
        except Exception as e:
            yield {'type': 'error', 'error': f'sdk_import_failed: {type(e).__name__}: {e}'}
            return

        tool_defs = [{'name': t['name'], 'description': t['description'],
                      'input_schema': t['input_schema']} for t in tools]
        try:
            with client.messages.stream(
                model=self.model, max_tokens=max_tokens,
                system=system, messages=messages, tools=tool_defs,
            ) as stream:
                current_tool = None
                for event in stream:
                    if event.type == 'content_block_start':
                        if getattr(event.content_block, 'type', None) == 'tool_use':
                            current_tool = {
                                'id': event.content_block.id,
                                'name': event.content_block.name,
                                'input_json': '',
                            }
                    elif event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            yield {'type': 'text_delta', 'text': event.delta.text}
                        elif hasattr(event.delta, 'partial_json') and current_tool:
                            current_tool['input_json'] += event.delta.partial_json
                    elif event.type == 'content_block_stop':
                        if current_tool:
                            try:
                                tool_input = json.loads(current_tool['input_json'])
                            except json.JSONDecodeError:
                                tool_input = {}
                            yield {
                                'type': 'tool_use',
                                'tool_name': current_tool['name'],
                                'tool_input': tool_input,
                                'tool_use_id': current_tool['id'],
                            }
                            current_tool = None
                response = stream.get_final_message()
                yield {
                    'type': 'message_complete',
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                    },
                    'stop_reason': response.stop_reason,
                    'content': response.content,
                }
        except Exception as e:
            yield {'type': 'error', 'error': f'{type(e).__name__}: {e}'}
