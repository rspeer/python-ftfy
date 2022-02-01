.. _config:

Configuring ftfy
================

The main functions of ftfy -- :func:`ftfy.fix_text` and :func:`ftfy.fix_and_explain` -- run text through a sequence of fixes. If the text changed, it will run them through again, so that you can be sure the output ends up in a standard form that will be unchanged by ftfy.

All the fixes are on by default, but you can pass in a configuration object or keyword options to turn them off. Check that the default fixes are appropriate for your use case. For example:

- You should set `unescape_html` to False if the output is meant to be interpreted as HTML.

- You should set `fix_character_width` to False if you want to preserve the spacing of CJK text.

- You should set `uncurl_quotes` to False if you want to preserve quotation marks with nice typography. You could even consider doing the opposite of `uncurl_quotes`, running `smartypants`_ on the result to make all the punctuation typographically nice.

- To be cautious and only fix mojibake when it can be fixed with a consistent sequence of encoding and decoding steps, you should set `decode_inconsistent_utf8` to False.

.. _smartypants: http://pythonhosted.org/smartypants/

If the only fix you need is to detect and repair decoding errors (mojibake), use the :func:`ftfy.fix_encoding` function directly. However, note that mojibake is often entangled with other issues such as the curliness of quotation marks, so limiting the process to this step might make some mojibake unfixable.

The TextFixerConfig object
--------------------------

The top-level functions of ftfy take a `config` argument that is an instance of :class:`ftfy.TextFixerConfig`. If this argument is None, the configuration will use its default values.

.. autoclass:: ftfy.TextFixerConfig()

Keyword arguments
-----------------
The top-level functions also accept keyword arguments in place of a `config` argument. Given these keyword arguments, they will pass them to the :class:`ftfy.TextFixerConfig` constructor, overriding the default values of those configuration options.
