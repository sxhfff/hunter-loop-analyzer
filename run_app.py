import subprocess
import sys
from pathlib import Path
import socket


def find_free_port(start=8501, end=8599):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("没有找到可用端口。")


def main():
    if getattr(sys, "frozen", False):
        project_root = Path(sys._MEIPASS)
    else:
        project_root = Path(__file__).resolve().parent

    app_path = project_root / "ui" / "app.py"
    if not app_path.exists():
        raise FileNotFoundError(f"找不到 ui/app.py: {app_path}")

    port = find_free_port()

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ],
        cwd=str(project_root),
    )

    print(f"程序已启动，请手动打开：http://127.0.0.1:{port}")
    input("按回车键退出启动器...")


if __name__ == "__main__":
    main()