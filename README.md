# MotionAI Studio

Run `./start.sh` and open the local address printed in the terminal. The launcher never kills other applications using a port. Python 3, Node, Claude CLI and an existing Remotion project are required.

## Connection

Open «تنظیمات اتصال», set the router URL, API key and Remotion project path. The key is kept only in page memory; alternatively set `MOTION_API_KEY` before starting the server. No API key is embedded in public files. Enter a model identifier manually or fetch the router's models. Model availability depends on the router account. Generation requires an Anthropic-compatible endpoint supported by Claude CLI; prompt enhancement also supports OpenAI-compatible chat completions.

## Workflow

1. Enter an idea, choose among twelve styles, Persian/English output, aspect ratio, FPS and 5–1800 seconds.
2. Enhance the prompt to review an editable brief, specific improvements and a scene plan. If the service fails, the UI displays an actionable error and preserves the previous prompt. An offline template is available only through its separate explicit button. Changing settings flags the prior enhancement as stale.
3. Generate. The studio streams visible model responses and tool names, checks TypeScript, then renders the unique composition created for that job to H.264 MP4.
4. Play or download the result. Archive playback supports projects outside the default directory. Stop cancels the running process group.

Token counts are provider-reported, not character-based estimates. Live usage depends on the provider returning usage events. Final usage replaces interim counts. Prompt enhancement is shown separately. Cost is shown only when reported by Claude CLI; it may not reflect a router's billing. Progress percentages apply to observed rendered frames only; other phases are indeterminate. No completion-time estimate is fabricated.

Audio uses verified existing project assets. The app does not synthesize narration or download stock music. A 30-minute duration is accepted, but successful output still depends on model context, generated scene quality and rendering resources. This release has not been verified with a complete paid model generation or a 30-minute render.

SSE events and active jobs are retained in memory until server restart, with reconnect replay. Keep this local tool bound to localhost; it executes generated code in the selected project. Existing output videos are rediscovered from the archive after restart.

## Validation

`python3 -m unittest discover -s tests -v`

Tests cover concurrent SSE/static responses and reconnect replay, custom-project video range delivery, input validation, localized offline scene coverage, stopping after model failure, and structured usage parsing.

## macOS browser permission failure

If Chromium reports `MachPortRendezvous` / `bootstrap_check_in` / `Permission denied (1100)`, run `Start Studio.command` yourself from Finder, or run `./start.sh` in an ordinary macOS Terminal. A server started in a restricted execution environment passes those restrictions to Chromium. The launcher opens a fresh local panel starting at port 8100 and does not stop existing servers. Keep its Terminal window open.

Use «رندر مجدد بدون مدل» to render existing source files without generating code or spending model tokens. It does not apply new creative settings. The optional composition field selects a specific composition; otherwise MotionFilm is preferred, or a single non-HelloWorld composition is detected. Ambiguous projects require explicit selection. Browser startup is checked before model generation, so this environmental failure is detected before model usage. No browser security flags or macOS security settings are disabled.

## Prompt enhancement diagnostics

The router may list models without authentication while requiring an API key for generation. Enter the key in Connection Settings or provide MOTION_API_KEY when starting the server. Page reload clears the in-memory key. Authentication failures, rate limits, timeouts and malformed/truncated model output have distinct messages. No silent offline fallback occurs. The parser accepts JSON inside Markdown fences or surrounding prose and validates scene continuity. Restart the running server after updates; reloading only the page does not reload Python code.

## Style selection and fresh compositions

New generation always gets a unique MotionFilm identifier and new component file; it never falls back to an existing composition or the render-only composition selection. Missing new files or registration stop the pipeline. These checks establish that the new composition exists and is connected, but do not automatically judge visual fidelity to a style.

Selected style and custom art-direction notes are explicit generation constraints. Pixel art no longer implies a platformer. If creative settings changed after enhancement, generation uses the current original idea rather than the stale enhanced prompt; enhance again to review an updated detailed brief. “Render existing code” intentionally preserves existing visuals and does not apply style changes. Restart the server after updating the source.
