How can I avoid producing mojibake?
===================================

Read the Python Unicode HOWTO
-----------------------------

The `Python Unicode HOWTO`_ is a useful introduction to how to use Unicode correctly in Python. If you find yourself confused about the difference between bytes and characters, or you need to unlearn bad habits from Python 2, it's a great place to start.

.. _`Python Unicode HOWTO`: https://docs.python.org/3/howto/unicode.html

Assume UTF-8
------------

**Assume text is in UTF-8** unless you have a specific reason to believe it isn't.

In the 2020s, `UTF-8 is everywhere`_, especially in text meant to be transferred over the Internet. Most mojibake comes from decoding correct UTF-8 as if it were some other encoding.

.. _`UTF-8 is everywhere`: http://utf8everywhere.org/

In Python 3, you should use the Unicode string type (`str`) for all operations. You should open text files in UTF-8::

    openfile = open(filename, encoding='utf-8', errors='replace')

When you are specifically working with bytes and you need to turn them into text, you should decode them as UTF-8::

    text = bytebuffer.decode('utf-8', 'replace')

The exceptions, the cases where you're not using UTF-8, are few but relevant. If you're interacting with C APIs, you'll need to represent your text as bytes in the format the API expects. Windows APIs in particular expect UTF-16.

We're mostly past the dark days when encodings were "character maps" of 256 possible characters, one byte per character. An unfortunate thing that keeps them alive is Microsoft Excel, whose "Export" feature will pick a 256-character encoding *based on your computer's operating system and default language*. So:

Don't export CSVs from Excel
----------------------------

I know that I'm telling you not to do something that may seem like a requirement of doing your job. But **don't export CSV files from Excel** if you have any other choice. Though Excel CSVs look right on basic ASCII characters, on any other text, it either won't work or won't do what you want. Excel CSVs aren't even interoperable between different computers.

My recommendation is to use Google Sheets to create CSVs, and keep Excel files in .xlsx format so the Unicode won't be mangled.

If you must export a CSV-like file from Excel, you can find an option to tell Excel to export in "Unicode Text", and it will create a tab-separated UTF-16 file. This is not a very widely-used format, but at least it's not mojibake.

You can follow these `unwieldy directions from a SalesForce help article`_  to use Excel and Notepad to create a UTF-8 CSV. You can see why I don't recommend this process.

.. _`unwieldy directions from a SalesForce help article`: https://help.salesforce.com/articleView?id=000324657&type=1&mode=1

Don't use chardet
-----------------

Encoding detection on raw bytes is not a good idea. It was important in the '90s, during the rough transition to Unicode -- and the most popular way of doing it, ``chardet``, hasn't changed since the '90s.

A heuristic designed before there was multilingual social media, before there were emoji, is not going to work correctly in the 2020s.

When chardet sees the *correct* UTF-8 encoding of an emoji, it will have no idea what it's looking at, because it won't match anything in its training data. Often, it will guess that it's Turkish encoded in Windows-1254. On other reasonable text, it will guess the "iso-8859-2" encoding, an encoding that you'd very rarely see used intentionally. Because the problem is inherent to the design of chardet, it's not easily fixed.

chardet was built on the assumption that "encoding detection is language detection", which is no longer true. Web sites now contain text in multiple languages, and for the most part they use UTF-8 regardless of the language.

I've strengthened my recommendation from "don't trust chardet's output" to "don't use chardet", because there's no realistic way to use chardet without trusting its output. We've reached a situation where major Python packages such as ``requests`` assume that chardet is correct, and yet the changing nature of text means that chardet is more wrong with each passing year.

So how should you interpret raw bytes of text if you're not told what encoding they're in? As UTF-8. Text is UTF-8 until proven otherwise.

ASCII isn't extended
--------------------

A sign that something is about to go wrong with encodings is if a developer is talking about "extended ASCII".

ASCII is a set of 128 character codes (95 of them displayable). It has not had any new characters added to it since the backslash was added in 1967.

Because ASCII is a 7-bit encoding but our computers use 8-bit bytes, it seems clear that ASCII *could* be extended to assign a meaning to all 256 possible bytes. There are many different encodings that have done so, and they're all incompatible with one another, which is why treating bytes as characters as a bad idea and why we have Unicode now.

Many developers refer to one of these encodings as "extended ASCII", whose colloquial meaning is "the encoding of 256 characters that I learned first". Its meaning is completely dependent on the country you were in and the operating system you were using when you started programming:

- My "extended ASCII" when I learned to program was IBM codepage 437, the one that was used in US versions of MS-DOS.
- To many people, "extended ASCII" is Windows codepage 1252, which they'd find in the Character Map of their Windows 9x computer, at least if they were in North America or Western Europe.
- To others in other countries, it could be a different Windows codepage, such as 1251 (which contains Cyrillic letters) or 1250 (which contains a different set of accented letters for Eastern European languages).
- Or it might be Latin-1, the common name for the ISO-8859-1 standard that became the first 256 characters of Unicode. Latin-1 is easy to implement by accident, such as when you see byte C2 and assume it means Unicode codepoint U+00C2 -- what you get by incorrectly running `chr()` on each byte.

"Extended ASCII" doesn't specify which encoding you mean, and often indicates that you don't realize that different people are thinking of different sets of 256 characters.

Instead of "extended ASCII", say the name of the encoding such as "Latin-1", "Windows-1252", "Windows-1250", "codepage 437", or maybe "I don't know what it is but it looks right on my machine".

And then revise things so that you use UTF-8, which is still a superset of ASCII but can represent every Unicode character.
