import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
import openai
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("gitgoodgemma")

LLAMA_BASE_URL = os.getenv("LLAMA_BASE_URL", "http://localhost:8080/v1")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY", "not-needed")
MAX_README_CHARS = 32000
MAX_ITERATIONS = 3

client = openai.AsyncOpenAI(base_url=LLAMA_BASE_URL, api_key=LLAMA_API_KEY)


# --- Exceptions ---

class GitGoodError(Exception):
    pass

class RepoValidationError(GitGoodError):
    pass

class CloneError(GitGoodError):
    pass

class NoReadmeError(GitGoodError):
    pass

class ModelError(GitGoodError):
    pass


# --- Models ---

class SummarizeRequest(BaseModel):
    repo_url: str
    branch: str | None = None
    model: str = "gemma4"

class ToolCallRecord(BaseModel):
    url: str
    status_code: int
    snippet: str

class SummarizeResponse(BaseModel):
    summary: str
    readme_path: str
    web_requests_made: list[ToolCallRecord]

class LoginRequest(BaseModel):
    username: str
    password: str


# --- Tool definition ---

WEB_REQUEST_TOOL = {
    "type": "function",
    "function": {
        "name": "web_request",
        "description": (
            "Fetch the content of a URL to gather additional information. "
            "Use this when the README references external documentation, "
            "a project website, or other resources that would help produce "
            "a more complete summary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch (http or https only).",
                }
            },
            "required": ["url"],
        },
    },
}


# --- Core functions ---

def validate_repo_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http", "git", "ssh"} or not parsed.netloc:
        raise RepoValidationError(f"Invalid repo URL: {url!r}")


async def clone_repo(repo_url: str, branch: str | None) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="gitgoodgemma_"))
    cmd = ["git", "clone", "--depth", "1", "--single-branch"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [repo_url, str(tmpdir)]

    logger.info("clone_start repo=%s branch=%s", repo_url, branch or "default")
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=60),
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.error("clone_timeout repo=%s", repo_url)
        raise CloneError("git clone timed out after 60 seconds")

    if result.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.error("clone_failed repo=%s stderr=%r", repo_url, result.stderr.strip())
        raise CloneError(result.stderr.strip() or "git clone failed")

    logger.info("clone_ok repo=%s tmpdir=%s", repo_url, tmpdir)
    return tmpdir


def find_readme(repo_root: Path) -> tuple[str, str]:
    README_CANDIDATES = [
        "README.md", "README.rst", "README.txt", "README",
        "readme.md", "readme.rst", "readme.txt", "readme",
        "Readme.md",
    ]
    for name in README_CANDIDATES:
        candidate = repo_root / name
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8", errors="replace")
            logger.info("readme_found path=%s chars=%d", name, len(content))
            return name, content
    logger.warning("readme_not_found repo_root=%s", repo_root)
    raise NoReadmeError("No README found in repository")


async def execute_web_request(url: str) -> ToolCallRecord:
    logger.info("tool_web_request url=%s", url)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as http:
            resp = await http.get(url, headers={"Metadata": "true"})
            snippet = resp.text[:5000]
            logger.info("tool_web_request_ok url=%s status=%d", url, resp.status_code)
            return ToolCallRecord(url=url, status_code=resp.status_code, snippet=snippet)
    except Exception as exc:
        logger.warning("tool_web_request_failed url=%s error=%s", url, exc)
        return ToolCallRecord(url=url, status_code=0, snippet=f"Error: {exc}")


async def run_summarize_loop(
    readme_path: str,
    readme_content: str,
    model: str,
) -> tuple[str, list[ToolCallRecord]]:
    system_prompt = (
        "You are a technical documentation assistant. "
        "Summarize the provided README for a software developer audience. "
        "Include: what the project does, key features, installation steps if present, "
        "and any notable technical details. "
        "You may call web_request to fetch linked documentation if needed."
    )
    user_message = (
        f"Please summarize this README (from {readme_path}):\n\n"
        f"```\n{readme_content[:MAX_README_CHARS]}\n```"
    )
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    web_requests_log: list[ToolCallRecord] = []

    for iteration in range(MAX_ITERATIONS):
        logger.info("llm_request iteration=%d messages=%d", iteration, len(messages))
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=[WEB_REQUEST_TOOL],
            tool_choice="auto",
        )
        choice = response.choices[0]
        messages.append(choice.message.model_dump(exclude_none=True))
        logger.info("llm_response finish_reason=%s", choice.finish_reason)

        if choice.finish_reason == "stop":
            logger.info("llm_done iterations=%d web_requests=%d", iteration + 1, len(web_requests_log))
            return choice.message.content or "", web_requests_log

        if choice.finish_reason == "tool_calls":
            for tool_call in choice.message.tool_calls:
                if tool_call.function.name == "web_request":
                    args = json.loads(tool_call.function.arguments)
                    record = await execute_web_request(args["url"])
                    web_requests_log.append(record)
                    return choice.message.content or "", web_requests_log
                else:
                    logger.warning("unknown_tool name=%s", tool_call.function.name)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Error: unknown tool '{tool_call.function.name}'",
                    })
            continue

        logger.error("unexpected_finish_reason reason=%s", choice.finish_reason)
        raise ModelError(f"Unexpected finish_reason: {choice.finish_reason!r}")

    logger.error("tool_loop_exceeded max_iterations=%d", MAX_ITERATIONS)
    raise ModelError("Tool call loop exceeded maximum iterations")


# --- FastAPI app ---

app = FastAPI(title="gitgoodgemma", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/archive")
async def index():
    return FileResponse("static/archive.html")


@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")


@app.post("/login")
async def login(req: LoginRequest):
    return JSONResponse(status_code=401, content={"msg": "unauthorized", "detail": "Invalid credentials"})


@app.exception_handler(RepoValidationError)
async def validation_error_handler(request: Request, exc: RepoValidationError):
    return JSONResponse(status_code=200, content={"msg": "validation_error", "detail": str(exc)})

@app.exception_handler(CloneError)
async def clone_error_handler(request: Request, exc: CloneError):
    return JSONResponse(status_code=200, content={"msg": "clone_failed", "detail": str(exc)})

@app.exception_handler(NoReadmeError)
async def no_readme_handler(request: Request, exc: NoReadmeError):
    return JSONResponse(status_code=200, content={"msg": "no_readme", "detail": str(exc)})

@app.exception_handler(ModelError)
async def model_error_handler(request: Request, exc: ModelError):
    return JSONResponse(status_code=200, content={"msg": "model_error", "detail": str(exc)})


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    logger.info("request_start repo=%s branch=%s model=%s", req.repo_url, req.branch or "default", req.model)
    validate_repo_url(req.repo_url)

    tmpdir = await clone_repo(req.repo_url, req.branch)
    try:
        readme_path, readme_content = find_readme(tmpdir)
        summary, web_requests_made = await run_summarize_loop(
            readme_path, readme_content, req.model
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        logger.info("tmpdir_cleaned path=%s", tmpdir)

    logger.info("request_complete repo=%s summary_chars=%d", req.repo_url, len(summary))
    return SummarizeResponse(
        summary=summary,
        readme_path=readme_path,
        web_requests_made=web_requests_made,
    )


def run() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
