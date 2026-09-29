"""
LAKSH - Complete AI Voice Assistant v4.0
- Scans ALL apps/folders on your laptop
- Auto-starts on every boot
- Controls everything by voice
- Always listening, no Enter needed
"""

import speech_recognition as sr
import pyttsx3
import os, sys, subprocess, webbrowser, datetime, time, re
import ctypes, pyautogui, psutil, requests, pyperclip, json, winreg
from pathlib import Path

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laksh_cache.json")

BUILTIN_APPS = {
    "notepad":"notepad.exe","calculator":"calc.exe","paint":"mspaint.exe",
    "chrome":"chrome.exe","google chrome":"chrome.exe","firefox":"firefox.exe",
    "edge":"msedge.exe","microsoft edge":"msedge.exe","word":"WINWORD.EXE",
    "excel":"EXCEL.EXE","powerpoint":"POWERPNT.EXE","teams":"Teams.exe",
    "discord":"Discord.exe","spotify":"Spotify.exe","vlc":"vlc.exe",
    "whatsapp":"WhatsApp.exe","telegram":"Telegram.exe","zoom":"Zoom.exe",
    "vs code":"Code.exe","visual studio code":"Code.exe","explorer":"explorer.exe",
    "file explorer":"explorer.exe","task manager":"Taskmgr.exe","cmd":"cmd.exe",
    "command prompt":"cmd.exe","powershell":"powershell.exe","wordpad":"wordpad.exe",
    "snipping tool":"SnippingTool.exe","settings":"ms-settings:","store":"ms-windows-store:",
}

CLOSE_MAP = {
    "chrome":["chrome.exe"],"google chrome":["chrome.exe"],"firefox":["firefox.exe"],
    "edge":["msedge.exe"],"browser":["chrome.exe","msedge.exe","firefox.exe"],
    "all browsers":["chrome.exe","msedge.exe","firefox.exe"],
    "youtube":["chrome.exe","msedge.exe","firefox.exe"],
    "whatsapp":["WhatsApp.exe","whatsapp.exe"],"spotify":["Spotify.exe","spotify.exe"],
    "discord":["Discord.exe","discord.exe"],"telegram":["Telegram.exe","telegram.exe"],
    "zoom":["Zoom.exe","zoom.exe"],"teams":["Teams.exe"],"vlc":["vlc.exe"],
    "notepad":["notepad.exe"],"calculator":["calc.exe"],"word":["WINWORD.EXE"],
    "excel":["EXCEL.EXE"],"powerpoint":["POWERPNT.EXE"],"task manager":["Taskmgr.exe"],
    "vs code":["Code.exe"],"visual studio code":["Code.exe"],
    "cmd":["cmd.exe"],"powershell":["powershell.exe"],
}


