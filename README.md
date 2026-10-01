# MotionAI Studio

**Turn an idea into an animated video with AI-assisted prompts, custom visual styles, and a local Remotion workflow.**

MotionAI Studio is a local web application. Describe your video, choose its visual style and language, review the enhanced prompt, and generate an MP4. The studio uses Claude Code to create React/Remotion scenes, checks TypeScript, and renders the result on your computer.

> **Project status:** Early-stage software. Automated backend tests have passed on macOS. Windows installation through WSL is documented below but has not been verified end to end. Model-generated videos and long renders can require troubleshooting.

## Features

- Twelve visual styles, including cinematic, editorial, minimalist, glass, typography, infographic, cyberpunk, cartoon, pixel art, paper, luxury, and isometric.
- Custom art-direction notes for colors, atmosphere, motion, and composition.
- Persian or English video text. The current interface is primarily Persian.
- Editable enhanced prompts, an improvement summary, and a scene timeline.
- Manual model selection and model discovery from a compatible router.
- Landscape, portrait, and square output at 24, 30, or 60 FPS.
- Configurable duration from 5 seconds to 30 minutes.
- Live activity, frame-rendering progress, elapsed time, and provider-reported usage.
- A separate option to render existing code without calling the AI model.
- Video playback, MP4 downloads, and a local output archive.

## Before you begin

You will set up three separate parts:

| Part | Purpose | Example location |
| --- | --- | --- |
| MotionAI Studio | The web interface and Python server | `~/motionai-studio` |
| Remotion project | Generated scenes, dependencies, and video output | `~/my-video` |
| AI router | Connects the selected model to the studio | Local 9Router service |

You need Python 3, Git, a current Node.js LTS release with npm, Claude Code, and access to a compatible AI provider. Python 3.12 or newer is a straightforward starting point. The studio backend uses Python's standard library, so there is no `pip install` step.

Installing these tools does not automatically provide AI access. Provider accounts, quotas, and charges depend on your chosen service. Video generation requires Claude Code-compatible tool use through an Anthropic-compatible endpoint. An endpoint that only supports ordinary chat completions is not sufficient for the complete workflow.

This guide uses 9Router as the example service. You may use another compatible service with the appropriate base URL, key, and model identifier.

## 1. Install the tools

Choose the instructions for your operating system. Afterward, continue with section 2.

### macOS

Open **Terminal** from Applications → Utilities.

**Install Git:**

```bash
xcode-select --install
```

Complete the installer. If the command says the tools are already installed, continue.

**Install Python:**

