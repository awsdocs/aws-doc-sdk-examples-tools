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

