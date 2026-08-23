import subprocess
import os
import uuid
import time
import tempfile

TEMP_DIR = os.path.join(tempfile.gettempdir(), "ai_lab_compiler")


def compile_and_run(code: str, input_data: str | None = None, timeout_sec: int = 10) -> dict:
    """
    Compiles student C code using GCC / MinGW.
    If compilation succeeds, executes the binary with optional input_data stdin piping.
    Returns structured results with stderr line numbers and stdout.
    """
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
    except (OSError, PermissionError):
        TEMP_DIR = tempfile.gettempdir()

    file_id = uuid.uuid4().hex
    src_path = os.path.join(TEMP_DIR, f"{file_id}.c")
    exe_path = os.path.join(TEMP_DIR, f"{file_id}.exe")

    start_time = time.time()

    try:
        # Write student code to temp file
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 1. Compile
        compile_result = subprocess.run(
            ["gcc", src_path, "-o", exe_path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if compile_result.returncode != 0:
            raw_error = compile_result.stderr.strip()

            # Replace temporary path with main.c for clean student error messages
            lines = raw_error.splitlines()
            clean_lines = []
            for line in lines:
                if file_id in line or src_path in line:
                    line = line.replace(src_path, "main.c").replace(f"{file_id}.c", "main.c")
                clean_lines.append(line)

            clean_error = "\n".join(clean_lines)

            # Extract line number from GCC error
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
                "execution_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # 2. Execute compiled binary with optional stdin
        run_kwargs = {
            "capture_output": True,
            "text": True,
            "timeout": timeout_sec,
        }
        if input_data:
            run_kwargs["input"] = input_data

        run_result = subprocess.run([exe_path], **run_kwargs)

        exec_time = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "output": run_result.stdout.strip(),
            "execution_time_ms": exec_time,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "compiler_error": "GCC compiler not found. Please verify MinGW installation.",
            "line": None,
            "execution_time_ms": 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "compiler_error": "Execution timed out (Limit: 10s). Your code may contain an infinite loop or unhandled input prompt.",
            "line": None,
            "execution_time_ms": timeout_sec * 1000,
        }
    except Exception as e:
        return {
            "success": False,
            "compiler_error": f"Internal execution error: {str(e)}",
            "line": None,
            "execution_time_ms": 0,
        }
    finally:
        # Clean up temporary files
        for p in [src_path, exe_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
