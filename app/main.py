import os
import sys
import subprocess


def main():
    builtins = ["echo", "exit", "type", "pwd", "cd"]

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            command = input()
        except EOFError:
            break

        parts = command.split()

        if not parts:
            continue

        name = parts[0]
        args = parts[1:]

        if name == "exit":
            break

        elif name == "pwd":
            print(os.getcwd())

        elif name == "cd":
            if not args:
                continue

            directory = args[0]

            try:
                os.chdir(directory)
            except OSError:
                print(f"cd: {directory}: No such file or directory")

        elif name == "echo":
            print(command[5:] if command.startswith("echo ") else "")

        elif name == "type":
            if not args:
                print("type: not found")
                continue

            target = args[0]

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
            executable = None

            for directory in os.environ.get("PATH", "").split(os.pathsep):
                path = os.path.join(directory, name)

                if os.path.isfile(path) and os.access(path, os.X_OK):
                    executable = path
                    break

            if executable:
                try:
                    subprocess.run([name] + args, executable=executable)
                except OSError:
                    print(f"{name}: command not found")
            else:
                print(f"{name}: command not found")


if __name__ == "__main__":
    main()