import os
import shlex
import subprocess
import sys
from typing import List, Tuple, Optional, Union
import shutil

CREATE_NEW_CONSOLE = 0x00000010

def windows_to_wsl(path: str) -> str:
    path = os.path.abspath(path)
    if path.startswith("/"):
        return path
    # handle normal windows drive paths
    drive = path[0].lower()
    rest = path[2:].replace("\\", "/")
    return f" '/mnt/{drive}/{rest}'"

def windows_to_wsl_quote(sources: List[str]) -> str:
    quoted = ""

    for path in sources:
        sub = windows_to_wsl(path)
        quoted += " " + sub + ("'/'*.cpp " if os.path.isdir(path) else " ")
    return quoted

# def run_wsl_command(cmd: str, distro: Optional[str] = None, capture: bool = False) -> subprocess.CompletedProcess:
#     """
#     Helper to run a bash -lc "<cmd>" inside WSL.
#     If capture True, returns CompletedProcess with stdout/stderr captured as text.
#     """
#     wsl_cmd = ["wsl.exe"]
#     if distro:
#         wsl_cmd += ["-d", distro]
#     wsl_cmd += ["--", "bash", "-lc", cmd]
#     if capture:
#         return subprocess.run(wsl_cmd, text=True, capture_output=True)
#     else:
#         return subprocess.run(wsl_cmd)

def run_wsl_command(
        cmd: str,
        distro: Optional[str] = None,
        capture: bool = False,
        keep_open: Optional[str] = None,  # None | "shell" | "pause"
) -> Union[subprocess.CompletedProcess, subprocess.Popen]:
    """
    Run a WSL command.

    - capture=True: run in-process and return CompletedProcess (stdout/stderr captured).
    - capture=False: open a new terminal window running the command.
    - keep_open:
        - None (default): close when command finishes.
        - "shell": after the cmd finishes, start an interactive bash in that window.
        - "pause": after the cmd finishes, prompt "Press any key to exit..." and wait.

    Notes:
    - With the "start" fallback (cmd.exe /c start) the returned Popen usually refers
      to the short-lived cmd.exe wrapper. If you need to reliably wait for the
      window to close, prefer Windows Terminal (wt.exe) or use keep_open to create
      a long-lived process inside the terminal.
    """
    if keep_open == "shell":
        wrapped_cmd = f'{cmd}; echo; exec bash'
    elif keep_open == "pause":
        wrapped_cmd = f'{cmd}; echo; read -n1 -r -p "Press any key to exit..."'
    else:
        wrapped_cmd = cmd

    # WSL command base
    wsl_base = ["wsl.exe"]
    if distro:
        wsl_base += ["-d", distro]
    wsl_base += ["--", "bash", "-lc", wrapped_cmd]

    if capture:
        # same behavior as before
        return subprocess.run(wsl_base, text=True, capture_output=True)

    # Non-capture: open a new terminal window
    wt_path = shutil.which("wt.exe") or shutil.which("wt")
    if wt_path:
        # Windows Terminal: spawn wsl; WT usually spawns the window and returns quickly,
        # but the shell inside the window will remain if we used keep_open.
        wt_args = [wt_path, "wsl"]
        if distro:
            wt_args += ["-d", distro]
        wt_args += ["--", "bash", "-lc", wrapped_cmd]
        return subprocess.Popen(wt_args, close_fds=True)

    # Fallback: cmd.exe /c start "" wsl.exe ...  (start opens a new window)
    start_args = ["cmd.exe", "/c", "start", "", "wsl.exe"]
    if distro:
        start_args += ["-d", distro]
    start_args += ["--", "bash", "-lc", wrapped_cmd]
    # Note: Popen here refers to the short-lived cmd.exe process (it returns immediately).
    return subprocess.Popen(start_args, shell=False, close_fds=True)

def compile_in_wsl(sources: List[str],
                   distro: Optional[str] = None,
                   root_path="/",
                   custom_options=None,
                   language_standard=None,
                   executable_name=None
                   ) -> Tuple[bool, str]:
    """
    Compile the given source files in WSL via g++.
    - sources: list of Windows paths OR WSL paths to .cpp files
    - output_binary_wsl: if provided, should be a WSL path for the produced executable (e.g. /home/user/prog)
                         If None, produced binary will be next to first source with name a.out or <basename>.
    Returns: (success, wsl_path_of_binary). Compilation stdout+stderr is printed and returned via console.
    """
    srcs_quoted = windows_to_wsl_quote(sources)
    # cmd = f"g++ {extra_flags} -o {shlex.quote(wsl_bin)} {srcs_quoted}"
    options_str = ""
    if custom_options is not None:
        options_str += " -O2 " if custom_options["Optimize"].get() else ""
        options_str += " -Wall " if custom_options["Warn All"].get() else ""
        options_str += " -g " if custom_options["Debug info"].get() else ""
        options_str += " -Werror " if custom_options["Warnings as errors"].get() else ""
        options_str += " -static " if custom_options["Link static"].get() else ""
    lang_std_str = f" -std={language_standard} " if language_standard is not None else ""
    if executable_name is None:
        executable_name = "a.out"

    cmd = f"cd {root_path} && g++ {options_str} {lang_std_str} -IHeaders -ISources {srcs_quoted} -o {executable_name}"
    print("Compiling inside WSL: ", cmd)
    cp = run_wsl_command(cmd, distro=distro, capture=False, keep_open="pause")
    print("--- compile stdout/stderr ---")
    print(cp.stdout, cp.stderr)
    success = (cp.returncode == 0)
    return success  #, wsl_bin

