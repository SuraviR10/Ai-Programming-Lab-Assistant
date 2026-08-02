"""
Compiler Route
POST /compile — compiles C code, runs it on success, or returns AI feedback on failure.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from services.gcc_service import compile_and_run
from services.groq_service import analyze_compiler_error

router = APIRouter()


class CompileRequest(BaseModel):
    code: str


@router.post("/compile")
async def compile_code(request: CompileRequest):
    result = compile_and_run(request.code)

    if result["success"]:
        # Compilation and execution succeeded — do NOT call Groq
        return {"success": True, "output": result["output"]}

    # Compilation failed — call Groq only now
    compiler_error = result["compiler_error"]
    line_number = result.get("line")

    ai_feedback = analyze_compiler_error(request.code, compiler_error, line_number)

    return {
        "success": False,
        "compiler_error": compiler_error,
        "line": line_number,
        "ai_feedback": ai_feedback,
    }
