# WECCA × Western AI: Concrete Crack Detection

Detecting cracks in sanded concrete-canoe concrete, and comparing approaches fairly:

1. Classical image processing (no ML)
2. Off-the-shelf model prompted with "crack" (no training)
3. YOLO segmentation trained on public crack datasets
4. YOLO fine-tuned on our own canoe photos (January)

Pipeline: **capture → dataset → labels → models → evaluation**. Target: CUCAI 2027 paper.

## Who owns what

| Folder | What | Owner | Linear |
|---|---|---|---|
| `capture/` | Photo box, capture checklist, imaging notes | Connor | WAI-15 |
| `dataset/` | Folder layout, rename script, photo spreadsheet | Anthony | WAI-5 |
| `labelling/` | Labelling tool notes + what-counts-as-a-crack guide | Ben | WAI-10 |
| `models/baselines/` | Off-the-shelf model + YOLO on public data | Alan | WAI-8 |
| `models/classical/` | Classical CV baseline | Adam | WAI-9 |
| `eval/` | One scoring script for every model | Lucian | WAI-7 |
| `paper/` | CUCAI paper skeleton | Adam | WAI-22 |

Each folder has its own README saying what goes there. Full task details are in each person's Linear ticket.

## Where the data lives

**Photos, labels and model weights are NOT stored in this repo.** They live in the shared Google Drive (`raw/`, `tiles/`, `labels/`). They're WECCA's photos and too big for git anyway. Scripts take the Drive folder path as an argument. `.gitignore` blocks common image and weight files as a safety net.

## Getting started

```bash
git clone https://github.com/AdamDunn1437/wecca-crack-detection.git
cd wecca-crack-detection
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Then read [CONTRIBUTING.md](CONTRIBUTING.md) for how we work (branches + pull requests).

Questions → message Adam on Discord.
