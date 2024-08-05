import os
import subprocess

import pytest

# Get the filename of 'face.txt', an example of mojibake
THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, "face.txt")
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
    with open(TEST_FILENAME, "rb") as infile:
        output = get_command_output(["ftfy"], stdin=infile)
        assert output == CORRECT_OUTPUT
