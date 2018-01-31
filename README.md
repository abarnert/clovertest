# Requirements

* Linux, OS X, or other *nix environment
* Python 3.6+ (as `python3` on `PATH`)
* Complete Python stdlib
* `sqlite3` command-line tool (as `sqlite3` on `PATH`) (for tests only)
* nim 0.17+ (optional)

# Running

As specified, there should be `data` and `specs` directories in the application directory (that is, the place where the script is installed), not the current working directory. (I handled that by just `chdir`ing to the script's directory at start.)

The output will go into a sqlite3 database named `clover.db` in that same directory.

Note that if you run the script multiple times with the same data, you will get duplicate rows. (By default, sqlite3 maintains a hidden auto-int primary key, effectively a row ID, so each of these inserted rows ends up unique as far as it's concerned.)

There's also a nim implementation included, mainly just so I could play with the language (this seemed like a good problem for that). To compile it, you'll need to install the compiler (`brew install nim` should do it on OS X, and I think most Linux package managers have it), then `nim compile clover.nim`. This will generate a binary `clover` that you can run. This one requires that CWD be the source directory, doesn't log as nicely, and probably has additional bugs. It's also slower, despite being a compiled language (not surprising, given that most of the work happens inside Python modules like `csv` and `sqlite3`, not actual Python code).

# Data types

I'm using sqlite, which handles data types differently from many other databases. See [Manifest Typing](https://sqlite.org/datatype3.html) for details, but the short version is that types are associated with values, not columns. (Also, the database doesn't make fine distinctions between types that really only differ as far as implementation concerns rather than actual values.)

I do explicitly convert each value to the specified type anyway. Of course this wastes a bit of CPU time, but it's useful for error checking. For example, if a data file has `FOO` or `1.3` in an `INTEGER` field, sqlite would let us store that, only to cause problems down the line when we try to use it. (Or, more esoterically, depending on your sqlite version, storing an integer that's too big to fit into a signed 64-bit int may also cause problems down the line, and it's only detected at insert time if we've passed an `int` value to the DB-API methods.)

As for `BOOLEAN`, I don't think there is such a type in SQL (even if a few databases do have `BOOLEAN`, or other things like `BOOL` or `BIT`, as nonstandard extensions). I convert that to a Python `bool`. By default, the sqlite3 DB-API module will convert that back to the integers 1 and 0 for storage, so that's what ends up in the database. I could, of course, add handlers in the script to convert back to `True` and `False` on `SELECT`, but that won't affect what's stored in the database (or checked in my test script using the sqlite CLI), and we actually don't `SELECT` anything anywhere, so there didn't seem much point.

# Format ambiguities

It's not clear whether widths are in UTF-8 bytes, or Unicode characters. The former is obviously less useful, and also introduces the problem of dealing with truncated UTF-8 characters. But it's pretty easy to imagine an exported producing garbage files like that. Or one that truncated to byte width but didn't split up UTF-8 characters (replacing partial characters with space, maybe?). So in real life, we'd want to check which we're getting (e.g., create a field of width 1 and stick a CJK character in it and see what gets exported for us to process) and figure out what to do. (If we need to handle truncated characters, we obviously want to read in binary mode, split by bytes, and then decode for the database. We could use `errors='ignore'` to truncate a partial character at the end, but that would also hide invalid Unicode elsewhere in the string rather than failing on it, so it might be better to explicitly find bad UTF-8 at the end, chop it off, then decode strict. At any rate, I decided to go with treating widths as characters, not bytes, so none of this comes up.

The spec implies that we could read `sum(widths)+1` characters at a time rather than a line at a time. However, that seems more fragile than reading a line at a time (especially if humans might edit the data files), so I did the latter. That raises the question of what to do about excess characters at the end of a line. I chose to ignore them, but it might arguably be better to warn about them.

From the example, it looks like we're supposed to read `BOOLEAN` values from the data files as integer 0 and 1. What if there's a `T` or a `Y` there? I decided to treat those as errors, not as `True`. If there's a `23`, on the other hand, that's treated as `True`, by the usual "nonzero integers are truthy" rule.

# Error handling

Obviously if a format file is missing or can't be parsed or leads to an invalid table or something, we can just (log and) skip the data file.

But what if there's an error in the data file itself, after multiple valid rows? Rollback the whole file, skip the bad line and move on, or keep everything before the error but punt on the rest of the file? Depends on details of the use case. I went with the first option.

# Testing

The `tests.py` script removes the database, runs `clover.py`, and then uses the `sqlite3` CLI tool to verify that the output is as expected.

The `testformat1` table tests the error handling. Because Zaphod's `valid` of `Z` can't be interpreted as a `BOOLEAN`, that entire file should be rolled back, so only the three rows from the original example should appear.

The `superheroes` table should have 12 rows from the 4 files. The empty file should not have caused a problem. Many of the `identity` values will be truncated. Some of the names contain special characters--both ASCII punctuation that could screw up careless formatting code, and Unicode stuff like CJK and astral characters that could cause mojibake.

If the tests pass, nothing gets written to stdout (although the usual INFO logging of the names of the 6 files goes stderr), and the script exits successfully. Otherwise, you get an `AssertionError` traceback.

The `testnim.py` script does the same thing, but runs `clover` instead. You'll have to compile the `nim` implementaton manually.
