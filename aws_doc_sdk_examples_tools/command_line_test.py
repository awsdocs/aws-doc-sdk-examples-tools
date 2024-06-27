import pytest
from unittest.mock import patch, mock_open
from argparse import Namespace
from .doc_gen import DocGen, MetadataError
from .command_line import doc_gen

@pytest.fixture
def mock_doc_gen():
    doc_gen =  DocGen.empty()
    doc_gen.errors._errors = [MetadataError(file="a.yaml", id="Error 1"), MetadataError(file="b.yaml", id="Error 2")]
    return doc_gen

@pytest.fixture
def patched_environment(mock_doc_gen):
    with patch('argparse.ArgumentParser.parse_args') as mock_parse_args, \
         patch('aws_doc_sdk_examples_tools.doc_gen.DocGen.empty', return_value=mock_doc_gen), \
         patch('aws_doc_sdk_examples_tools.doc_gen.DocGen.from_root'), \
         patch('json.dumps') as mock_json_dump, \
         patch('builtins.open', mock_open()):
        yield mock_parse_args, mock_json_dump

@pytest.mark.parametrize("strict,should_raise", [
    (True, True),
    (False, False)
])
def test_doc_gen_strict_option(strict, should_raise, patched_environment):
    mock_parse_args, mock_json_dump = patched_environment
    mock_args = Namespace(
        from_root=['/mock/path'],
        write_json='mock_output.json',
        strict=strict
    )
    mock_parse_args.return_value = mock_args

    if should_raise:
        with pytest.raises(Exception) as exc_info:
            doc_gen()
        assert "Errors found in metadata" in str(exc_info.value)
        assert "Error 1" in str(exc_info.value)
        assert "Error 2" in str(exc_info.value)
    else:
        doc_gen()