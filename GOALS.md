# K-CLI Product Goals

## Product outcome

Make K-CLI a developer-first, verification-first agentic coding workspace that
developers choose for real repository work—not merely a prompt-to-code demo.

## Experience goals

1. Make every core workflow discoverable through both clicks and keyboard input:
   plan, context selection, run, verify, diff, review, and rollback.
2. Keep developers in control: show the active model, working context, run
   state, verification evidence, and uncommitted changes at the moment they
   matter.
3. Make the workstation feel premium through calm information hierarchy,
   responsive feedback, accessible focus states, and progressive disclosure—no
   copied third-party UI or decorative noise that hides important actions.
4. Support local and cloud coding models through Ollama, llama.cpp, native
   GGUF, native provider APIs, OpenRouter, and the OpenAI-compatible
   chat-completions protocol. New or unusual providers should be addable through
   a small adapter, rather than being claimed as universally compatible.
5. Preserve the verification-first boundary: a generated answer is a candidate
   until the configured local checks pass; irreversible or destructive actions
   must stay explicit and reviewable.

## Definition of done for each UI change

- It works with mouse/click, Enter, and documented shortcuts where appropriate.
- It has a clear empty, loading, success, and failure state.
- It is covered by a focused automated test.
- It does not weaken workspace containment, verification, or Git safeguards.

## Near-term roadmap

- [x] Add protected planning, context visibility, verification cards, diff view,
  and a custom-model field to the workstation.
- [ ] Add a model/provider connection screen with health checks and saved local
  profiles that never store secrets in the repository.
- [ ] Add an explicit review-and-approve step before any workspace patch is
  applied.
- [ ] Capture an authentic terminal demo and publish a v0.3.0 release.
