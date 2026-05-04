$env:DOTTALK_APPEND_TRACE = "0"
$env:DOTTALK_INDEX_TRACE  = "0"

Copy-Item "\dottalkpp\build\src\Release\dottalkpp.exe" `
          "\dottalkpp\dottalkpp\bin\dottalkpp.exe" `
          -Force

Set-Location "\dottalkpp\dottalkpp\data"
& "\dottalkpp\dottalkpp\bin\dottalkpp.exe"

Set-Location "\dottalkpp"

$py12 = "\dottalkpp\build\vcpkg_installed\x64-windows\tools\python3\python.exe"
& $py12 "\dottalkpp\bindings\pydottalk_smoke.py"