# ══ SYSTEM SCANNER ═══════════════════════════════
class SystemScanner:
    def __init__(self):
        self.apps = {}
        self.folders = {}
        self.files = {}
        self._load()

    def _load(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE) as f:
                    d = json.load(f)
                    self.apps = d.get("apps", {})
                    self.folders = d.get("folders", {})
                    self.files = d.get("files", {})
                print(f"  [Loaded: {len(self.apps)} apps, {len(self.folders)} folders]")
                return
            except: pass
        print("  [First run — scanning laptop. This takes ~30 seconds...]")
        self.scan_all()

    def _save(self):
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"apps":self.apps,"folders":self.folders,"files":self.files}, f)
        except: pass

    def scan_all(self):
        self._scan_apps()
        self._scan_folders()
        self._save()
        print(f"  [Scan done: {len(self.apps)} apps, {len(self.folders)} folders, {len(self.files)} files]")

    def rescan(self):
        self.apps={}; self.folders={}; self.files={}
        self.scan_all()

    def _scan_apps(self):
        # Start menu shortcuts
        for sdir in [
            os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        ]:
            if not os.path.exists(sdir): continue
            for root, _, files in os.walk(sdir):
                for f in files:
                    if f.endswith(".lnk"):
                        self.apps[f[:-4].lower().strip()] = os.path.join(root, f)
        # Exe files
        for base in [r"C:\Program Files", r"C:\Program Files (x86)",
                     os.path.expanduser(r"~\AppData\Local"),
                     os.path.expanduser(r"~\AppData\Roaming"),
                     os.path.expanduser(r"~\AppData\Local\Programs")]:
            if not os.path.exists(base): continue
            try:
                for root, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    for f in files:
                        if f.lower().endswith(".exe"):
                            n = f[:-4].lower()
                            if n not in self.apps:
                                self.apps[n] = os.path.join(root, f)
            except: continue
        for k,v in BUILTIN_APPS.items():
            if k not in self.apps: self.apps[k] = v

    def _scan_folders(self):
        user = Path.home()
        bases = [user, user/"Desktop", user/"Documents", user/"Downloads",
                 user/"Pictures", user/"Videos", user/"Music",
                 user/"OneDrive", user/"OneDrive"/"Desktop",
                 user/"OneDrive"/"Documents"]
        for b in bases:
            if b.exists():
                self.folders[b.name.lower()] = str(b)
                try:
                    for sub in b.iterdir():
                        if sub.is_dir():
                            self.folders[sub.name.lower()] = str(sub)
                except: continue
        # Files
        exts = {".pdf",".docx",".doc",".xlsx",".xls",".pptx",".ppt",
                ".txt",".mp3",".mp4",".jpg",".jpeg",".png",".zip"}
        for loc in [user/"Desktop", user/"OneDrive"/"Desktop",
                    user/"Documents", user/"OneDrive"/"Documents", user/"Downloads"]:
            if not loc.exists(): continue
            try:
                for f in loc.iterdir():
                    if f.is_file() and f.suffix.lower() in exts:
                        self.files[f.stem.lower()] = str(f)
                        self.files[f.name.lower()] = str(f)
            except: continue

    def find_app(self, q):
        q = q.lower().strip()
        if q in self.apps: return self.apps[q]
        for n,p in self.apps.items():
            if q in n or n in q: return p
        words = q.split()
        for n,p in self.apps.items():
            if any(w in n for w in words if len(w)>3): return p
        return None

    def find_folder(self, q):
        q = q.lower().strip()
        if q in self.folders: return self.folders[q]
        for n,p in self.folders.items():
            if q in n or n in q: return p
        return None

    def find_file(self, q):
        q = q.lower().strip()
        if q in self.files: return self.files[q]
        for n,p in self.files.items():
            if q in n or n in q: return p
        user = Path.home()
        for loc in [user/"Desktop", user/"OneDrive"/"Desktop",
                    user/"Documents", user/"Downloads"]:
            if not loc.exists(): continue
            try:
                for f in loc.rglob(f"*{q}*"):
                    return str(f)
            except: continue
        return None


# ══ VOICE ENGINE ════════════════════════════════
class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 165)
        self.engine.setProperty('volume', 1.0)
        for v in self.engine.getProperty('voices'):
            if 'zira' in v.name.lower():
                self.engine.setProperty('voice', v.id); break

    def speak(self, text):
        if not text: return
        print(f"\n  LAKSH: {text}")
        self.engine.say(text)
        self.engine.runAndWait()


# ══ SPEECH ENGINE ═══════════════════════════════
class SpeechEngine:
    def __init__(self):
        self.r = sr.Recognizer()
        self.r.energy_threshold = 300
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8

    def listen(self):
        with sr.Microphone() as src:
            self.r.adjust_for_ambient_noise(src, duration=0.2)
            try:
                audio = self.r.listen(src, timeout=8, phrase_time_limit=15)
                text = self.r.recognize_google(audio, language="en-IN")
                print(f"\n  YOU: {text}")
                return text.lower().strip()
            except: return None


# ══ AI BRAIN ════════════════════════════════════
class AIBrain:
    def ask(self, q):
        if GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
                d = {"contents":[{"parts":[{"text":f"You are LAKSH, a friendly AI voice PC assistant. Answer in 1-2 short sentences, no bullets: {q}"}]}],"generationConfig":{"maxOutputTokens":150}}
                r = requests.post(url, json=d, timeout=8)
                if r.status_code==200: return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            except: pass
        q2 = q.lower()
        if "how are you" in q2: return "I am doing great and always ready to help!"
        if "your name" in q2: return "I am Laksh, your personal AI assistant!"
        if "joke" in q2: return "Why do programmers prefer dark mode? Because light attracts bugs!"
        if "thank" in q2: return "You are welcome!"
        return "I am here to help. Try asking me to open an app, file, folder, or control your laptop."


