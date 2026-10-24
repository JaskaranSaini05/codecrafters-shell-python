
import os
import sys


def main():
    builtins = ["echo", "exit", "type"]

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        command = input()
        parts = command.split()

        if not parts:
            continue

        name = parts[0]

        if name == "exit":
            break
        elif name == "echo":
            print(command[5:] if command.startswith("echo ") else "")
        elif name == "type":
            if len(parts) < 2:
                print("type: not found")
                continue

            target = parts[1]

            if target in builtins:
                print(f"{target} is a shell builtin")
            else:
                found = None

                for directory in os.environ.get("PATH", "").split(os.pathsep):
                    path = os.path.join(directory, target)

                    if os.path.isfile(path) and os.access(path, os.X_OK):
                        found = path
                        break

                if found:
                    print(f"{target} is {found}")
                else:
                    print(f"{target}: not found")
        else:
            print(f"{name}: command not found")


if __name__ == "__main__":
    main()
