from typing import List, Dict, Any
from pathlib import Path
from pprint import pformat
import logging
from .doc_gen import DocGen

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_root(root: str, base: DocGen) -> Dict[str, Any]:
    """
    Process a single root directory & collect example stats.

    Args:
        root (str): The root dir to process.
        base (DocGen): Instance of DocGen class.

    Returns:
        dict: Stats for the given root.
    """
    try:
        docgen_root = Path(root)
        if not docgen_root.exists():
            logging.warning(f"Root directory {docgen_root} does not exist.")
            return {}

        doc_gen = base.clone().for_root(docgen_root)
        doc_gen.collect_snippets()

        stats = doc_gen.stats()
        stats['root'] = docgen_root.name
        return stats
    except Exception as e:
        logging.error(f"Error processing root {root}: {e}")
        return {}

def collect_stats(roots: List[str]) -> List[Dict[str, Any]]:
    """
    Collects stats for a list of root directories.

    Args:
        roots (List[str]): A list of root directories as strings.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries with collected stats for each root.
    """
    base = DocGen.empty()
    all_stats = []

    for root in roots:
        stats = process_root(root, base)
        if stats:
            all_stats.append(stats)

    return all_stats

def print_stats(stats: Dict[str, Any]):
    """
    Prints stats in a formatted manner.

    Args:
        stats (dict): A dictionary containing collected stats.
    """
    logging.info(f"Root: {stats['root']}")
    logging.info(f"SDKs: {stats['sdks']}")
    logging.info(f"Services: {stats['services']}")
    logging.info(f"Examples: {stats['examples']}")
    logging.info(f"Version: {stats['versions']}")
    logging.info(f"Snippets: {stats['snippets']}")
    genai = pformat(dict(stats.get("genai", {})))
    logging.info(f"GenAI: {genai}")

def main(roots: List[str]):
    """
    Main function that collects stats for each root directory and prints the results.

    Args:
        roots (List[str]): A list of root directory paths as strings.
    """
    all_stats = collect_stats(roots)
    
    for stats in all_stats:
        print_stats(stats)

if __name__ == "__main__":
    from sys import argv

    if len(argv) < 2:
        logging.error("No root directories provided. Usage: script.py <root1>")
    else:
        main(argv[1:])
