# Codex Skills

Personal Codex skills synced through GitHub.

Repository: <https://github.com/imtangyujing/codex-skills>

## Layout

- `skills/`: personal skill folders to sync across machines.
- `install.sh`: links every folder in `skills/` into `${CODEX_HOME:-$HOME/.codex}/skills`.

Do not put Codex-managed system folders here, such as `.system` or `codex-primary-runtime`.

## How It Works

This repo is the source of truth for personal skills.

On this Mac, `~/.codex/skills/<skill-name>` is a symlink to:

```bash
~/Documents/Dev/codex-skills/skills/<skill-name>
```

That means editing a personal skill through Codex edits the files inside this Git repo.

GitHub sync is not automatic. After editing a skill, commit and push the repo. On another Mac, pull the repo to receive the change.

## First Setup On Another Mac

```bash
mkdir -p ~/Documents/Dev
cd ~/Documents/Dev
git clone https://github.com/imtangyujing/codex-skills.git
cd codex-skills
./install.sh
```

`./install.sh` creates symlinks from `~/.codex/skills` to this repo. If a same-name local skill already exists, the script backs it up before linking.

## After Editing Skills

```bash
cd ~/Documents/Dev/codex-skills
git status
git add skills
git commit -m "Update skills"
git push
```

Use this after changing existing skills or adding new ones.

## Git Commands In Plain Words

These are normal Git commands, not custom commands created for this repo.

```bash
git status
```

Show what changed locally.

```bash
git add skills
```

Put changes inside the `skills/` folder into the next saved version. Think of it as choosing what to include.

```bash
git commit -m "Update skills"
```

Save the chosen changes as a local version. The text after `-m` is the note for that version. You can write a clearer note, for example:

```bash
git commit -m "更新寓言写作 skill"
```

```bash
git push
```

Upload local commits to GitHub. Other computers cannot receive the change until this runs successfully.

```bash
git pull
```

Download commits from GitHub onto this computer.

Short version:

- `add`: choose changed files.
- `commit`: save a local version.
- `push`: upload to GitHub.
- `pull`: download from GitHub.

## Common Git Cheat Sheet

Initialize a new Git repo in the current folder:

```bash
git init
```

Clone a GitHub repo to this computer:

```bash
git clone https://github.com/imtangyujing/codex-skills.git
```

Check current file changes and branch status:

```bash
git status
```

See exact unstaged file changes:

```bash
git diff
```

Choose files for the next commit:

```bash
git add skills
```

Choose everything that changed in the repo:

```bash
git add .
```

Save chosen changes as a local version:

```bash
git commit -m "Update skills"
```

Show commit history:

```bash
git log --oneline
```

Show what changed in one commit:

```bash
git show <commit-id>
```

List branches:

```bash
git branch
```

Create and switch to a new branch:

```bash
git checkout -b <branch-name>
```

Switch to an existing branch:

```bash
git checkout <branch-name>
```

Merge another branch into the current branch:

```bash
git merge <branch-name>
```

Upload local commits to GitHub:

```bash
git push
```

Download GitHub commits to this computer:

```bash
git pull
```

For this skills repo, the most common loop is still:

```bash
cd ~/Documents/Dev/codex-skills
git status
git diff
git add skills
git commit -m "Update skills"
git push
```

## On The Other Mac

```bash
cd ~/Documents/Dev/codex-skills
git pull
./install.sh
```

Run `./install.sh` after the first clone, after adding a new skill, or if symlinks were removed. For ordinary edits to existing skills, `git pull` is usually enough because the symlinks already point into this repo.

## Common Commands

Check whether local skill edits have not been pushed:

```bash
cd ~/Documents/Dev/codex-skills
git status
```

Publish local edits:

```bash
cd ~/Documents/Dev/codex-skills
git add skills
git commit -m "Update skills"
git push
```

Fetch edits from GitHub:

```bash
cd ~/Documents/Dev/codex-skills
git pull
```

## Add A New Skill

Create or copy the skill into `skills/<skill-name>`, then run:

```bash
./install.sh
git add skills/<skill-name>
git commit -m "Add <skill-name> skill"
git push
```