# ══ WINDOW HELPER ═══════════════════════════════
class WinHelper:
    @staticmethod
    def bring_to_front(kw):
        u = ctypes.windll.user32
        Proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        found=[]
        def cb(hwnd,_):
            if u.IsWindowVisible(hwnd):
                l=u.GetWindowTextLengthW(hwnd); b=ctypes.create_unicode_buffer(l+1)
                u.GetWindowTextW(hwnd,b,l+1)
                if kw.lower() in b.value.lower(): found.append(hwnd)
            return True
        u.EnumWindows(Proc(cb),0)
        if found:
            u.ShowWindow(found[0],9); u.SetForegroundWindow(found[0]); time.sleep(0.5); return True
        return False

    @staticmethod
    def is_running(exe):
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'].lower()==exe.lower(): return True
            except: pass
        return False


# ══ PC CONTROLLER ═══════════════════════════════
class PCController:
    def __init__(self, scanner):
        self.s = scanner
        self.w = WinHelper()

    def lock(self): ctypes.windll.user32.LockWorkStation(); return "Locking your laptop."
    def shutdown(self): os.system("shutdown /s /t 10"); return "Shutting down in 10 seconds. Say cancel shutdown to stop."
    def cancel_shutdown(self): os.system("shutdown /a"); return "Shutdown cancelled."
    def restart(self): os.system("shutdown /r /t 10"); return "Restarting in 10 seconds."
    def sleep(self): os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return "Sleeping."
    def vol_up(self): [pyautogui.press('volumeup') for _ in range(5)]; return "Volume increased."
    def vol_down(self): [pyautogui.press('volumedown') for _ in range(5)]; return "Volume decreased."
    def mute(self): pyautogui.press('volumemute'); return "Muted."
    def screenshot(self):
        p=os.path.expanduser(f"~/Desktop/ss_{int(time.time())}.png"); pyautogui.screenshot(p); return "Screenshot saved to Desktop."
    def sysinfo(self):
        c=psutil.cpu_percent(1); r=psutil.virtual_memory(); b=psutil.sensors_battery()
        bt=f" Battery {b.percent:.0f}%." if b else ""
        return f"CPU {c:.0f} percent. RAM {r.percent:.0f} percent.{bt}"

    def open_app(self, name):
        n=name.lower().strip()
        uri={"settings":"ms-settings:","store":"ms-windows-store:"}
        if n in uri: os.startfile(uri[n]); return f"Opening {name}."
        path=self.s.find_app(n)
        if path:
            try:
                if path.endswith(".lnk") or (":" in path and len(path)<25): os.startfile(path)
                else: subprocess.Popen(path)
                return f"Opening {name}."
            except: pass
        if "whatsapp" in n:
            try: subprocess.Popen(["explorer.exe","shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"]); return "Opening WhatsApp."
            except: pass
            webbrowser.open("https://web.whatsapp.com"); return "Opening WhatsApp in browser."
        webbrowser.open(f"https://google.com/search?q=download+{name}"); return f"Could not find {name}. Searching Google to download it."

    def open_folder(self, name):
        n=name.lower().strip()
        shortcuts={"desktop":os.path.expanduser("~/Desktop"),"documents":os.path.expanduser("~/Documents"),
                   "downloads":os.path.expanduser("~/Downloads"),"pictures":os.path.expanduser("~/Pictures"),
                   "videos":os.path.expanduser("~/Videos"),"music":os.path.expanduser("~/Music"),
                   "onedrive":os.path.expanduser("~/OneDrive"),"this pc":"explorer","recycle bin":"shell:RecycleBinFolder"}
        if n in shortcuts:
            t=shortcuts[n]
            if t=="explorer": subprocess.Popen("explorer.exe")
            elif t.startswith("shell:"): subprocess.Popen(["explorer.exe",t])
            elif os.path.exists(t): os.startfile(t)
            else:
                od=os.path.expanduser(f"~/OneDrive/{name}")
                if os.path.exists(od): os.startfile(od)
                else: return f"Could not find {name} folder."
            return f"Opening {name} folder."
        path=self.s.find_folder(n)
        if path and os.path.exists(path): os.startfile(path); return f"Opening {name} folder."
        return f"I could not find a folder named {name}."

    def open_file(self, name):
        path=self.s.find_file(name.lower().strip())
        if path and os.path.exists(path): os.startfile(path); return f"Opening {os.path.basename(path)}."
        return f"I could not find a file named {name}."

    def close_app(self, name):
        n=name.lower().strip()
        if n in ["tab","the tab","current tab","this tab","website","page","the page"]:
            pyautogui.hotkey('ctrl','w'); return "Closed the current tab."
        exe_list=CLOSE_MAP.get(n)
        if exe_list is None:
            e=BUILTIN_APPS.get(n,f"{name}.exe")
            exe_list=[] if e.endswith(":") else [e]
        killed=False
        for exe in exe_list:
            for p in psutil.process_iter(['name']):
                try:
                    if p.info['name'].lower()==exe.lower(): p.kill(); killed=True
                except: pass
        return f"Closed {name}." if killed else f"Could not find {name} running."

    # Chrome
    def _chrome(self):
        if not self.w.is_running("chrome.exe"):
            path=self.s.find_app("chrome")
            if path: subprocess.Popen(path)
            else:
                try: subprocess.Popen("chrome.exe")
                except: webbrowser.open("https://google.com"); return
            time.sleep(3)
        else: self.w.bring_to_front("Google Chrome")
        time.sleep(0.5)

    def chrome_search(self, q):
        self._chrome(); pyautogui.hotkey('ctrl','t'); time.sleep(0.8)
        pyautogui.hotkey('ctrl','l'); time.sleep(0.5)
        pyperclip.copy(q); pyautogui.hotkey('ctrl','v'); pyautogui.press('enter')
        return f"Searching Google for {q} in Chrome."

    def yt_search_play(self, q):
        self._chrome(); pyautogui.hotkey('ctrl','t'); time.sleep(0.8)
        pyautogui.hotkey('ctrl','l'); time.sleep(0.5)
        pyperclip.copy(f"https://www.youtube.com/results?search_query={q.replace(' ','+')}"); pyautogui.hotkey('ctrl','v'); pyautogui.press('enter')
        time.sleep(5)
        for _ in range(6): pyautogui.press('tab'); time.sleep(0.15)
        pyautogui.press('enter'); time.sleep(2)
        return f"Playing {q} on YouTube."

    def yt_search(self, q):
        self._chrome(); pyautogui.hotkey('ctrl','t'); time.sleep(0.8)
        pyautogui.hotkey('ctrl','l'); time.sleep(0.5)
        pyperclip.copy(f"https://www.youtube.com/results?search_query={q.replace(' ','+')}"); pyautogui.hotkey('ctrl','v'); pyautogui.press('enter')
        return f"Searched YouTube for {q}."

    def yt_open(self):
        self._chrome(); pyautogui.hotkey('ctrl','t'); time.sleep(0.8)
        pyautogui.hotkey('ctrl','l'); time.sleep(0.5)
        pyperclip.copy("https://youtube.com"); pyautogui.hotkey('ctrl','v'); pyautogui.press('enter')
        return "Opening YouTube in Chrome."

    def yt_pp(self): self.w.bring_to_front("YouTube"); time.sleep(0.5); pyautogui.press('k'); return "Toggled play and pause."
    def yt_mute(self): self.w.bring_to_front("YouTube"); time.sleep(0.3); pyautogui.press('m'); return "Toggled mute."
    def yt_fs(self): self.w.bring_to_front("YouTube"); time.sleep(0.3); pyautogui.press('f'); return "Toggled fullscreen."
    def yt_fwd(self): self.w.bring_to_front("YouTube"); time.sleep(0.3); pyautogui.press('l'); return "Skipped 10 seconds forward."
    def yt_back(self): self.w.bring_to_front("YouTube"); time.sleep(0.3); pyautogui.press('j'); return "Went back 10 seconds."
    def yt_next(self): self.w.bring_to_front("YouTube"); time.sleep(0.3); pyautogui.hotkey('shift','n'); return "Playing next video."
    def yt_nth(self, n):
        self.w.bring_to_front("YouTube"); pyautogui.hotkey('alt','left'); time.sleep(2)
        for _ in range(5+((n-1)*6)): pyautogui.press('tab'); time.sleep(0.1)
        pyautogui.press('enter'); return f"Playing video number {n}."

    def scroll_down(self): pyautogui.scroll(-5); return "Scrolled down."
    def scroll_up(self): pyautogui.scroll(5); return "Scrolled up."
    def go_back(self): pyautogui.hotkey('alt','left'); return "Going back."
    def go_fwd(self): pyautogui.hotkey('alt','right'); return "Going forward."
    def refresh(self): pyautogui.hotkey('ctrl','r'); return "Refreshed."
    def new_tab(self): self._chrome(); pyautogui.hotkey('ctrl','t'); return "Opened new tab."
    def close_tab(self): pyautogui.hotkey('ctrl','w'); return "Closed tab."

    # Spotify
    def _spotify(self):
        if not self.w.is_running("Spotify.exe"):
            path=self.s.find_app("spotify")
            if path: subprocess.Popen(path)
            else:
                try: subprocess.Popen("Spotify.exe")
                except: webbrowser.open("https://open.spotify.com"); return False
            time.sleep(5)
        self.w.bring_to_front("Spotify"); time.sleep(0.8); return True

    def sp_play(self, song):
        if not self._spotify(): return f"Spotify not found."
        time.sleep(1); pyautogui.hotkey('ctrl','l'); time.sleep(1.2)
        pyautogui.hotkey('ctrl','a'); time.sleep(0.2)
        pyperclip.copy(song); pyautogui.hotkey('ctrl','v'); time.sleep(0.5)
        pyautogui.press('enter'); time.sleep(3)
        for _ in range(4): pyautogui.press('tab'); time.sleep(0.25)
        pyautogui.press('enter'); return f"Playing {song} on Spotify."

    def sp_search(self, song):
        if not self._spotify(): return "Spotify not found."
        pyautogui.hotkey('ctrl','l'); time.sleep(1.2)
        pyautogui.hotkey('ctrl','a'); time.sleep(0.2)
        pyperclip.copy(song); pyautogui.hotkey('ctrl','v'); time.sleep(0.5)
        pyautogui.press('enter'); return f"Searched Spotify for {song}."

    def sp_pp(self):
        if not self.w.is_running("Spotify.exe"): return "Spotify is not open."
        self.w.bring_to_front("Spotify"); time.sleep(0.5); pyautogui.press('space'); return "Toggled Spotify."

    def sp_next(self): self.w.bring_to_front("Spotify"); time.sleep(0.3); pyautogui.hotkey('ctrl','right'); return "Next song."
    def sp_prev(self): self.w.bring_to_front("Spotify"); time.sleep(0.3); pyautogui.hotkey('ctrl','left'); return "Previous song."

    # WhatsApp
    def _whatsapp(self):
        if not self.w.is_running("WhatsApp.exe"):
            path=self.s.find_app("whatsapp")
            if path:
                try: subprocess.Popen(path); time.sleep(5); return True
                except: pass
            try: subprocess.Popen(["explorer.exe","shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"]); time.sleep(5); return True
            except: pass
            webbrowser.open("https://web.whatsapp.com"); return False
        self.w.bring_to_front("WhatsApp"); time.sleep(1); return True

    def wa_send(self, contact, message):
        if not self._whatsapp(): return f"Opened WhatsApp Web. Please send to {contact} manually."
        time.sleep(2)
        pyautogui.hotkey('ctrl','f'); time.sleep(1.5)
        pyautogui.hotkey('ctrl','a'); pyautogui.press('backspace'); time.sleep(0.3)
        pyperclip.copy(contact); pyautogui.hotkey('ctrl','v'); time.sleep(2.5)
        pyautogui.press('down'); time.sleep(0.5); pyautogui.press('enter'); time.sleep(1.5)
        sw,sh=pyautogui.size()
        pyautogui.click(sw//2, int(sh*0.94)); time.sleep(0.8)
        pyautogui.click(sw//2, int(sh*0.94)); time.sleep(0.5)
        pyperclip.copy(message); pyautogui.hotkey('ctrl','v'); time.sleep(0.5)
        pyautogui.press('enter'); return f"Message sent to {contact} on WhatsApp."

    def wa_chat(self, contact):
        if not self._whatsapp(): return "Opened WhatsApp Web."
        time.sleep(2); pyautogui.hotkey('ctrl','f'); time.sleep(1.5)
        pyautogui.hotkey('ctrl','a'); pyautogui.press('backspace'); time.sleep(0.3)
        pyperclip.copy(contact); pyautogui.hotkey('ctrl','v'); time.sleep(2.5)
        pyautogui.press('down'); time.sleep(0.5); pyautogui.press('enter')
        return f"Opened chat with {contact}."

    def google(self, q): webbrowser.open(f"https://google.com/search?q={q.replace(' ','+')}"); return f"Searching Google for {q}."
    def open_url(self, url):
        if not url.startswith("http"): url="https://"+url
        webbrowser.open(url); return f"Opening {url}."


# ══ COMMAND PROCESSOR ═══════════════════════════
class CommandProcessor:
    def __init__(self, pc):
        self.pc=pc; self.ai=AIBrain()

    def process(self, cmd):
        cmd=cmd.strip().lower()

        # System
        if any(x in cmd for x in ["lock","lock screen","lock laptop"]): return self.pc.lock()
        if any(x in cmd for x in ["cancel shutdown","abort shutdown"]): return self.pc.cancel_shutdown()
        if any(x in cmd for x in ["shutdown","shut down","turn off","power off"]): return self.pc.shutdown()
        if any(x in cmd for x in ["restart","reboot"]): return self.pc.restart()
        if any(x in cmd for x in ["sleep","hibernate"]): return self.pc.sleep()
        if any(x in cmd for x in ["screenshot","take screenshot","capture screen"]): return self.pc.screenshot()
        if any(x in cmd for x in ["volume up","increase volume","louder","turn up"]): return self.pc.vol_up()
        if any(x in cmd for x in ["volume down","decrease volume","quieter","lower volume"]): return self.pc.vol_down()
        if any(x in cmd for x in ["mute","silence"]): return self.pc.mute()
        if any(x in cmd for x in ["system info","pc status","battery","cpu","ram"]): return self.pc.sysinfo()
        if any(x in cmd for x in ["rescan","scan apps","refresh apps","update app list"]): self.pc.s.rescan(); return "Done scanning. I now know all apps and folders on your laptop."

        # Spotify
        if re.search(r"\bopen spotify\b",cmd): self.pc._spotify(); return "Opening Spotify."
        m=re.search(r"play\s+(.+?)\s+(?:on|in)\s+spotify",cmd)
        if m: return self.pc.sp_play(m.group(1).strip())
        m=re.search(r"(?:search|find)\s+(.+?)\s+(?:on|in)\s+spotify",cmd)
        if m: return self.pc.sp_search(m.group(1).strip())
        if any(x in cmd for x in ["next song","next track","skip song"]): return self.pc.sp_next()
        if any(x in cmd for x in ["previous song","prev song","previous track"]): return self.pc.sp_prev()
        if any(x in cmd for x in ["pause music","pause spotify","stop music","resume music","play music"]): return self.pc.sp_pp()

        # YouTube
        if re.search(r"\bopen youtube\b$",cmd) or cmd.strip()=="youtube": return self.pc.yt_open()
        # "open youtube and search X and play" / "play X on youtube"
        m=re.search(r"(?:open youtube.*?search\s+(?:for\s+)?|play\s+)(.+?)(?:\s+on youtube|\s+and play|$)",cmd)
        if m and ("youtube" in cmd or cmd.split()[0]=="play"):
            q=re.sub(r"\s*(on|in)\s*youtube\s*$","",m.group(1)).strip()
            if q: return self.pc.yt_search_play(q)
        m=re.search(r"(?:search|find)\s+(.+?)\s+on\s+youtube",cmd)
        if m: return self.pc.yt_search(m.group(1).strip())
        if any(x in cmd for x in ["pause video","pause the video","play video","resume video","stop video","pause youtube"]): return self.pc.yt_pp()
        if any(x in cmd for x in ["mute video","mute youtube"]): return self.pc.yt_mute()
        if any(x in cmd for x in ["fullscreen","full screen"]): return self.pc.yt_fs()
        if any(x in cmd for x in ["skip forward","forward 10"]): return self.pc.yt_fwd()
        if any(x in cmd for x in ["skip back","rewind","go back 10"]): return self.pc.yt_back()
        if any(x in cmd for x in ["next video","skip video"]): return self.pc.yt_next()
        m=re.search(r"play\s+(?:the\s+)?(\w+)(?:st|nd|rd|th)?\s+video",cmd)
        if m:
            wn={"first":1,"second":2,"third":3,"fourth":4,"fifth":5,"1":1,"2":2,"3":3,"4":4,"5":5}
            return self.pc.yt_nth(wn.get(m.group(1).lower(),1))

        # WhatsApp
        m=re.search(r"(?:send(?:\s+a)?\s+(?:message|msg|whatsapp)(?:\s+to)?\s+([a-zA-Z]+)|(?:whatsapp|message|text)\s+([a-zA-Z]+))\s+(?:saying|say|tell|that|:)\s+(.+)",cmd)
        if m:
            c=(m.group(1) or m.group(2)).strip(); msg=m.group(3).strip()
            return self.pc.wa_send(c,msg)
        m=re.search(r"open\s+(?:whatsapp\s+)?chat\s+(?:with|to)\s+([a-zA-Z]+)",cmd)
        if m: return self.pc.wa_chat(m.group(1).strip())

        # Browser controls
        if any(x in cmd for x in ["go back","previous page"]): return self.pc.go_back()
        if any(x in cmd for x in ["go forward","next page"]): return self.pc.go_fwd()
        if any(x in cmd for x in ["refresh","reload"]): return self.pc.refresh()
        if any(x in cmd for x in ["new tab","open new tab"]): return self.pc.new_tab()
        if any(x in cmd for x in ["close tab","close this tab"]): return self.pc.close_tab()
        if any(x in cmd for x in ["scroll down","go down"]): return self.pc.scroll_down()
        if any(x in cmd for x in ["scroll up","go up"]): return self.pc.scroll_up()
        m=re.search(r"(?:search on chrome|chrome search|open chrome and search|search in chrome)\s+(.+)",cmd)
        if m: return self.pc.chrome_search(m.group(1).strip())

        # Close
        m=re.search(r"close\s+(.+)",cmd)
        if m: return self.pc.close_app(m.group(1).strip())

        # Open folder
        m=re.search(r"open\s+(?:my\s+|the\s+)?(.+?)\s+folder",cmd)
        if m: return self.pc.open_folder(m.group(1).strip())
        m=re.search(r"(?:go to|navigate to|show)\s+(.+?)\s+folder",cmd)
        if m: return self.pc.open_folder(m.group(1).strip())

        # Open file (by extension)
        m=re.search(r"open\s+(.+\.(?:pdf|docx?|xlsx?|pptx?|txt|mp3|mp4|jpg|png))",cmd)
        if m: return self.pc.open_file(m.group(1).strip())

        # Open + search
        m=re.search(r"open\s+(.+?)\s+and\s+(?:search|find)\s+(?:for\s+)?(.+)",cmd)
        if m:
            r=self.pc.open_app(m.group(1).strip()); time.sleep(2)
            self.pc.google(m.group(2).strip()); return r+f" Searching for {m.group(2).strip()}."

        # Open anything (app/folder/file — smart detect)
        m=re.search(r"open\s+(.+)",cmd)
        if m:
            name=m.group(1).strip()
            for w in [" the "," app"," application"," please"," folder"]:
                name=name.replace(w,"").strip()
            # Try app first
            if self.pc.s.find_app(name): return self.pc.open_app(name)
            # Try folder
            if self.pc.s.find_folder(name): return self.pc.open_folder(name)
            # Try file
            if self.pc.s.find_file(name): return self.pc.open_file(name)
            # Default
            return self.pc.open_app(name)

        # Google search
        m=re.search(r"(?:search|google|look up|find)\s+(?:for\s+)?(.+?)(?:\s+on\s+google)?$",cmd)
        if m and "youtube" not in cmd and "spotify" not in cmd:
            return self.pc.google(m.group(1).strip())

        # Website
        m=re.search(r"(?:go to|visit|open)\s+([\w.-]+\.(?:com|org|net|in|io|co|edu))",cmd)
        if m: return self.pc.open_url(m.group(1))

        # Time/date
        if "time" in cmd: return f"It is {datetime.datetime.now().strftime('%I:%M %p')}."
        if any(x in cmd for x in ["date","today","what day"]): return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

        # Greeting
        if any(x in cmd for x in ["hello","hi","hey","good morning","good evening","good afternoon"]):
            h=datetime.datetime.now().hour
            g="Good morning" if h<12 else "Good afternoon" if h<17 else "Good evening"
            return f"{g}! I am Laksh. How can I help you?"

        # Exit
        if any(x in cmd for x in ["stop laksh","exit laksh","quit laksh","goodbye","bye laksh","turn off laksh"]): return "QUIT"

        return self.ai.ask(cmd)


# ══ STARTUP MANAGER ═════════════════════════════
def install_startup():
    try:
        sp=os.path.abspath(__file__); py=sys.executable
        vbs=os.path.join(os.path.dirname(sp),"laksh_start.vbs")
        with open(vbs,"w") as f:
            f.write(f'Set s=CreateObject("WScript.Shell")\ns.Run """{py}"" ""{sp}""",0,False\n')
        key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key,"LAKSH",0,winreg.REG_SZ,f'wscript.exe "{vbs}"')
        winreg.CloseKey(key)
        sf=os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup")
        import shutil; shutil.copy(vbs, os.path.join(sf,"LAKSH.vbs"))
        print("  LAKSH added to startup — will run automatically on every boot!")
        return True
    except Exception as e: print(f"  [Startup error: {e}]"); return False

def is_startup_installed():
    try:
        k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_READ)
        winreg.QueryValueEx(k,"LAKSH"); winreg.CloseKey(k); return True
    except: return False

