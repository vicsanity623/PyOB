import platform
import subprocess
from pathlib import Path


def main():
    os_name = platform.system().lower()
    project_root = Path(__file__).parent.absolute()

    print(f"🚀 Building NoClaw for {os_name}...")

    # Base configuration for all platforms
    common = [
        "--name=NoClaw",
        "--clean",
        "--noconfirm",
        "--hidden-import=autoreviewer",
        "--hidden-import=core_utils",
        "--hidden-import=prompts_and_memory",
        "--hidden-import=requests",
        "--hidden-import=ollama",
        "--collect-all=ruff",
        "--collect-all=mypy",
        "--collect-all=ollama",
        "noclaw_launcher.py",
    ]

    if os_name == "darwin":
        # macOS: Create a .app bundle (--windowed) for Spotlight/Icon support
        cmd = (
            ["pyinstaller"]
            + common
            + [
                "--windowed",
                "--icon=no-claw.icns",
            ]
        )
        dist_output = project_root / "dist" / "NoClaw.app"

    elif os_name == "windows":
        # Windows: Create a single .exe
        cmd = (
            ["pyinstaller"]
            + common
            + [
                "--onefile",
                "--console",
                "--icon=no-claw.ico",  # Usually .ico for Windows
            ]
        )
        dist_output = project_root / "dist" / "NoClaw.exe"

    else:
        # Linux: Create a single binary
        cmd = ["pyinstaller"] + common + ["--onefile", "--console"]
        dist_output = project_root / "dist" / "NoClaw"

    # --- Step 1: Run PyInstaller ---
    print("🛠️  Running PyInstaller...")
    subprocess.run(cmd, check=True)
    print(f"\n✅ PyInstaller Build complete: {dist_output}")

    # --- Step 2: macOS Specific DMG Packaging ---
    if os_name == "darwin":
        print("\n📦 Starting DMG creation...")

        dmg_name = "NoClaw-v0.1.2.dmg"
        dmg_path = project_root / dmg_name

        # Remove old DMG if it exists
        if dmg_path.exists():
            dmg_path.unlink()

        # create-dmg command
        # We point directly to the NoClaw.app bundle
        dmg_cmd = [
            "create-dmg",
            "--volname",
            "NoClaw Installer",
            "--app-drop-link",
            "400",
            "120",
            "--window-size",
            "600",
            "400",
            "--icon-size",
            "100",
            "--icon",
            "NoClaw.app",
            "150",
            "120",
            str(dmg_path),
            str(dist_output),
        ]

        try:
            subprocess.run(dmg_cmd, check=True)
            print(f"\n🔥 SUCCESS! DMG created at: {dmg_path}")
            print(
                "You can now distribute the DMG. Users can drag NoClaw to Applications."
            )
        except FileNotFoundError:
            print("\n❌ Error: 'create-dmg' not found.")
            print("Fix: brew install create-dmg")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error creating DMG: {e}")


if __name__ == "__main__":
    main()
