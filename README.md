# Codex Skills

Personal Codex skills synced through GitHub.

## Layout

- `skills/`: personal skill folders to sync across machines.
- `install.sh`: links every folder in `skills/` into `${CODEX_HOME:-$HOME/.codex}/skills`.

Do not put Codex-managed system folders here, such as `.system` or `codex-primary-runtime`.

## First Setup On This Mac

```bash
cd /Users/jay/Documents/Dev/codex-skills
git init
git add .
git commit -m "Add personal Codex skills"
gh repo create codex-skills --private --source=. --remote=origin --push
./install.sh
```

## Setup On Another Mac

```bash
mkdir -p ~/Documents/Dev
cd ~/Documents/Dev
git clone https://github.com/imtangyujing/codex-skills.git
cd codex-skills
./install.sh
```

## Daily Sync

After editing a skill on any machine:

```bash
cd ~/Documents/Dev/codex-skills
git status
git add skills
git commit -m "Update skills"
git push
```

On the other machine:

```bash
cd ~/Documents/Dev/codex-skills
git pull
./install.sh
```

## Add A New Skill

Create or copy the skill into `skills/<skill-name>`, then run:

```bash
./install.sh
git add skills/<skill-name>
git commit -m "Add <skill-name> skill"
git push
```

