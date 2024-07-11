import argparse
import re
from pathlib import Path
from .doc_gen import DocGen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=f"{Path(__file__).parent.parent.parent}",
        help="The root path from which to search for files to check. The default is the root of the git repo (two up from this file).",
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--service", default="s3")
    parser.add_argument("--language", default="Python")
    parser.add_argument("--prompt", default="Explain this code at the 200 level")
    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    doc_gen = DocGen.from_root(root=root_path)
    doc_gen.collect_snippets(snippets_root=root_path)
    out = Path(args.out)

    for example in doc_gen.examples.values():
        if example.category == "Api":
            if args.service in example.services:
                if args.language in example.languages:
                    for version in example.languages[args.language].versions:
                        print(f"Found {example.id}")
                        for i, excerpt in enumerate(version.excerpts):
                            code = ""
                            for snippet_tag in excerpt.snippet_tags:
                                code += doc_gen.snippets[snippet_tag].code + "\n"
                            prompt = "\n".join(
                                [
                                    example.id,
                                    "",
                                    "```python",
                                    code,
                                    "```",
                                    "",
                                    args.prompt,
                                ]
                            )
                            # Indent for markdown
                            prompt = re.sub(r"(?m)^", "  ", prompt)
                            part = "." + str(i) if i > 0 else ""
                            name = out / (example.id + part + ".md")
                            with open(name, "w") as file:
                                file.write(
                                    "\n".join(["---", "prompt: |", prompt, "---"])
                                )
                                print(f"Wrote {name}")


if __name__ == "__main__":
    main()
