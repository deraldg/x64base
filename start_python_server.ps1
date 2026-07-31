d:

Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

python -m http.server 3000 --directory D:\dev\x64base-site\out

Serving HTTP on :: port 3000 (http://[::]:3000/) ...

http://localhost:3000/
