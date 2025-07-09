# Lliam - LLM-powered IAM Policy Metadata Enhancement

Lliam automates the process of generating, running, parsing, and applying [Ailly](https://www.npmjs.com/package/@ailly/cli) prompt outputs to enhance AWS DocGen IAM policy examples with rich metadata.

---

## 📦 Overview

Lliam provides a multi-step workflow to:
1. **Generate** Ailly prompts from DocGen IAM policy snippets
2. **Execute** Ailly CLI to get LLM-enhanced metadata
3. **Update** your DocGen examples with the enhanced metadata

The workflow is designed around three main commands that can be run independently or in sequence.

---

## ✅ Prerequisites

- Python 3.8+
- Node.js and npm (for `npx @ailly/cli`)
- A DocGen project directory with IAM policy examples

---

## 🚀 Usage

### Step 1: Create Prompts

Generate Ailly prompts from your DocGen IAM policy examples:

```bash
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app create-prompts \
  /path/to/your/docgen/project \
  --system-prompts path/to/system_prompt.txt
```

### Step 2: Run Ailly

Execute Ailly to generate enhanced metadata:

```bash
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app run-ailly
```

Optionally process specific batches:
```bash
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app run-ailly --batches "batch_01,batch_02"
```

### Step 3: Update Repository

Apply the enhanced metadata back to your DocGen examples:

```bash
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app update-reservoir \
  /path/to/your/docgen/project
```

Optionally update specific batches or packages:
```bash
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app update-reservoir \
  /path/to/your/docgen/project \
  --batches "batch_01,batch_02" \
  --packages "package1,package2"
```

---

## 🗂 Workflow Details

1. **Prompt Generation**: 
   - Scans DocGen examples for IAM policies with default metadata prefixes
   - Creates batched Markdown files in `.ailly_iam_policy/`
   - Generates `.aillyrc` configuration with system prompts

2. **Ailly Execution**:
   - Runs `npx @ailly/cli` on generated prompts
   - Processes batches to manage large datasets
   - Generates `.ailly.md` response files

3. **Metadata Update**:
   - Parses Ailly responses for enhanced metadata
   - Updates DocGen examples with `title`, `title_abbrev`, `synopsis`, and `description`
   - Applies service-specific suffixes to metadata

---

## 💡 Example Workflow

```bash
# Generate prompts from IAM policy examples
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app create-prompts \
  ~/projects/AWSIAMPolicyExampleReservoir \
  --system-prompts prompts/iam_system_prompt.txt

# Run Ailly on all generated prompts
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app run-ailly

# Update the repository with enhanced metadata
python -m aws_doc_sdk_examples_tools.lliam.entry_points.lliam_app update-reservoir \
  ~/projects/AWSIAMPolicyExampleReservoir
```

This workflow will:
- Extract IAM policy snippets and create batched prompts in `.ailly_iam_policy/`
- Execute Ailly to generate enhanced metadata
- Parse responses and update your DocGen examples with rich metadata
