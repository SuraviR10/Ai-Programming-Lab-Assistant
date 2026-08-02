import subprocess
import os
import uuid

TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp"))


def compile_and_run(code: str) -> dict:
    os.makedirs(TEMP_DIR, exist_ok=True)

    file_id = uuid.uuid4().hex
    src_path = os.path.join(TEMP_DIR, f"{file_id}.c")
    exe_path = os.path.join(TEMP_DIR, f"{file_id}.exe")

    try:
        # Write student code to file
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Compile
        compile_result = subprocess.run(
            ["gcc", src_path, "-o", exe_path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if compile_result.returncode != 0:
            # Get the raw stderr - this is the GCC error
            raw_error = compile_result.stderr.strip()

            # Clean up the temp path from error lines, replace with "main.c"
            lines = raw_error.splitlines()
            clean_lines = []
            for line in lines:
                # Each GCC error line starts with the file path
                # Replace the UUID filename with main.c
                if file_id in line:
                    line = line.replace(src_path, "main.c")
                clean_lines.append(line)

            clean_error = "\n".join(clean_lines)

            # Extract line number from error
            line_number = None
            for line in clean_lines:
                parts = line.split(":")
                if len(parts) >= 3:
                    try:
                        line_number = int(parts[1])
                        break
                    except ValueError:
                        continue

            return {
                "success": False,
                "compiler_error": clean_error,
                "line": line_number,
            }

        # Run the compiled program
        run_result = subprocess.run(
            [exe_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return {
            "success": True,
            "output": run_result.stdout,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "compiler_error": "GCC not found. Please ensure MinGW is installed and added to PATH.",
            "line": None,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "compiler_error": "Timed out. Your program may have an infinite loop.",
            "line": None,
        }
    except Exception as e:
        return {
            "success": False,
            "compiler_error": f"Server error: {str(e)}",
            "line": None,
        }
    finally:
        for p in [src_path, exe_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
