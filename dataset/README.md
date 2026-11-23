# dataset/ (Anthony, WAI-5)

Folder layout, rename script and photo spreadsheet ("manifest"). Every other part of the project reads from this.

**Goes here**

- `rename_photos.py`: takes a folder of photos, reads the time from the file name (`20261114_124317` = Nov 14, 12:43:17), renames them consistently and adds rows to the manifest
- Manifest columns: file name, cast, stage (before sanding / after sanding), zone, time taken, notes

**Drive layout:** `raw/` (originals, never edited), `tiles/` (January), `labels/`

**Usage:** fill in once the script exists, e.g.

```bash
python dataset/rename_photos.py --input "<Drive>/incoming" --out "<Drive>/raw" --cast 2 --stage after_sanding
```

Timeline: setup by Dec 1, cast 2 after-sanding photos loaded by Dec 5.
