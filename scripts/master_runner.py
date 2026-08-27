# -*- coding: utf-8 -*-
"""
Project BUKI - Master Service Launcher & Live Health Dashboard
Manages Ollama, GPT-SoVITS, Chatterbox, and FastAPI Server in one unified process.
"""
import os
import sys
import time
import subprocess
import threading
import urllib.request
import socket
from pathlib import Path

# Fix Windows console UTF-8 output
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).parent.parent
OPENDCMART_ROOT = PROJECT_ROOT.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Service Definitions
SERVICES = {
    "ollama": {
        "name": "🤖 Ollama Local LLM",
        "port": 11434,
        "health_url": "http://127.0.0.1:11434/api/tags",
        "cwd": OPENDCMART_ROOT,
        "cmd": ["C:\\Users\\rerun\\AppData\\Local\\Programs\\Ollama\\ollama.exe", "serve"],
        "log": LOGS_DIR / "ollama.log",
        "process": None
    },
    "gpt_sovits": {
        "name": "🎙️ GPT-SoVITS Zero-Shot TTS",
        "port": 9880,
        "health_url": "http://127.0.0.1:9880/",
        "cwd": OPENDCMART_ROOT / "tools" / "GPT-SoVITS",
        "cmd": ["C:\\Users\\rerun\\AppData\\Local\\hermes\\bin\\uv.exe", "run", "python", "run_server.py"],
        "log": LOGS_DIR / "gpt_sovits.log",
        "process": None
    },
    "chatterbox": {
        "name": "🎭 Chatterbox 0.5B TTS",
        "port": 9882,
        "health_url": "http://127.0.0.1:9882/health",
        "cwd": OPENDCMART_ROOT / "tools" / "Chatterbox-TTS",
        "cmd": ["C:\\Users\\rerun\\AppData\\Local\\hermes\\bin\\uv.exe", "run", "python", "run_server.py"],
        "log": LOGS_DIR / "chatterbox.log",
        "process": None
    },
    "buki_server": {
        "name": "⚡ BUKI Web & API Server",
        "port": 8000,
        "health_url": "http://127.0.0.1:8000/api/info",
        "cwd": PROJECT_ROOT / "src" / "backend",
        "cmd": ["C:\\Python314\\python.exe", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"],
        "log": LOGS_DIR / "buki_server.log",
        "process": None
    }
}

RUNNING = True

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0

def check_service_health(service_key: str) -> bool:
    cfg = SERVICES[service_key]
    url = cfg["health_url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BUKI-Monitor"})
        with urllib.request.urlopen(req, timeout=1.5) as res:
            return res.status in [200, 404, 405]
    except Exception:
        return False

def start_service(service_key: str):
    cfg = SERVICES[service_key]
    if is_port_in_use(cfg["port"]):
        return

    log_file = open(cfg["log"], "a", encoding="utf-8")
    log_file.write(f"\n\n=== [{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting {cfg['name']} ===\n")
    log_file.flush()

    try:
        proc = subprocess.Popen(
            cfg["cmd"],
            cwd=str(cfg["cwd"]),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        cfg["process"] = proc
    except Exception as e:
        print(f"❌ Error starting {cfg['name']}: {e}")

def stop_service(service_key: str):
    cfg = SERVICES[service_key]
    port = cfg["port"]
    
    if cfg["process"] and cfg["process"].poll() is None:
        try:
            cfg["process"].terminate()
        except Exception:
            pass

    if os.name == "nt":
        kill_cmd = f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"
        subprocess.run(["powershell", "-NoProfile", "-Command", kill_cmd], capture_output=True)

def start_all():
    for key in ["ollama", "gpt_sovits", "chatterbox", "buki_server"]:
        start_service(key)

def stop_all():
    global RUNNING
    RUNNING = False
    print("\n🛑 Shutting down all Project BUKI background services...")
    for key in ["buki_server", "chatterbox", "gpt_sovits"]:
        stop_service(key)
    print("✅ All services stopped safely.")

def get_tailscale_ip() -> str:
    try:
        res = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "100.124.66.37"

def display_dashboard():
    tailscale_ip = get_tailscale_ip()
    while RUNNING:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 68)
        print(" 🔮 PROJECT BUKI - MASTER SERVICE & HEALTH DASHBOARD")
        print("=" * 68)
        print(f" 🌐 로컬 접속 주소:     http://localhost:8000")
        print(f" 📱 모바일/테일스케일:   http://{tailscale_ip}:8000")
        print(f" 📁 로그 파일 저장소:   {LOGS_DIR}")
        print("-" * 68)
        print("  서비스명                       포트    실시간 상태      로그 위치")
        print("-" * 68)

        for key, cfg in SERVICES.items():
            port = cfg["port"]
            alive = check_service_health(key)
            status_text = "🟢 ONLINE  " if alive else "🔴 OFFLINE "
            log_name = cfg["log"].name
            print(f"  {cfg['name']:<30} {port:<7} {status_text:<15} logs/{log_name}")

        print("-" * 68)
        print(" [1] 🌐 브라우저 열기 (Web UI)        [R] 🔄 전체 서비스 재시작")
        print(" [2] 📄 BUKI 웹서버 로그 보기         [3] 🎙️ GPT-SoVITS 로그 보기")
        print(" [4] 🎭 Chatterbox 로그 보기          [Q] 🛑 전체 종료 및 나가기")
        print("=" * 68)
        print(" 💡 3초마다 상태가 자동 갱신됩니다. 원하시는 명령 번호를 입력하세요: ", end="", flush=True)

        for _ in range(6):
            if not RUNNING:
                break
            time.sleep(0.5)

def user_input_loop():
    while RUNNING:
        try:
            cmd = input().strip().lower()
            if cmd == "q":
                stop_all()
                sys.exit(0)
            elif cmd == "r":
                print("\n🔄 Restarting all services...")
                for k in ["buki_server", "chatterbox", "gpt_sovits"]:
                    stop_service(k)
                time.sleep(1)
                start_all()
            elif cmd == "1":
                if os.name == "nt":
                    os.system("start http://localhost:8000")
            elif cmd == "2":
                if os.name == "nt":
                    os.system(f"start powershell -NoExit -Command \"Get-Content -Path '{SERVICES['buki_server']['log']}' -Wait -Tail 30\"")
            elif cmd == "3":
                if os.name == "nt":
                    os.system(f"start powershell -NoExit -Command \"Get-Content -Path '{SERVICES['gpt_sovits']['log']}' -Wait -Tail 30\"")
            elif cmd == "4":
                if os.name == "nt":
                    os.system(f"start powershell -NoExit -Command \"Get-Content -Path '{SERVICES['chatterbox']['log']}' -Wait -Tail 30\"")
        except (EOFError, KeyboardInterrupt):
            stop_all()
            break

if __name__ == "__main__":
    print("🚀 Initializing Project BUKI Master Services...")
    start_all()
    
    t_dash = threading.Thread(target=display_dashboard, daemon=True)
    t_dash.start()
    
    try:
        user_input_loop()
    except KeyboardInterrupt:
        stop_all()