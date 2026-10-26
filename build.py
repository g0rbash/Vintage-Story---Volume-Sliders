"""Build the mod zip: python build.py  ->  releases/volumesliders_<version>.zip

The zip is named after the version in modinfo.json and goes in the local releases/ folder. Older versions' zips stay
there. To update the mod after a version has been published, change "version" in modinfo.json first: a new version
number gets a new zip, and a released version's zip is never rebuilt from changed code (see the check below).
"""
import json, os, subprocess, sys, zipfile

root = os.path.dirname(os.path.abspath(__file__))
version = json.load(open(os.path.join(root, "modinfo.json"), encoding="utf-8"))["version"]


def git(*args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


# Once v<version> is tagged, the code behind that number is fixed. If it has changed since, the number must go up.
tag = f"v{version}"
if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}").returncode == 0:
    changed = git("diff", "--name-only", tag, "--", "src", "assets", "modinfo.json", "VolumeSliders.csproj").stdout.split()
    if changed:
        sys.exit(f"{tag} is already released, but these files changed since: {', '.join(changed)}\n"
                 f"Raise \"version\" in modinfo.json (for example to the next 0.1.x or 0.2.0), then build again.")

subprocess.run(["python", os.path.join(root, "tools", "generate.py")], check=True)
subprocess.run(["dotnet", "build", "-c", "Release", "-v", "q"], cwd=root, check=True)

os.makedirs(os.path.join(root, "releases"), exist_ok=True)
out = os.path.join(root, "releases", f"volumesliders_{version}.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(root, "modinfo.json"), "modinfo.json")
    z.write(os.path.join(root, "bin", "volumesliders.dll"), "volumesliders.dll")
    z.write(os.path.join(root, "LICENSE"), "LICENSE")
    for d, _, files in os.walk(os.path.join(root, "assets")):
        for f in files:
            full = os.path.join(d, f)
            z.write(full, os.path.relpath(full, root))
print(out)
