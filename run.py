#!/usr/bin/env python
"""One entry point for everything.   python run.py <command>

  setup   install packages + create .env if missing
  check   test the Hindsight connection
  demo    scripted learning-over-time demo (terminal)
  text    interactive text console (no microphone needed)
  web     web UI at http://localhost:8000   (add --port 9000 to change)
  phone   web UI reachable from your phone on the same Wi-Fi
  voice   Laksh voice assistant + memory (Windows, needs microphone)
  test    run the self-tests
"""
import os, socket, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
CORE = ["hindsight-client", "fastapi", "uvicorn", "requests", "pydantic"]
VOICE = ["SpeechRecognition", "pyttsx3", "pyautogui", "psutil", "pyperclip", "pywin32", "pyaudio"]


def py(*args):
    return subprocess.call([sys.executable, *args], env=ENV)


def pip(*pkgs):
    return py("-m", "pip", "install", "--quiet", *pkgs) == 0


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except OSError:
        return "your-laptop-ip"
    finally:
        s.close()


def setup():
    if sys.version_info >= (3, 13):
        print(f"! Python {sys.version_info.major}.{sys.version_info.minor}: works for web/text, but microphone support "
              "(PyAudio) needs Python 3.11. Install 3.11 and use laksh.bat.")
    if not (ROOT / ".env").exists():
        (ROOT / ".env").write_text((ROOT / ".env.example").read_text())
        print("Created .env - open it and fill in your keys.")
    print("Installing core packages...")
    if not pip(*CORE):
        sys.exit("Core install failed. Check your internet connection, then run setup again.")
    if os.name == "nt":
        print("Installing voice packages (each one separately)...")
        bad = [p for p in VOICE if not pip(p)]
        if bad:
            print(f"! Could not install: {', '.join(bad)}. Web, text and demo modes still work.")
            if "pyaudio" in bad:
                print("  PyAudio has no build for this Python. Use Python 3.11 (py -3.11 run.py setup).")
    print("Setup done. Next: python run.py check")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    rest = sys.argv[2:]
    port = rest[rest.index("--port") + 1] if "--port" in rest else "8000"
    if cmd == "setup": setup()
    elif cmd == "check": sys.exit(py("check_hindsight.py"))
    elif cmd == "demo": sys.exit(py("cli_demo.py"))
    elif cmd == "text": sys.exit(py("chat_cli.py"))
    elif cmd == "voice": sys.exit(py("laksh_voice.py", *rest))
    elif cmd == "test":
        pip("pytest", "httpx"); sys.exit(py("-m", "pytest", "-q", "tests"))
    elif cmd == "web":
        print(f"\n  LAKSH Ops -> http://localhost:{port}\n"); sys.exit(py("-m", "uvicorn", "server:app", "--port", port))
    elif cmd == "phone":
        print(f"\n  On your phone (same Wi-Fi) open:  http://{lan_ip()}:{port}\n  (allow Python through the Windows firewall if asked)\n")
        sys.exit(py("-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", port))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
