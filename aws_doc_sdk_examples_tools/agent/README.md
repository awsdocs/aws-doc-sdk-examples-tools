# Ailly Prompt Workflow

This project automates the process of generating, running, parsing, and applying [Ailly](https://www.npmjs.com/package/@ailly/cli) prompt outputs to an AWS DocGen project. It combines all steps into one streamlined command using a single Python script.

---

## 📦 Overview

This tool:
1. **Generates** Ailly prompts from DocGen snippets.
2. **Runs** Ailly CLI to get enhanced metadata.
3. **Parses** Ailly responses into structured JSON.
4. **Updates** your DocGen examples with the new metadata.

All of this is done with one command.

---

## ✅ Prerequisites

- Python 3.8+
- Node.js and npm (for `npx`)
- A DocGen project directory

---

## 🚀 Usage

From your project root, run:

```bash
python -m aws_doc_sdk_examples_tools.agent.bin.main \
  /path/to/your/docgen/project \
  --system-prompts path/to/system_prompt.txt
```

### 🔧 Arguments

Run `python -m aws_doc_sdk_examples_tools.agent.bin.main --help` for more info.

---

## 🗂 What This Does

Under the hood, this script:

1. Creates a directory `.ailly_iam_policy` containing:
   - One Markdown file per snippet.
   - A `.aillyrc` configuration file.

2. Runs `npx @ailly/cli` to generate `.ailly.md` outputs.

3. Parses the Ailly `.ailly.md` files into a single `iam_updates.json` file.

4. Updates each matching `Example` in the DocGen instance with:
   - `title`
   - `title_abbrev`
   - `synopsis`

---

## 💡 Example

```bash
python -m aws_doc_sdk_examples_tools.agent.bin.main \
  ~/projects/AWSIAMPolicyExampleReservoir \
  --system-prompts prompts/system_prompt.txt
```

This will:
- Write prompts and config to `.ailly_iam_policy/`
- Run Ailly and capture results
- Parse and save output as `.ailly_iam_policy/iam_updates.json`
- Apply updates to your DocGen examples
