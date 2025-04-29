# Ailly Prompt Workflow

This project provides two scripts to **generate**, **run**, and **parse** [Ailly](https://www.npmjs.com/package/@ailly/cli) prompts based on your AWS DocGen snippets.

## Overview

1. **Generate** Ailly prompts from DocGen snippets (`make_prompts.py`).
2. **Run** the Ailly CLI on the generated prompts (`npx @ailly/cli`).
3. **Parse** the Ailly outputs back into structured JSON (`parse_json_files.py`).

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

This will:
- Create Markdown files for each snippet.
- Create a `.aillyrc` file with the provided system prompts.

---

## Step 2: Run Ailly CLI

Run Ailly on the generated prompts. From inside the .ailly_prompts directory:

```bash
npx @ailly/cli --root .ailly_prompts
```

This will create `.ailly.md` output files in the `.ailly_prompts` directory (or whatever output directory you specified).

---

## Step 3: Parse Ailly output

After Ailly has generated response files (`*.ailly.md`), parse them into JSON objects using `parse_json_files.py`:

```bash
python parse_json_files.py .ailly_prompts/*.ailly.md --out output.json
```

**Arguments:**
- Positional: List of files to parse (you can use a glob like `*.ailly.md`).
- `--out`: (Optional) Output file path for the resulting JSON array. Defaults to `out.json`.

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
python parse_json_files.py .ailly_prompts/*.ailly.md --out results.json
```
