#!/usr/bin/env python3
"""Generate README.md for latest-hermes with Chinese descriptions."""

import json
import urllib.request
import urllib.parse
import os
import subprocess
from datetime import datetime

# Translation cache
_translate_cache = {}
CACHE_FILE = os.path.expanduser("~/.hermes/scripts/translate_cache.json")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_cache():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(_translate_cache, f, ensure_ascii=False)

def translate_text(text):
    """Translate English text to Chinese."""
    if not text:
        return "暂无描述"
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return text
    if text in _translate_cache:
        return _translate_cache[text]
    try:
        url = f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={urllib.parse.quote(text)}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            result = ''.join([s[0] for s in data[0] if s[0]])
            _translate_cache[text] = result
            return result
    except Exception:
        return text

def get_starred_repos(limit=10):
    """Get starred repos using gh CLI."""
    result = subprocess.run(
        ['gh', 'api', f'users/rainbowatlas/starred?per_page={limit}'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def main():
    global _translate_cache
    _translate_cache = load_cache()
    
    repos = get_starred_repos(10)
    
    # Collect descriptions to translate
    descriptions = []
    for repo in repos:
        desc = repo.get('description') or ''
        if desc and not any('\u4e00' <= c <= '\u9fff' for c in desc):
            if desc not in _translate_cache:
                descriptions.append(desc)
    
    # Translate new descriptions
    for i, desc in enumerate(descriptions):
        translated = translate_text(desc)
        print(f"  Translated {i+1}/{len(descriptions)}: {desc[:50]}...")
        import time
        time.sleep(0.3)
    
    save_cache()
    
    # Generate README
    lines = [
        "# Latest Hermes 🌟\n",
        "Recently starred repositories — automatically curated.\n",
        "| # | Repository | Description | Stars | Language |",
        "|---|------------|-------------|-------|----------|"
    ]
    
    for i, repo in enumerate(repos, 1):
        name = repo['full_name']
        desc = repo.get('description') or ''
        stars = repo.get('stargazers_count', 0)
        lang = repo.get('language') or '—'
        stars_str = f"★{stars:,}"
        
        # Translate description
        if desc:
            if any('\u4e00' <= c <= '\u9fff' for c in desc):
                desc_zh = desc
            else:
                desc_zh = translate_text(desc)
        else:
            desc_zh = "暂无描述"
        
        repo_link = f"[{name}](https://github.com/{name})"
        lines.append(f"| {i} | {repo_link} | {desc_zh} | {stars_str} | {lang} |")
    
    today = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"\n> Updated: {today}")
    
    readme_content = '\n'.join(lines) + '\n'
    
    # Write README
    readme_path = os.path.expanduser("~/latest-hermes/README.md")
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"\nREADME.md updated with {len(repos)} repositories.")
    print(readme_content)

if __name__ == '__main__':
    main()
