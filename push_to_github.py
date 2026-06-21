"""
Загружает все файлы проекта на GitHub через Git Tree API.
"""
import os, json, base64, urllib.request, urllib.error

TOKEN = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]
REPO = "vovaki-coger/neuro-killaura-visuals"
BASE = os.path.dirname(os.path.abspath(__file__))
BRANCH = "main"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json",
    "User-Agent": "NeuroKillAura-Push",
}

def api(method, path, body=None):
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        print(f"HTTP {e.code} {path}: {content[:200]}")
        return None

def get_all_files():
    skip = {'.git', '__pycache__', '.DS_Store', 'push_to_github.py', 'models'}
    result = []
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if f.endswith('.pyc'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, BASE).replace('\\', '/')
            result.append((rel, full))
    return result

def main():
    # 1. Get current HEAD
    ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    if not ref:
        print("Creating initial commit...")
        # try to get default branch
        repo_info = api("GET", f"/repos/{REPO}")
        branch = repo_info.get("default_branch", "main") if repo_info else "main"
        ref = api("GET", f"/repos/{REPO}/git/ref/heads/{branch}")

    base_sha = ref["object"]["sha"]
    print(f"Base commit SHA: {base_sha}")

    # 2. Get base tree SHA
    commit = api("GET", f"/repos/{REPO}/git/commits/{base_sha}")
    base_tree_sha = commit["tree"]["sha"]
    print(f"Base tree SHA: {base_tree_sha}")

    # 3. Build tree entries
    files = get_all_files()
    print(f"Uploading {len(files)} files...")

    tree_entries = []
    for i, (rel, full) in enumerate(files):
        with open(full, "rb") as fh:
            raw = fh.read()
        try:
            content = raw.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = base64.b64encode(raw).decode()
            encoding = "base64"

        # Create blob
        blob_body = {"content": content, "encoding": encoding}
        blob = api("POST", f"/repos/{REPO}/git/blobs", blob_body)
        if not blob:
            print(f"  SKIP (blob error): {rel}")
            continue
        tree_entries.append({
            "path": rel,
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        if (i + 1) % 5 == 0:
            print(f"  {i+1}/{len(files)} done...")

    print(f"Creating tree with {len(tree_entries)} entries...")
    tree = api("POST", f"/repos/{REPO}/git/trees", {
        "base_tree": base_tree_sha,
        "tree": tree_entries,
    })
    if not tree:
        print("ERROR: tree creation failed")
        return

    # 4. Create commit
    new_commit = api("POST", f"/repos/{REPO}/git/commits", {
        "message": "feat: Neuro KillAura Launcher v2.0\n\n- PyTorch MLP (16→64→32→4)\n- CustomTkinter GUI (dark/light/purple themes)\n- Microsoft OAuth + Mojang + Offline auth\n- Pulse Visuals (rings, particles, hit waves)\n- Rili ESP (Box, Tracers, Health/Armor bars, Radar)\n- HUD (CPS graph, combo, watermark)\n- GitHub Actions → PyInstaller .exe release",
        "tree": tree["sha"],
        "parents": [base_sha],
    })
    if not new_commit:
        print("ERROR: commit creation failed")
        return

    # 5. Update branch
    result = api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}", {
        "sha": new_commit["sha"],
        "force": True,
    })
    if result:
        print(f"\n✅ Pushed! Commit: {new_commit['sha'][:8]}")
        print(f"   https://github.com/{REPO}")
    else:
        print("ERROR: branch update failed")

if __name__ == "__main__":
    main()
