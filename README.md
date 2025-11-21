# NoPaste C++ Compiler GUI (wrapper for g++)

## Supported commands

Compilation flags: 
- Optimize:           `-O2`
- Useful Warnings:    `-Wall`
- Debug Info:         `-g`
- Warnings as Errors: `-Werror`
- Link Static:        `-static`

## Execution with Valgrind

Can execute output normally, or with valgrind (only runs with `--leak-check=full` option for now).

## Create an executable

Get it from the **releases**, or create one yourself:
```
pyinstaller --onefile --windowed --icon=skull.ico --add-data "skull.ico;."  run.py
```

<img width="931" height="592" alt="image" src="https://github.com/user-attachments/assets/1c44a06a-bcd2-48cb-a01f-bf1750f44ef3" />
