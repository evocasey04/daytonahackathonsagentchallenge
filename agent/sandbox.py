import os
from daytona import Daytona


_client = None

CHALLENGE_DIR = "/home/daytona/challenge"


def get_client() -> Daytona:
    global _client
    if _client is None:
        _client = Daytona()
    return _client


def create_sandbox(challenge_dir: str):
    """Spin up a fresh Daytona sandbox and upload the challenge repo into it."""
    client = get_client()
    sandbox = client.create()

    sandbox.process.exec(f"mkdir -p {CHALLENGE_DIR}")

    for fname in os.listdir(challenge_dir):
        fpath = os.path.join(challenge_dir, fname)
        if os.path.isfile(fpath) and not fname.startswith("ground_truth"):
            with open(fpath, "rb") as f:
                content = f.read()
            sandbox.fs.upload_file(content, f"{CHALLENGE_DIR}/{fname}")

    return sandbox


def exec_in_sandbox(sandbox, command: str) -> str:
    result = sandbox.process.exec(command)
    return result.result or ""


def destroy_sandbox(sandbox):
    try:
        sandbox.delete()
    except Exception:
        pass
