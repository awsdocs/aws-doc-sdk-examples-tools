# Ailly Prompt Workflow

This project provides three scripts to **generate** Ailly prompts, **run** them, **parse** the results, and **update** a DocGen instance.

## Overview

1. **Generate** Ailly prompts from DocGen snippets (`make_prompts.py`).
2. **Run** the Ailly CLI on the generated prompts (`npx @ailly/cli`).
3. **Parse** the Ailly outputs into structured JSON (`parse_json_files.py`).
4. **Update** your DocGen project with the parsed results (`update_doc_gen.py`).

---

## Prerequisites

- Python 3.8+
- Node.js & npm (for `npx`)

---

## Step 1: Generate Ailly prompts

Use `make_prompts.py` to create a directory of Markdown files and a `.aillyrc` configuration file.

```bash
python make_prompts.py \
  --doc-gen-root /path/to/your/docgen/project \
  --system-prompts "You are a helpful assistant..." \
  --out .ailly_prompts
```

**Arguments:**
- `--doc-gen-root`: Path to your DocGen project root.
- `--system-prompts`: One or more system prompts, either as strings or file paths.
- `--out`: (Optional) Output directory. Defaults to `.ailly_prompts`.

---

## Step 2: Run Ailly CLI

Run Ailly on the generated prompts:

```bash
npx @ailly/cli --root .ailly_prompts
```

This will create `{file}.ailly.md` output files in the `.ailly_prompts` directory (or whatever output directory you specified).

---

## Step 3: Parse Ailly output

Parse the `.ailly.md` files into JSON using `parse_json_files.py`:

```bash
python parse_json_files.py .ailly_prompts/*.ailly.md --out example_updates.json
```

**Arguments:**
- Positional: List of files to parse (e.g., `*.ailly.md`).
- `--out`: (Optional) Path for the JSON output. Defaults to `out.json`.

---

## Step 4: Update DocGen with Ailly results

Use `update_doc_gen.py` to load the parsed data back into your `DocGen` project:

```bash
python update_doc_gen.py \
  --doc-gen-root /path/to/your/docgen/project \
  --updates-path example_updates.json
```

**Arguments:**
- `--doc-gen-root`: Path to the root of your DocGen project.
- `--updates-path`: JSON file generated in Step 3 (default: `example_updates.json`).

This will update the `title`, `title_abbrev`, and `synopsis` fields in the corresponding DocGen examples.

---

## Example Full Workflow

```bash
# Step 1: Generate prompts
python make_prompts.py \
  --doc-gen-root ~/projects/aws-docgen-root \
  --system-prompts system_prompt.txt \
  --out .ailly_prompts

# Step 2: Run Ailly
npx @ailly/cli --root .ailly_prompts

# Step 3: Parse results
python parse_json_files.py .ailly_prompts/*.ailly.md --out example_updates.json

# Step 4: Update DocGen
python update_doc_gen.py \
  --doc-gen-root ~/projects/aws-docgen-root \
  --updates-path example_updates.json
```
