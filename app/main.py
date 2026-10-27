import os
import sys
import subprocess
import readline

BUILTINS = ["echo", "exit", "type", "pwd", "cd"]


def parse_command(command):
    args = []
    current = []
    quote = None
    i = 0
    started = False

    while i < len(command):
        char = command[i]

        if quote == "'":
            if char == "'":
                quote = None
            else:
                current.append(char)
            started = True

        elif quote == '"':
            if char == '"':
                quote = None
            elif char == "\\":
                if i + 1 < len(command) and command[i + 1] in ['"', '\\']:
                    i += 1
                    current.append(command[i])
                else:
                    current.append(char)
            else:
                current.append(char)
            started = True

        else:
            if char in ("'", '"'):
                quote = char
                started = True

            elif char == "\\":
                if i + 1 < len(command):
                    i += 1
                    current.append(command[i])
                started = True

            elif command[i:i + 3] in ("1>>", "2>>"):
                if started:
                    args.append("".join(current))
                    current = []
                    started = False
                args.append(command[i:i + 3])
                i += 2

            elif command[i:i + 2] == ">>":
                if started:
                    args.append("".join(current))
                    current = []
                    started = False
                args.append(">>")
                i += 1

            elif command[i:i + 2] in ("1>", "2>"):
                if started:
                    args.append("".join(current))
                    current = []
                    started = False
                args.append(command[i:i + 2])
                i += 1

            elif char == ">":
                if started:
                    args.append("".join(current))
                    current = []
                    started = False
                args.append(">")

            elif char.isspace():
                if started:
                    args.append("".join(current))
                    current = []
                    started = False

            else:
                current.append(char)
                started = True

        i += 1

    if started:
        args.append("".join(current))

    return args


def find_executable(name):
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            directory = "."

        path = os.path.join(directory, name)

        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def get_completions(text):
    matches = set()

    for command in BUILTINS:
        if command.startswith(text):
            matches.add(command)

    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            directory = "."

        try:
            for filename in os.listdir(directory):
                if not filename.startswith(text):
                    continue

                path = os.path.join(directory, filename)

                if os.path.isfile(path) and os.access(path, os.X_OK):
                    matches.add(filename)
        except OSError:
            continue

    return sorted(matches)


def get_filename_completions(text):
    if "/" in text:
        directory, prefix = text.rsplit("/", 1)
        search_directory = directory if directory else "/"
    else:
        prefix = text
        search_directory = "."

    try:
        entries = sorted(
            name for name in os.listdir(search_directory)
            if name.startswith(prefix)
        )
    except OSError:
        return []

    matches = []

    for entry in entries:
        full_path = os.path.join(search_directory, entry)

        if os.path.isdir(full_path):
            matches.append(entry + "/")
        else:
            matches.append(entry)

    return matches


def completer(text, state):
    if state == 0:
        line = readline.get_line_buffer()
        end_index = readline.get_endidx()
        before_cursor = line[:end_index]
        last_space = before_cursor.rfind(" ")

        if last_space != -1:
            prefix = before_cursor[last_space + 1:]
            matches = get_filename_completions(prefix)
        elif "/" in text:
            matches = get_filename_completions(text)
        else:
            matches = get_completions(text)

        completer.matches = matches

        if not matches:
            completer.tab_pressed = False
            sys.stdout.write("\x07")
            sys.stdout.flush()
        elif len(matches) > 1:
            if getattr(completer, "tab_pressed", False):
                completer.tab_pressed = False
                sys.stdout.write("\n")
                sys.stdout.write("  ".join(matches))
                sys.stdout.write("\n$ " + line)
                sys.stdout.flush()
                completer.matches = []
            else:
                completer.tab_pressed = True
                sys.stdout.write("\x07")
                sys.stdout.flush()
                completer.matches = []
        else:
            completer.tab_pressed = False
            match = matches[0]

            if not match.endswith("/"):
                match += " "

            completer.matches = [match]

    try:
        return completer.matches[state]
    except (IndexError, AttributeError):
        return None


completer.tab_pressed = False
readline.set_completer(completer)
readline.parse_and_bind("tab: complete")


def main():
    while True:
        try:
            command = input("$ ")
        except EOFError:
            break

        parts = parse_command(command)

        if not parts:
            continue

        output_file = None
        error_file = None
        output_mode = "w"
        error_mode = "w"
        filtered_parts = []
        i = 0

        while i < len(parts):
            operator = parts[i]

            if operator in (">", "1>", ">>", "1>>"):
                if i + 1 < len(parts):
                    output_file = parts[i + 1]
                    output_mode = "a" if operator in (">>", "1>>") else "w"
                    i += 2
                else:
                    i += 1

            elif operator in ("2>", "2>>"):
                if i + 1 < len(parts):
                    error_file = parts[i + 1]
                    error_mode = "a" if operator == "2>>" else "w"
                    i += 2
                else:
                    i += 1

            else:
                filtered_parts.append(parts[i])
                i += 1

        parts = filtered_parts

        if not parts:
            continue

        name = parts[0]
        args = parts[1:]
        output = None
        error_output = None

        try:
            if output_file is not None:
                output = open(output_file, output_mode)

            if error_file is not None:
                error_output = open(error_file, error_mode)

        except OSError:
            if output is not None:
                output.close()
            if error_output is not None:
                error_output.close()
            continue

        stdout_target = output if output is not None else sys.stdout
        stderr_target = error_output if error_output is not None else sys.stderr

        try:
            if name == "exit":
                break

            elif name == "pwd":
                print(os.getcwd(), file=stdout_target)

            elif name == "cd":
                if not args:
                    continue

                directory = args[0]

                if directory == "~":
                    directory = os.environ.get("HOME", "")

                try:
                    os.chdir(directory)
                except OSError:
                    print(
                        f"cd: {args[0]}: No such file or directory",
                        file=stderr_target
                    )

            elif name == "echo":
                print(" ".join(args), file=stdout_target)

            elif name == "type":
                if not args:
                    print("type: not found", file=stdout_target)
                    continue

                target = args[0]

                if target in BUILTINS:
                    print(f"{target} is a shell builtin", file=stdout_target)
                else:
                    found = find_executable(target)

                    if found:
                        print(f"{target} is {found}", file=stdout_target)
                    else:
                        print(f"{target}: not found", file=stdout_target)

            else:
                executable = find_executable(name)

                if executable:
                    try:
                        subprocess.run(
                            [name] + args,
                            executable=executable,
                            stdout=output,
                            stderr=error_output
                        )
                    except OSError:
                        print(f"{name}: command not found", file=stderr_target)
                else:
                    print(f"{name}: command not found", file=stderr_target)

        finally:
            if output is not None:
                output.close()

            if error_output is not None:
                error_output.close()


if __name__ == "__main__":
    main()