from .labels import Example, Label, LabelSet, Sdk, Service, Snippet, select
from . import known_labels


def test_LabelSet_init():
    label_set = LabelSet([Label(name="a", value="1"), Label(name="b", value="2"), Label(name="a", value="11")])
    assert label_set['a'] == ["1", "11"]
    assert label_set['b'] == ["2"]


def test_LabelSet_iter():
    label_set = LabelSet([Label(name="a", value="1"), Label(name="b", value="2"), Label(name="a", value="11")])
    labels = [*label_set]
    assert labels == [Label(name="a", value="1"), Label(name="a", value="11"), Label(name="b", value="2")]


def test_LabelSet_cover():
    ls_snippet = LabelSet([Label(name="sdk", value="rust:1"), Label(name="service", value="ec2"), Label(name="action", value="DescribeInstance")])
    ls_sdk_rust = LabelSet([Label(name="sdk", value="rust:1")])
    ls_sdk_java = LabelSet([Label(name="sdk", value="java:2")])
    ls_example_describe_instance = LabelSet([Label(name="service", value="ec2"), Label(name="action", value="DescribeInstance")])

    assert ls_snippet.covers(ls_snippet) is True
    assert ls_snippet.covers(ls_sdk_rust) is True
    assert ls_snippet.covers(ls_sdk_java) is False
    assert ls_snippet.covers(ls_example_describe_instance) is True

    assert ls_sdk_rust.covers(ls_snippet) is False
    assert ls_sdk_rust.covers(ls_sdk_rust) is True
    assert ls_sdk_rust.covers(ls_sdk_java) is False
    assert ls_sdk_rust.covers(ls_example_describe_instance) is False

    assert ls_sdk_java.covers(ls_snippet) is False
    assert ls_sdk_java.covers(ls_sdk_rust) is False
    assert ls_sdk_java.covers(ls_sdk_java) is True
    assert ls_sdk_java.covers(ls_example_describe_instance) is False

    assert ls_example_describe_instance.covers(ls_snippet) is False
    assert ls_example_describe_instance.covers(ls_sdk_rust) is False
    assert ls_example_describe_instance.covers(ls_sdk_java) is False
    assert ls_example_describe_instance.covers(ls_example_describe_instance) is True


def test_select():
    snippets = [
        Snippet(id="rustv1.ec2.DescribeInstance", labels=[Label(name=known_labels.SDK, value="rust:v1"), Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="DescribeInstance")]),
        Snippet(id="rustv1.ec2.RebootInstance", labels=[Label(name=known_labels.SDK, value="rust:v1"), Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="RebootInstance")]),
        Snippet(id="rustv1.ses.Send", labels=[Label(name=known_labels.SDK, value="rust:v1"), Label(name=known_labels.SERVICE, value="ses"), Label(name=known_labels.ACTION, value="Send")]),
        Snippet(id="javav2.ec2.DescribeInstance", labels=[Label(name=known_labels.SDK, value="java:v2"), Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="DescribeInstance")]),
        Snippet(id="javav2.ec2.RebootInstance", labels=[Label(name=known_labels.SDK, value="java:v2"), Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="RebootInstance")]),
        Snippet(id="javav2.ses.Send", labels=[Label(name=known_labels.SDK, value="java:v2"), Label(name=known_labels.SERVICE, value="ses"), Label(name=known_labels.ACTION, value="Send")]),
    ]

    examples = [
        Example(id="ec2.describe_instance", title="Describe an &EC2; Instance", labels=[Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="DescribeInstance")]),
        Example(id="ec2.reboot_instance", title="Reboot an &EC2; Instance", labels=[Label(name=known_labels.SERVICE, value="ec2"), Label(name=known_labels.ACTION, value="RebootInstance")]),
        Example(id="ses.Send", title="Send a message to an &SES; queue", labels=[Label(name=known_labels.SERVICE, value="ses"), Label(name=known_labels.ACTION, value="RebootInstance")]),
        Example(id="s3.PutObject", title="Put an object into &S3; storage", labels=[Label(name=known_labels.SERVICE, value="s3"), Label(name=known_labels.ACTION, value="PutObject")])
    ]

    service = Service(name="ec2", labels=[Label(name=known_labels.SERVICE, value="ec2")])

    sdk = Sdk(language="rust", version="v1")

    example_snippets = select(snippets, examples[0])
    service_examples = select(examples, service)
    sdk_snippets = select(snippets, sdk)
    # sdk_examples = select_all(examples, sdk_snippets)

    assert example_snippets == frozenset([snippets[0], snippets[3]])
    assert service_examples == frozenset([examples[0], examples[1]])
    assert sdk_snippets == frozenset([snippets[0], snippets[1], snippets[2]])
