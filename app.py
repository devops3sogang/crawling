from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/run")
def run_crawler():
    try:
        result = subprocess.run(
            ["python", "crawler.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": e.stderr}