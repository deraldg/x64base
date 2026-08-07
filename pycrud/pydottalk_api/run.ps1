$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
& .\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
