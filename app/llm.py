"""Model layer: OpenAI or Anthropic for answers, OpenAI for embeddings. Everything configurable through environment variables."""

import os

OPENAI_KEY = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY', '')
PROVIDER = os.getenv('LLM_PROVIDER') or ('openai' if OPENAI_KEY else 'anthropic' if ANTHROPIC_KEY else 'none')
OPENAI_PREFS = [m for m in [os.getenv('OPENAI_CHAT_MODEL')] if m] + [
    'gpt-5.4-mini',
    'gpt-5-mini',
    'gpt-4.1-mini',
    'gpt-4o-mini',
]
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_CHAT_MODEL', 'claude-haiku-5-5')
EMBED_MODEL = os.getenv('EMBED_MODEL', 'text-embedding-3-small')

_oa = None
_an = None
_chat_model = None


def openai_client():
    global _oa
    if _oa is None and OPENAI_KEY:
        from openai import OpenAI

        _oa = OpenAI(api_key=OPENAI_KEY)
    return _oa


def anthropic_client():
    global _an
    if _an is None and ANTHROPIC_KEY:
        import anthropic

        _an = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    return _an


def chat_model():
    """First preferred OpenAI model this key can use (checked once), or the Anthropic model."""
    global _chat_model
    if _chat_model:
        return _chat_model
    if PROVIDER == 'openai':
        try:
            have = {m.id for m in openai_client().models.list()}
            _chat_model = next((m for m in OPENAI_PREFS if m in have), OPENAI_PREFS[0])
        except Exception:
            _chat_model = OPENAI_PREFS[0]
    elif PROVIDER == 'anthropic':
        _chat_model = ANTHROPIC_MODEL
    else:
        _chat_model = 'none'
    return _chat_model


def can_embed():
    return bool(OPENAI_KEY)


def embed(texts, batch=96):
    cl = openai_client()
    out = []
    for i in range(0, len(texts), batch):
        r = cl.embeddings.create(model=EMBED_MODEL, input=texts[i : i + batch])
        out.extend(d.embedding for d in r.data)
    return out


def complete(system, messages, max_tokens=300):
    """One-shot (non-streaming) completion, used for query rewriting."""
    return ''.join(stream(system, messages, max_tokens=max_tokens))


def stream(system, messages, max_tokens=900):
    """Yield answer text deltas. messages = [{'role': 'user'|'assistant', 'content': str}]"""
    model = chat_model()
    if PROVIDER == 'openai':
        kw = dict(model=model, messages=[{'role': 'system', 'content': system}] + messages, stream=True)
        if model.startswith(('gpt-5', 'o')):
            kw['max_completion_tokens'] = max_tokens * 4  # reasoning models spend tokens before answering
            kw['reasoning_effort'] = 'low'
        else:
            kw['max_tokens'] = max_tokens
            kw['temperature'] = 0.2
        for ev in openai_client().chat.completions.create(**kw):
            if ev.choices and ev.choices[0].delta and ev.choices[0].delta.content:
                yield ev.choices[0].delta.content
    elif PROVIDER == 'anthropic':
        with anthropic_client().messages.stream(
            model=model, system=system, messages=messages, max_tokens=max_tokens, temperature=0.2
        ) as s:
            yield from s.text_stream
    else:
        raise RuntimeError('No model configured: set OPENAI_API_KEY or ANTHROPIC_API_KEY')
