import subprocess
import os
from nose.tools import eq_, assert_raises


# Get the filename of 'halibote.txt', which contains some mojibake about
# Harry Potter in Chinese
THIS_DIR = os.path.dirname(__file__)
TEST_FILENAME = os.path.join(THIS_DIR, 'halibote.txt')
CORRECT_OUTPUT = os.linesep.join(['【更新】《哈利波特》石堧卜才新婚娶初戀今痠逝', ''])
FAILED_OUTPUT = os.linesep.join([
    "ftfy error:",
    "This input couldn't be decoded as 'windows-1252'. We got the following error:",
    "",
    "    'charmap' codec can't decode byte 0x90 in position 5: character maps to <undefined>",
    "",
    "ftfy works best when its input is in a known encoding. You can use `ftfy -g`",
    "to guess, if you're desperate. Otherwise, give the encoding name with the",
    "`-e` option, such as `ftfy -e latin-1`.",
    "",
])


def get_command_output(args, stdin=None):
    return subprocess.check_output(args, stdin=stdin, stderr=subprocess.STDOUT, timeout=5).decode('utf-8')


def test_basic():
    output = get_command_output(['ftfy', TEST_FILENAME])
    eq_(output, CORRECT_OUTPUT)


def test_guess_bytes():
    output = get_command_output(['ftfy', '-g', TEST_FILENAME])
    eq_(output, CORRECT_OUTPUT)


def test_alternate_encoding():
    # The file isn't really in Windows-1252. But that's a problem ftfy
    # can fix, if it's allowed to be sloppy when reading the file.
    output = get_command_output(['ftfy', '-e', 'sloppy-windows-1252', TEST_FILENAME])
    eq_(output, CORRECT_OUTPUT)


def test_wrong_encoding():
    # It's more of a problem when the file doesn't actually decode.
    with assert_raises(subprocess.CalledProcessError) as context:
        get_command_output(['ftfy', '-e', 'windows-1252', TEST_FILENAME])
    e = context.exception
    eq_(e.output.decode('utf-8'), FAILED_OUTPUT)


def test_same_file():
    with assert_raises(subprocess.CalledProcessError) as context:
        get_command_output(['ftfy', TEST_FILENAME, '-o', TEST_FILENAME])
    e = context.exception
    assert e.output.decode('utf-8').startswith("ftfy error:\nCan't read and write the same file.")


def test_stdin():
    with open(TEST_FILENAME, 'rb') as infile:
        output = get_command_output(['ftfy'], stdin=infile)
        eq_(output, CORRECT_OUTPUT)