def check_script_installed(distro: Optional[str] = None) -> bool:
    """Return True if `script` is present in the target WSL distro."""
    cp = run_wsl_command("command -v script >/dev/null 2>&1 && echo OK || echo MISSING", distro=distro, capture=True)
    return "OK" in cp.stdout

def run_interactive_in_new_console(binary_wsl_path: str,
                                   recording_windows_path: str,
                                   distro: Optional[str] = None):
    """
    Launch the compiled binary inside WSL, in a NEW Windows console window, attached to a pty via `script`.
    The interactive transcript will be saved to recording_windows_path (Windows absolute).
    """
    # normalize recording path and convert to WSL
    recording_windows_path = os.path.abspath(recording_windows_path)
    wsl_record = windows_to_wsl(recording_windows_path)

    # make sure binary path is quoted for safe shell usage
    binary_quoted = shlex.quote(binary_wsl_path)
    record_quoted = shlex.quote(wsl_record)

    # Use `script -q -f <file> -c "<binary>"` so the child sees a pty and we capture the session.
    # After the program exits, present a "Press any key to close..." prompt so the console stays open.
    bash_inner = f'script -q -f {record_quoted} -c {binary_quoted}; echo; read -n1 -s -r -p "Press any key to close..."'

    # Build the wsl.exe invocation
    wsl_cmd = ["wsl.exe"]
    if distro:
        wsl_cmd += ["-d", distro]
    wsl_cmd += ["--", "bash", "-lc", bash_inner]

    print("Launching interactive session in a NEW console window.")
    print("Recording path (Windows):", recording_windows_path)
    # Start new console so the user sees a separate interactive window
    proc = subprocess.Popen(wsl_cmd, creationflags=CREATE_NEW_CONSOLE)
    proc.wait()
    print("Interactive session ended. Recording saved to:", recording_windows_path)

def fallback_run_without_script(binary_wsl_path: str, distro: Optional[str] = None):
    """
    If 'script' is not available, fall back to launching the WSL binary in a new console without recording.
    (It will still be interactive.)
    """
    bash_inner = f'{shlex.quote(binary_wsl_path)}; echo; read -n1 -s -r -p "Press any key to close..."'
    wsl_cmd = ["wsl.exe"]
    if distro:
        wsl_cmd += ["-d", distro]
    wsl_cmd += ["--", "bash", "-lc", bash_inner]
    print("`script` not found in WSL. Launching interactive session WITHOUT recording.")
    proc = subprocess.Popen(wsl_cmd, creationflags=CREATE_NEW_CONSOLE)
    proc.wait()

if __name__ == "__main__":
    # Example usage:
    # Suppose your project files are in C:\Users\You\projects\myprog\main.cpp and helper.cpp
    # Provide Windows paths below:
    cpp_files = [
        r"C:\projs\COMP345-warzone-a1\Sources",
    ]

    # Where to put the final recording on Windows:
    recording_out = r"C:\projs\NoPaste\session_record.txt"

    # Optional: specify target distro name (otherwise default distro is used)
    distro_name = None  # e.g. "Ubuntu-22.04"

    # ok, wsl_bin = compile_in_wsl(cpp_files, output_binary_wsl=None, distro=distro_name)
    ok = compile_in_wsl(cpp_files, output_binary_wsl=None, distro=distro_name)
    if not ok:
        print("Compilation failed; fix errors then re-run.")
        sys.exit(1)

    # Make sure 'script' exists; if not, either ask user to install util-linux or fall back
    if check_script_installed(distro=distro_name):
        run_interactive_in_new_console("/", recording_out, distro=distro_name)  # used to have wsl_bin instead of "/"
    else:
        print("`script` not found in WSL. You can install it with e.g. 'sudo apt install util-linux' (Debian/Ubuntu).")
        # fallback (no recording)
        fallback_run_without_script("/", distro=distro_name)  # used to have wsl_bin instead of "/"
