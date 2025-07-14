from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from pprint import pprint
from typing import Dict, Optional, Tuple
import yaml

AILLY_DIR = Path(".ailly_iam_policy")
BATCH_01_DIR = AILLY_DIR / "batch_01"

"""
Example inference data:
{
    "prompt": "What is high intensity interval training?",
    "modelResponses": [
        {
            "response": "High intensity interval training (HIIT) is a workout strategy that alternates between short bursts of intense, maximum-effort exercise and brief recovery periods, designed to maximize calorie burn and improve cardiovascular fitness.",
            "modelIdentifier": "Model1"
        }
    ]
}
"""


@dataclass
class Parsed:
    greymatter: Optional[Dict]
    contents: str


def parse_md_with_grey_matter(contents: str) -> Parsed:
    if not contents.startswith("---"):
        return Parsed(None, contents)

    end_delimiter_pos = contents.find("---", 3)
    if end_delimiter_pos == -1:
        return Parsed(None, contents)

    front_matter = contents[3:end_delimiter_pos].strip()

    try:
        front_matter_dict = yaml.safe_load(front_matter)
        remaining_content = contents[end_delimiter_pos + 3 :].lstrip()

        return Parsed(front_matter_dict, remaining_content)
    except yaml.YAMLError:
        return Parsed(None, contents)


def get_pairs() -> Dict[str, Tuple[Parsed, Parsed]]:
    all_files = list(BATCH_01_DIR.glob("*"))
    pairs: Dict[str, Tuple[Parsed, Parsed]] = defaultdict(
        lambda: (Parsed(None, ""), Parsed(None, ""))
    )
    for file in all_files:
        contents = file.read_text("utf-8")
        parsed = parse_md_with_grey_matter(contents)

        if file.name.endswith(".md.ailly.md"):
            key = file.name.replace(".md.ailly.md", "")
            a, _ = pairs[key]
            pairs[key] = (a, parsed)
        elif file.name.endswith(".md"):
            key = file.name.replace(".md", "")
            _, b = pairs[key]
            pairs[key] = (parsed, b)
        else:
            raise Exception(f"{file.name} doesn't have a valid extension.")

    return pairs

def get_ailly_rc() -> Parsed:
    aillyrc = (AILLY_DIR / ".aillyrc").read_text()
    return parse_md_with_grey_matter(aillyrc)

def write_jsonl(pairs: Dict[str, Tuple[Parsed, Parsed]]):
    # Get aillyrc contents
    aillyrc_parsed = get_ailly_rc()
    aillyrc_content = aillyrc_parsed.contents
    
    # Create output file
    output_path = AILLY_DIR / "inference_data.jsonl"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for key, (prompt_parsed, response_parsed) in pairs.items():
            # Skip if response doesn't have greymatter or model info
            if (not response_parsed.greymatter or 
                not response_parsed.greymatter.get("debug") or 
                not response_parsed.greymatter["debug"].get("model")):
                continue
                
            # Create the JSON object
            entry = {
                "prompt": aillyrc_content + prompt_parsed.contents,
                "modelResponses": [
                    {
                        "response": response_parsed.contents,
                        "modelIdentifier": response_parsed.greymatter["debug"]["model"].replace(":0", "")
                    }
                ]
            }
            
            # Write as a JSON line
            f.write(json.dumps(entry) + "\n")
    
    print(f"JSONL file created at {output_path}")

pairs = get_pairs()
limited_pairs = [pair for pair in list(pairs.items())[:1]]
write_jsonl(pairs)