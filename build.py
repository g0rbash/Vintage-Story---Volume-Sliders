"""Build the mod zip: python build.py  ->  dist/volumesliders_<version>.zip"""
import json, os, subprocess, zipfile

root = os.path.dirname(os.path.abspath(__file__))
subprocess.run(["python", os.path.join(root, "tools", "generate.py")], check=True)
subprocess.run(["dotnet", "build", "-c", "Release", "-v", "q"], cwd=root, check=True)

version = json.load(open(os.path.join(root, "modinfo.json")))["version"]
os.makedirs(os.path.join(root, "dist"), exist_ok=True)
out = os.path.join(root, "dist", f"volumesliders_{version}.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(root, "modinfo.json"), "modinfo.json")
    z.write(os.path.join(root, "bin", "volumesliders.dll"), "volumesliders.dll")
    for d, _, files in os.walk(os.path.join(root, "assets")):
        for f in files:
            full = os.path.join(d, f)
            z.write(full, os.path.relpath(full, root))
print(out)
