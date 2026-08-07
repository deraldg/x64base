From PowerShell:

```powershell
cd D:\dev\x64base-site

# Install deps if needed
# npm install

# Build static export
# npm run build

# Serve exported site locally
cd .\out
python -m http.server 4173 --bind 127.0.0.1
```

Then open:

[http://127.0.0.1:4173/](http://127.0.0.1:4173/)

For live development instead:

```powershell
cd D:\dev\x64base-site
npm run dev
```

Then open the URL Next prints, usually:

[http://localhost:3000/](http://localhost:3000/)

The production-style files are in `D:\dev\x64base-site\out` after `npm run build`.