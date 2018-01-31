# Requirements

* Linux, OS X, or other *nix environment
* Python 3.6+ (as `python3` on `PATH`)
* Complete Python stdlib
* `sqlite3` command-line tool (as `sqlite3` on `PATH`) (for tests only)

# Running

As specified, there should be `data` and `specs` directories in the application directory (that is, the place where the script is installed), not the current working directory. (I handled that by just `chdir`ing to the script's directory at start.)

The output will go into a sqlite3 database named `clover.db` in that same directory.

Note that if you run the script multiple times with the same data, you will get duplicate rows. (By default, sqlite3 maintains a hidden auto-int primary key, effectively a row ID, so each of these inserted rows ends up unique as far as it's concerned.)

The `tests.py` script removes the database, runs `clover.py`, and then uses the `sqlite3` CLI tool to verify that the output is as expected.

# Data Types

I'm using sqlite, which handles data types differently from many other databases. See [Manifest Typing](https://sqlite.org/datatype3.html) for details, but the short version is that types are associated with values, not columns. (Also, the database doesn't make fine distinctions between types that really only differ as far as implementation concerns rather than actual values.)

I do explicitly convert each value to the specified type anyway. Of course this wastes a bit of CPU time, but it's useful for error checking. For example, if a data file has `FOO` or `1.3` in an `INTEGER` field, sqlite would let us store that, only to cause problems down the line when we try to use it. (Or, more esoterically, depending on your sqlite version, storing an integer that's too big to fit into a signed 64-bit int may also cause problems down the line, and it's only detected at insert time if we've passed an `int` value to the DB-API methods.)

As for `BOOLEAN`, I don't think there is such a type in SQL (even if a few databases do have `BOOLEAN`, or other things like `BOOL` or `BIT`, as nonstandard extensions). I convert that to a Python `bool`. By default, the sqlite3 DB-API module will convert that back to the integers 1 and 0 for storage, so that's what ends up in the database. I could, of course, add handlers in the script to convert back to `True` and `False` on `SELECT`, but that won't affect what's stored in the database (or checked in my test script using the sqlite CLI), and we actually don't `SELECT` anything anywhere, so there didn't seem much point.
