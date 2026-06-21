import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOKEN = process.env.GITHUB_PERSONAL_ACCESS_TOKEN;
const REPO = "vovaki-coger/neuro-killaura-visuals";
const BRANCH = "main";
const BASE = __dirname;

const headers = {
  "Authorization": `token ${TOKEN}`,
  "Accept": "application/vnd.github.v3+json",
  "Content-Type": "application/json",
  "User-Agent": "NeuroKillAura",
};

async function api(method, endpoint, body) {
  const url = `https://api.github.com${endpoint}`;
  const resp = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`${resp.status} ${endpoint}: ${txt.slice(0,200)}`);
  }
  return resp.json();
}

function walkFiles(dir, base = dir, skip = new Set(['.git','__pycache__','models','.DS_Store'])) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (skip.has(entry.name) || entry.name.endsWith('.pyc')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) results.push(...walkFiles(full, base, skip));
    else results.push([path.relative(base, full).replace(/\\/g, '/'), full]);
  }
  return results;
}

async function main() {
  console.log('Getting branch ref...');
  const ref = await api("GET", `/repos/${REPO}/git/ref/heads/${BRANCH}`);
  const baseSha = ref.object.sha;
  console.log(`Base commit: ${baseSha.slice(0,8)}`);

  const commit = await api("GET", `/repos/${REPO}/git/commits/${baseSha}`);
  const baseTreeSha = commit.tree.sha;

  const files = walkFiles(BASE);
  console.log(`Uploading ${files.length} files...`);

  const treeEntries = [];
  for (let i = 0; i < files.length; i++) {
    const [rel, full] = files[i];
    const raw = fs.readFileSync(full);
    let content, encoding;
    try {
      content = raw.toString('utf-8');
      encoding = 'utf-8';
    } catch {
      content = raw.toString('base64');
      encoding = 'base64';
    }
    const blob = await api("POST", `/repos/${REPO}/git/blobs`, { content, encoding });
    treeEntries.push({ path: rel, mode: "100644", type: "blob", sha: blob.sha });
    if ((i + 1) % 10 === 0 || i === files.length - 1) {
      process.stdout.write(`  ${i+1}/${files.length}\n`);
    }
  }

  console.log('Creating tree...');
  const tree = await api("POST", `/repos/${REPO}/git/trees`, {
    base_tree: baseTreeSha,
    tree: treeEntries,
  });

  console.log('Creating commit...');
  const newCommit = await api("POST", `/repos/${REPO}/git/commits`, {
    message: "feat: Neuro KillAura Launcher v2.0 — full source\n\n" +
      "- PyTorch MLP KillAura (16→64→32→4)\n" +
      "- CustomTkinter GUI (dark/light/purple themes)\n" +
      "- Microsoft OAuth + Mojang Legacy + Offline auth\n" +
      "- Pulse Visuals (rings, particles, hit waves)\n" +
      "- Rili ESP (Box ESP, Tracers, Health/Armor bars, Radar)\n" +
      "- HUD (CPS graph, combo, watermark)\n" +
      "- GitHub Actions → PyInstaller .exe release",
    tree: tree.sha,
    parents: [baseSha],
  });

  console.log('Updating branch...');
  await api("PATCH", `/repos/${REPO}/git/refs/heads/${BRANCH}`, {
    sha: newCommit.sha,
    force: true,
  });

  console.log(`\n✅ Pushed! https://github.com/${REPO}`);
  console.log(`   Commit: ${newCommit.sha.slice(0,8)}`);

  // Create tag v2.0.0 for release
  console.log('\nCreating release tag v2.0.0...');
  try {
    const tagObj = await api("POST", `/repos/${REPO}/git/tags`, {
      tag: "v2.0.0",
      message: "Neuro KillAura Launcher v2.0.0",
      object: newCommit.sha,
      type: "commit",
      tagger: { name: "NeuroKillAura Bot", email: "bot@replit.com", date: new Date().toISOString() },
    });
    await api("POST", `/repos/${REPO}/git/refs`, { ref: "refs/tags/v2.0.0", sha: tagObj.object.sha });
    console.log('Tag v2.0.0 created → GitHub Actions will build the .exe release');
  } catch(e) {
    console.log('Tag may already exist:', e.message.slice(0,100));
  }

  // Create GitHub Release directly
  console.log('Creating GitHub Release...');
  try {
    const release = await api("POST", `/repos/${REPO}/releases`, {
      tag_name: "v2.0.0",
      name: "⚡ Neuro KillAura Launcher v2.0.0",
      body: `## ⚡ Neuro KillAura Launcher v2.0.0

### 📥 Установка (Windows)
1. Нажми **Actions** → **Build & Release** → **Run workflow**
2. После сборки скачай \`NeuroKillAura-Windows-x64.zip\`
3. Распакуй и запусти \`NeuroKillAura.exe\`

### Что внутри
- **Лаунчер** — CustomTkinter GUI с темами (dark/light/purple)
- **Нейросеть** — PyTorch MLP 16→64→32→4, human-like aim
- **Авторизация** — Microsoft OAuth, Mojang, Оффлайн
- **Pulse Visuals** — пульсирующие круги, частицы, hit waves
- **Rili ESP** — Box ESP, Tracers, Health/Armor bars, Radar, Crosshair
- **HUD** — CPS-график, combo, watermark, keybinds

### Горячие клавиши
| Клавиша | Действие |
|---------|---------|
| \`INSERT\` | Открыть/закрыть меню |
| \`R\` | Вкл/выкл KillAura |
| \`G\` | Вкл/выкл визуалы |
| \`H\` | Вкл/выкл HUD |
| \`ESC\` | Выход |

> ⚙️ **Для автосборки .exe**: перейди в **Actions** → **Build & Release** → **Run workflow**`,
      draft: false,
      prerelease: false,
    });
    console.log(`✅ Release: ${release.html_url}`);
  } catch(e) {
    console.log('Release note:', e.message.slice(0,200));
  }
}

main().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