def remove_startup():
    try:
        k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
        winreg.DeleteValue(k,"LAKSH"); winreg.CloseKey(k)
    except: pass
    sf=os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\LAKSH.vbs")
    if os.path.exists(sf): os.remove(sf)
    print("  LAKSH removed from startup.")


# ══ MAIN ════════════════════════════════════════
class LakshAssistant:
    def __init__(self):
        print("\n"+"═"*54)
        print("   LAKSH — Complete AI Voice Assistant  v4.0")
        print("   Scans ALL apps. Auto-starts on boot.")
        print("   Say 'bye Laksh' to stop")
        print("═"*54+"\n")
        self.scanner=SystemScanner()
        self.voice=VoiceEngine()
        self.speech=SpeechEngine()
        self.pc=PCController(self.scanner)
        self.processor=CommandProcessor(self.pc)
        if not is_startup_installed():
            print("  [First run — adding to Windows startup...]")
            install_startup()

    def start(self):
        self.voice.speak("Hello! I am Laksh, your personal AI assistant. I am always listening and can control everything on your laptop. Just speak!")
        while True:
            try:
                print("  [LISTENING...]",end="\r")
                cmd=self.speech.listen()
                if not cmd: continue
                resp=self.processor.process(cmd)
                if resp=="QUIT":
                    self.voice.speak("Goodbye! I will start again when you restart your laptop.")
                    break
                if resp: self.voice.speak(resp)
                time.sleep(0.5)
            except KeyboardInterrupt:
                self.voice.speak("Stopping now."); break
            except Exception as e:
                print(f"  [Error: {e}]"); time.sleep(0.5)

if __name__=="__main__":
    if len(sys.argv)>1:
        if sys.argv[1]=="--remove-startup": remove_startup(); sys.exit()
        if sys.argv[1]=="--install-startup": install_startup(); sys.exit()
    LakshAssistant().start()
