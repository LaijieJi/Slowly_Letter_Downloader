import cx_Freeze
import sys
import os

dir_path = os.getcwd()
interface_path = os.path.join(dir_path, "interface")

base = None

if sys.platform == 'win32':
    base = 'Win32GUI'

options = {"build_exe": {
    "packages": [
        "os",
        "re",
        "json",
        "time",
        "logging",
        "threading",
        "playwright",
        "pdfrw",
        "customtkinter",
        "tkinter",
        "pyglet",
        "PIL",
    ],
    "include_files": [
        "interface",
        "utils.py",
        "browser.py",
    ],
    "excludes": [
        "numpy",
        "pandas",
    ],
}}

executables = [cx_Freeze.Executable(
    "main.py",
    base=base,
    target_name="SLD",
    icon=os.path.join(interface_path, "SLD_icon.ico"),
)]

cx_Freeze.setup(
    name="Slowly Letter Downloader",
    options=options,
    author="PastaSource",
    version="0.3",
    description="Automates the downloading of letters from Slowly",
    python_requires=">=3.12",
    executables=executables,
)
