#!/usr/bin/env python3
"""构建脚本 - 使用 PyInstaller --icon 参数正确打包"""

import subprocess
import sys
import shutil
from pathlib import Path

VERSION = "1.0.3"
APP_NAME = "ZZZ_PrtSc"


def main():
    print(f"=== Building {APP_NAME} v{VERSION} ===")

    project_root = Path(__file__).parent.resolve()
    icon_path = project_root / "app_icon.ico"
    png_icon_path = project_root / "app_icon.png"

    if not icon_path.exists():
        if png_icon_path.exists():
            print("Generating ICO from PNG...")
            from make_ico import png_to_ico
            png_to_ico(str(png_icon_path), str(icon_path))
        else:
            print("Error: app_icon.ico and app_icon.png not found")
            return 1

    for dir_name in ['build', 'dist']:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"Cleaned: {dir_name}/")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", f"{APP_NAME}_{VERSION}",
        "--onefile",
        "--windowed",
        "--icon", str(icon_path),
        "--add-data", f"{icon_path};.",
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32process",
        "--hidden-import", "win32clipboard",
        "--hidden-import", "win32com.client",
        "--collect-all", "customtkinter",
        "--exclude-module", "numpy",
        "--exclude-module", "pyreadline3",
        "--exclude-module", "adodbapi",
        "--exclude-module", "psutil",
        "--exclude-module", "PIL.ImageShow",
        "--exclude-module", "PIL.ImageQt",
        "--clean",
        str(project_root / "main.py"),
    ]

    print(f"\nExecuting PyInstaller...")
    result = subprocess.run(cmd, cwd=str(project_root))

    if result.returncode != 0:
        print(f"Build failed! Exit code: {result.returncode}")
        return 1

    exe_path = project_root / "dist" / f"{APP_NAME}_{VERSION}.exe"
    if not exe_path.exists():
        print(f"Error: EXE not found: {exe_path}")
        return 1

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\nBuild complete: {exe_path}")
    print(f"Size: {size_mb:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