Download the macOS installer from [Python Downloads](https://www.python.org/downloads/macos/), run it, and reopen Terminal.

**Install Node.js:**

Download the **LTS** macOS installer from [Node.js Downloads](https://nodejs.org/en/download), run it, and reopen Terminal.

Check the tools:

```bash
git --version
python3 --version
node --version
npm --version
```

Each command should print a version number.

### Windows: use WSL 2 with Ubuntu

For this version of MotionAI Studio, use Ubuntu inside WSL instead of running the Python server directly in PowerShell. The application's process-management code and launch scripts are written for a Unix environment.

Open **PowerShell as Administrator**, then run:

```powershell
wsl --install -d Ubuntu-24.04
```

Restart Windows if requested. Open **Ubuntu** from the Start menu and create your Linux username and password. Password characters are not displayed while typing; this is normal. See [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install) if setup fails.

**Run all remaining Windows commands in Ubuntu, not PowerShell.**

Install the basic tools:

```bash
sudo apt update
sudo apt install -y python3 git curl ca-certificates build-essential
```

Install Node.js using nvm:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
```

Close and reopen Ubuntu, then run:

```bash
nvm install --lts
nvm use --lts
```

This follows the [official nvm installation instructions](https://github.com/nvm-sh/nvm#installing-and-updating).

Verify the tools:

```bash
python3 --version
git --version
node --version
npm --version
```

Install the browser libraries needed for rendering on Ubuntu 24.04:

```bash
sudo apt install -y \
  libnss3 libdbus-1-3 libatk1.0-0 libasound2t64 \
  libxrandr2 libxkbcommon-dev libxfixes3 libxcomposite1 \
  libxdamage1 libgbm-dev libcups2 libcairo2 \
  libpango-1.0-0 libatk-bridge2.0-0
```

Other distributions may need different package names. Refer to [Remotion's Linux dependencies](https://www.remotion.dev/docs/miscellaneous/linux-dependencies).

Keep the studio, Remotion project, and router inside the same Ubuntu environment. Use folders under `~`, rather than mixing Windows and Linux installations.

## 2. Install Claude Code

In macOS Terminal or Ubuntu on Windows:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Close and reopen your terminal, then check:

```bash
claude --version
```

If the command is not found, follow the installer's PATH instructions. For the current terminal, the default installation can usually be made available with:

```bash
export PATH="$HOME/.local/bin:$PATH"
claude --version
```

See the [official Claude Code setup guide](https://code.claude.com/docs/en/setup). The studio passes its configured router and API key to Claude Code; installing or signing into the CLI alone does not configure the studio's router connection.

## 3. Download MotionAI Studio

Replace `YOUR_USERNAME` and `YOUR_REPOSITORY` with the owner and repository name shown on this project's GitHub page:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git motionai-studio
cd ~/motionai-studio
```

The folder should contain:

```text
motionai-studio/
├── app.py
├── start.sh
├── Start Studio.command
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
└── tests/
    └── test_studio.py
```

The installation commands in this guide assume the folder is named `motionai-studio`.

## 4. Create your Remotion video project

The studio does not include a ready-to-use Remotion workspace. Create it separately:

```bash
cd ~
npx create-video@latest
```

In the setup wizard:

1. Choose a basic **Hello World** Remotion template with TypeScript.
2. Name the project `my-video`.
3. Finish the wizard.

Then install its dependencies:

```bash
cd ~/my-video
npm install
```

See [Remotion's project setup documentation](https://www.remotion.dev/docs/).

Install the rendering browser and check the project:

```bash
npx remotion browser ensure
npx tsc --noEmit
npx remotion compositions
```

The last command should list available compositions. If these checks fail, resolve that issue before generating a video in the studio. The browser download is handled by [Remotion's browser command](https://www.remotion.dev/docs/cli/browser).

Already have a Remotion project? You can use it instead, provided its dependencies are installed and these checks pass. Keep a backup of important work because the AI edits files in the selected project.

## 5. Set up the AI router

In a separate terminal window:

```bash
npm install -g 9router
9router
```

Open the router dashboard at [localhost:20128](http://localhost:20128). Connect an AI provider you have access to, obtain a router API key, and note the exact model identifier available through that connection. Follow the [9Router setup instructions](https://github.com/decolua/9router) for provider-specific steps.

Keep the router running while using MotionAI Studio. On Windows, run it inside the same Ubuntu environment as the studio.

If npm reports a global-install permissions error, use Node through [nvm](https://github.com/nvm-sh/nvm), reopen the terminal, and retry the installation.

## 6. Start MotionAI Studio

Open another terminal window:

```bash
cd ~/motionai-studio
bash start.sh
```

Open the address printed in that terminal, usually:

```text
http://127.0.0.1:8080
```

If the port is occupied, the program tries the next available port. Always use the printed address. Keep the terminal open while working.

On Windows, open that address in your usual Windows browser. If localhost forwarding does not work, try a browser within your WSL environment or review your WSL networking configuration; the app listens only on the loopback interface.

**Optional macOS launcher:**

```bash
cd ~/motionai-studio
chmod +x start.sh "Start Studio.command"
./"Start Studio.command"
```

This launcher opens the browser automatically and starts searching for a free port at `8100`. If your Node installation depends on nvm, launching with `bash start.sh` from a terminal where `node --version` works is the simplest option.

## 7. Connect the studio to your model

Click **تنظیمات اتصال** — Connection Settings.

| Setting | What to enter |
| --- | --- |
| Service URL | `http://localhost:20128/v1` for the example router |
| API key | Your router API key |
| Remotion project path | `~/my-video`, or your own project folder |
| Composition identifier | Leave empty for a new generation; this field is for rendering existing code |

In the model field, enter the exact identifier provided by your router, or use **دریافت مدل‌ها** — Fetch Models. The prefilled model is only an example and may not be available to your account.

The API key stays in page memory and is cleared when the page reloads. Enter it again after refreshing. Alternatively, the server can read the `MOTION_API_KEY` environment variable supplied before startup. The application does not automatically load a `.env` file.

A visible model list does not prove authentication works: some routers allow listing models without a key but require one for generation.

## 8. Create your first video

Start with a short test: **10 seconds, 30 FPS, and landscape format**.

1. Enter an idea, for example: “Create a cinematic coffee advertisement with warm morning light, elegant titles, and a calm ending.”
2. Select **Cinematic**, or another visual style.
3. Add custom style notes if needed, such as “Warm brown and gold palette, slow motion, no game characters.”
4. Select Persian or English for the video text.
5. Choose duration, aspect ratio, and FPS.
6. Click **بهبود حرفه‌ای پرامپت** — Enhance Prompt.
7. Review the editable prompt, improvement summary, and scene timeline.
8. Click **ساخت ویدیو** — Generate Video.
9. Watch the activity panel while the model creates code, TypeScript is checked, and Remotion renders the video.
10. Play or download the completed MP4.

Files are saved in the `out` folder of your Remotion project, for example `~/my-video/out`.

If you change the idea or creative settings after enhancement, enhance again to review an updated brief. Otherwise, generation uses your current original idea and settings instead of the stale enhanced prompt.

### Generate a new video or render existing code?

| Action | Calls the model? | Applies a new style or idea? |
| --- | --- | --- |
| Generate Video | Yes | Yes, through newly generated code |
| Render Existing Code | No | No; it renders the current source files |

To change a previous game's visuals into a cinematic advertisement, use **Generate Video**. Re-rendering existing code will preserve the game's appearance.

Every new generation requests its own composition and component file. If that new scene is missing, the studio stops instead of silently rendering an old one. This checks scene registration, not artistic quality.

## 9. Understand progress and usage

- Elapsed time measures the current job's running time.
- A moving progress indicator means the phase has no measurable percentage yet.
- Frame percentages describe observed rendering progress, not a guaranteed overall completion percentage.
- Token counts come from the provider or CLI, not from counting displayed characters.
- Prompt enhancement and video generation have separate usage displays.
- A dash means the value has not been reported.
- Reported cost may differ from your router's actual billing.

## Troubleshooting

### “Missing API key” or HTTP 401/403

Open Connection Settings and enter a valid router key. If you refreshed the page, the in-memory key was cleared. Also check that the connected provider permits the chosen model.

### Prompt enhancement returns an error

Check the service URL, API key, model identifier, and router status. Timeouts, exhausted quotas, incomplete responses, and invalid scene timelines now produce explicit messages. Your previous prompt is preserved.

The separate local-template button works without calling the model. A local template is not an AI-enhanced result.

### “claude”, “node”, or “npx” cannot be found

Run their version commands in the same terminal used to start the studio. Fix PATH or reopen the terminal after installation, then restart the studio.

### Remotion project not found

The setting must point to the folder containing the Remotion `package.json`, not the MotionAI Studio folder. Run `npm install` inside that Remotion folder.

### Browser launch fails on macOS

If the error contains `MachPortRendezvous`, `bootstrap_check_in`, or `Permission denied (1100)`, start the studio from an ordinary macOS Terminal. Restricted execution environments can prevent the rendering browser from starting. Restarting only the web page does not change the server's permissions.

### Browser launch fails in WSL

Check the Ubuntu browser libraries in section 1. Then run the browser and composition checks in section 4 from Ubuntu. Do not mix a Windows Node installation with Linux project dependencies.

### The output still looks like the previous video

Use Generate Video rather than Render Existing Code. Review your idea, selected style, style notes, and enhanced prompt. After installing updates, restart the Python server so the new generation checks take effect.

### TypeScript or generated-code errors

Read the activity log. The model may have created invalid code or used an unavailable dependency. Inspect the Remotion project or retry generation with a shorter, clearer request. Re-rendering alone does not repair code.

### The video has no audio

The current implementation uses verified audio assets already present in the project. It does not generate narration or automatically download music. Checking an audio option does not create an audio file.

### A long video fails or takes too long

Thirty minutes is the accepted duration limit, not a guarantee of successful generation or rendering. Begin with short clips. Larger durations, higher FPS, and complex scenes require more time and resources.

## Stop, restart, and update

Use the Stop button to cancel the current job. To stop the web server, press **Ctrl+C** in its terminal. Stop the router separately when you are finished.

To update a clean Git checkout:

```bash
cd ~/motionai-studio
git pull
bash start.sh
```

Stop the old server before restarting. If you have local code changes, save or commit them before pulling. Browser refresh alone does not reload the Python backend.

## Run the tests

From the MotionAI Studio folder:

```bash
python3 -m unittest discover -s tests -v
node --check static/app.js
```

The tests cover server behavior, playback byte ranges, prompt parsing, usage parsing, and fresh-scene validation. They do not prove that every provider works or that generated videos match their requested visual style.

## Current limitations

- The interface is primarily Persian; output text can be Persian or English.
- Windows native execution is not supported by this guide; use WSL.
- A full WSL installation and 30-minute production render have not been verified.
- Jobs and event history are held in memory and disappear when the server restarts. Saved MP4s remain on disk.
- The application runs generated code locally. It is intended for personal localhost use, not as a publicly exposed multi-user service.
- Internet access is required for model calls and initial dependency downloads. The optional web font also loads from an external service.

## Before publishing your own fork

Do not commit API keys, account configuration, private assets, dependency folders, or local backup files. If you add a license, choose it explicitly and include a `LICENSE` file; this guide does not assign one. Third-party tools and assets retain their own license terms.
