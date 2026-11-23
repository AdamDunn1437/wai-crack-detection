# How we work

Keep it simple: **never push straight to `main`**. Work on a branch, open a pull request (PR), and Adam reviews and merges it.

## The loop

```bash
# 1. Start from the latest main
git checkout main
git pull

# 2. Make a branch named after your ticket
git checkout -b wai-5-rename-script

# 3. Work, then commit small and often
git add dataset/rename_photos.py
git commit -m "WAI-5: read timestamp from file name"

# 4. Push your branch
git push -u origin wai-5-rename-script
```

5. On GitHub, click **Compare & pull request**. Put the ticket number in the title (e.g. `WAI-5: rename script`) so Linear links it.
6. Adam reviews and merges. Then go back to step 1 for the next piece.

**Tip:** Linear can copy the branch name for you. Open your ticket and press `Cmd/Ctrl + Shift + .`.

## Rules of thumb

- Stay in your own folder (see the table in the README). If you need to change someone else's folder, message them first.
- No photos, labels or model weights in git. They go on Drive.
- Each script gets a short README section: what it does, how to run it, an example command.
- Paths to Drive go in as command-line arguments, never hard-coded to your own computer.
- Open a PR early, even if it isn't finished ("Draft PR"), if you want feedback.

## New to git?

That's fine. Ask Adam on Discord, or pair with someone. GitHub Desktop (desktop.github.com) does all of the above with buttons.
