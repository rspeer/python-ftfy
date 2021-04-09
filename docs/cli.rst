Command-line usage
==================
ftfy can be used from the command line. By default, it takes UTF-8 input and
writes it to UTF-8 output, fixing problems in its Unicode as it goes.

Here's the usage documentation for the `ftfy` command:

.. code-block:: text

    usage: ftfy [-h] [-o OUTPUT] [-g] [-e ENCODING] [-n NORMALIZATION]
                [--preserve-entities]
                [filename]

    ftfy (fixes text for you), version 6.0

    positional arguments:
      filename              The file whose Unicode is to be fixed. Defaults to -,
                            meaning standard input.

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTPUT, --output OUTPUT
                            The file to output to. Defaults to -, meaning standard
                            output.
      -g, --guess           Ask ftfy to guess the encoding of your input. This is
                            risky. Overrides -e.
      -e ENCODING, --encoding ENCODING
                            The encoding of the input. Defaults to UTF-8.
      -n NORMALIZATION, --normalization NORMALIZATION
                            The normalization of Unicode to apply. Defaults to
                            NFC. Can be "none".
      --preserve-entities   Leave HTML entities as they are. The default is to
                            decode them, as long as no HTML tags have appeared in
                            the file.
