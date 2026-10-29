#!/usr/bin/env python3

import subprocess
import sys
import os
import shlex

def parse_output(line):
    tokens = shlex.split(line, posix=os.name != 'nt')
    if os.name == 'nt':
        tokens = [token.strip('"') for token in tokens]
    flash_command_index = next(
        (index for index, token in enumerate(tokens) if token in ('write_flash', 'write-flash')),
        None
    )
    if flash_command_index is None:
        return None

    chip_index = next(
        (index for index, token in enumerate(tokens[:flash_command_index]) if token == '--chip'),
        None
    )
    if chip_index is None or chip_index + 1 >= flash_command_index:
        return None

    chip = tokens[chip_index + 1]
    command_prefix = tokens[:chip_index]
    if not command_prefix:
        return None

    flash_options = []
    option_names = {
        '--flash_mode', '--flash-mode',
        '--flash_freq', '--flash-freq',
        '--flash_size', '--flash-size',
    }
    for index, token in enumerate(tokens):
        if token in option_names and index + 1 < len(tokens):
            flash_options.extend((token, tokens[index + 1]))

    binary_files = []
    index = flash_command_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token in ('-z', '--compress'):
            index += 1
        elif token in option_names:
            index += 2
        elif token.startswith('0x') and index + 1 < len(tokens):
            binary_files.extend((token, tokens[index + 1]))
            index += 2
        else:
            index += 1

    if not binary_files:
        return None

    # Extract the GitHub build number from the environment (assuming it is set)
    github_build_number = os.environ.get('GITHUB_RUN_NUMBER', '00000')
    github_owner_name, github_repo_name = os.environ.get('GITHUB_REPOSITORY', 'user/repo').split('/')

    merge_command = 'merge-bin' if tokens[flash_command_index] == 'write-flash' else 'merge_bin'
    output_file = f'web/firmware/{github_owner_name}_{github_repo_name}_b{github_build_number}_{chip}.bin'
    command = command_prefix + ['--chip', chip, merge_command, '-o', output_file]
    command.extend(flash_options)
    command.extend(binary_files)
    if os.name == 'nt':
        return subprocess.list2cmdline(command)
    return ' '.join(shlex.quote(token) for token in command)

def generate_merge_firmware_command(pio_env=None):
    command = ["pio", "run"]
    
    if pio_env is not None:
        command.extend(["-e", pio_env])

    command.extend(["-v", "-t", "upload", "--upload-port", "/dev/null"])

    try:
        completed_process = subprocess.run(command, capture_output=True, text=True, check=False)
    except subprocess.CalledProcessError as e:
        print(f"Error running pio command: {e}", file=sys.stderr)

    output = completed_process.stdout + completed_process.stderr
    if not output:
        print("No output received from pio command.", file=sys.stderr)
        sys.exit(1)

    relevant_lines = [
        line
        for line in output.splitlines()
        if 'write_flash' in line or 'write-flash' in line
    ]

    if not relevant_lines:
        print(output, file=sys.stderr)
        print("No relevant lines found in the output.", file=sys.stderr)
        sys.exit(1)

    for line in relevant_lines:
        new_command = parse_output(line)
        if new_command:
            print(new_command)
        else:
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for pio_env in sys.argv[1:]:
            generate_merge_firmware_command(pio_env)
    else:
        generate_merge_firmware_command()
