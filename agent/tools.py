import shlex

from agent.sandbox import exec_in_sandbox


def list_files(sandbox) -> str:
    return exec_in_sandbox(sandbox, "find /home/daytona/challenge -type f | sort")


def read_file(sandbox, filename: str) -> str:
    return exec_in_sandbox(sandbox, f"cat -- {shlex.quote(f'/home/daytona/challenge/{filename}')}")


def search_code(sandbox, pattern: str) -> str:
    return exec_in_sandbox(
        sandbox, f"grep -rn -- {shlex.quote(pattern)} /home/daytona/challenge/ 2>/dev/null"
    )


def run_static_analysis(sandbox) -> str:
    return exec_in_sandbox(
        sandbox,
        "pip install bandit -q 2>/dev/null; "
        "bandit -r /home/daytona/challenge/ -f json -q 2>/dev/null || true",
    )


TOOL_DEFINITIONS = [
    {
        "name": "list_files",
        "description": "List all files in the challenge repository.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "read_file",
        "description": "Read the contents of a specific file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Filename relative to the challenge root."}
            },
            "required": ["filename"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for a pattern across all files in the challenge repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Grep pattern to search for."}
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_static_analysis",
        "description": "Run bandit static analysis on the entire challenge repository and return JSON results.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


GEMINI_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "list_files",
                "description": "List all files in the challenge repository.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "read_file",
                "description": "Read the contents of a specific file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string", "description": "Filename relative to the challenge root."}
                    },
                    "required": ["filename"],
                },
            },
            {
                "name": "search_code",
                "description": "Search for a pattern across all files in the challenge repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Grep pattern to search for."}
                    },
                    "required": ["pattern"],
                },
            },
            {
                "name": "run_static_analysis",
                "description": "Run bandit static analysis on the entire challenge repository and return JSON results.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]
    }
]


def dispatch(sandbox, tool_name: str, tool_input: dict) -> str:
    if tool_name == "list_files":
        return list_files(sandbox)
    if tool_name == "read_file":
        return read_file(sandbox, tool_input["filename"])
    if tool_name == "search_code":
        return search_code(sandbox, tool_input["pattern"])
    if tool_name == "run_static_analysis":
        return run_static_analysis(sandbox)
    return f"Unknown tool: {tool_name}"
