
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

        if parts[0] == "exit":
            break
        elif parts[0] == "echo":
            print(command[5:] if command.startswith("echo ") else "")
        elif parts[0] == "type":
            if len(parts) > 1:
                name = parts[1]
                if name in builtins:
                    print(f"{name} is a shell builtin")
                else:
                    print(f"{name}: not found")
            else:
                print("type: not found")
        else:
            print(f"{parts[0]}: command not found")


if __name__ == "__main__":
    main()
