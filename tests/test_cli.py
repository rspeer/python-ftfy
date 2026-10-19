import os
import subprocess
from pathlib import Path

import pytest

# Get the filename of 'face.txt', an example of mojibake
THIS_DIR = Path(__file__).parent
TEST_FILENAME = THIS_DIR / "face.txt"
CORRECT_OUTPUT = os.linesep.join(["┒(⌣˛⌣)┎", ""])
FAILED_OUTPUT = os.linesep.join(
    [
        "ftfy error:",
        "This input couldn't be decoded as 'windows-1252'. We got the following error:",
        "",
        "    'charmap' codec can't decode byte 0x9d in position 4: character maps to <undefined>",
        "",
        "ftfy works best when its input is in a known encoding. You can use `ftfy -g`",
        "to guess, if you're desperate. Otherwise, give the encoding name with the",
        "`-e` option, such as `ftfy -e latin-1`.",
        "",
    ]
)


def get_command_output(args, stdin=None):
    return subprocess.check_output(args, stdin=stdin, stderr=subprocess.STDOUT, timeout=5).decode(
        "utf-8"
    )


def test_basic():
    output = get_command_output(["ftfy", TEST_FILENAME])
    assert output == CORRECT_OUTPUT


def test_guess_bytes():
    output = get_command_output(["ftfy", "-g", TEST_FILENAME])
    assert output == CORRECT_OUTPUT


def test_alternate_encoding():
    # The file isn't really in Windows-1252. But that's a problem ftfy
    # can fix, if it's allowed to be sloppy when reading the file.
    output = get_command_output(["ftfy", "-e", "sloppy-windows-1252", TEST_FILENAME])
    assert output == CORRECT_OUTPUT


def test_wrong_encoding():
    # It's more of a problem when the file doesn't actually decode.
    with pytest.raises(subprocess.CalledProcessError) as exception:
        get_command_output(["ftfy", "-e", "windows-1252", TEST_FILENAME])
    assert exception.value.output.decode("utf-8") == FAILED_OUTPUT


def test_same_file():
    with pytest.raises(subprocess.CalledProcessError) as exception:
        get_command_output(["ftfy", TEST_FILENAME, "-o", TEST_FILENAME])
    error = exception.value.output.decode("utf-8")
    assert error.startswith("ftfy error:")
    assert "Can't read and write the same file" in error


def test_stdin():
    with TEST_FILENAME.open("rb") as infile:
        output = get_command_output(["ftfy"], stdin=infile)
        assert output == CORRECT_OUTPUT


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        ([], '"café" <tag>&amp;\n&amp;\n'),
        (["--preserve-quotes"], "“café” <tag>&amp;\n&amp;\n"),
        (["--unescape-entities"], '"café" <tag>&\n&\n'),
        (["--preserve-entities"], '"café" <tag>&amp;\n&amp;\n'),
        (["--preserve-quotes", "--unescape-entities"], "“café” <tag>&\n&\n"),
        (["--preserve-quotes", "--preserve-entities"], "“café” <tag>&amp;\n&amp;\n"),
    ],
)
@pytest.mark.parametrize("use_stdin", [False, True])
def test_cli_fix_options(tmp_path, options, expected, use_stdin):
    source = tmp_path / "input.txt"
    source.write_text("“cafÃ©” <tag>&amp;\n&amp;\n", encoding="utf-8")
    if use_stdin:
        with source.open("rb") as infile:
            output = get_command_output(["ftfy", *options], stdin=infile)
    else:
        destination = tmp_path / "output.txt"
        get_command_output(["ftfy", *options, source, "-o", destination])
        output = destination.read_text(encoding="utf-8")
    if use_stdin:
        expected = expected.replace("\n", os.linesep)
    assert output == expected


def test_conflicting_entity_options(tmp_path):
    destination = tmp_path / "output.txt"
    destination.write_text("keep this file", encoding="utf-8")
    with pytest.raises(subprocess.CalledProcessError) as exception:
        get_command_output(
            ["ftfy", "--preserve-entities", "--unescape-entities", "-o", destination]
        )
    assert exception.value.returncode == 2
    assert "not allowed with argument" in exception.value.output.decode("utf-8")
    assert destination.read_text(encoding="utf-8") == "keep this file"
