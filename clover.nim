import db_sqlite
import future
import os
import parsecsv
import re
import streams
import strutils
import tables
import unicode

proc opendb() : DbConn =
  open("clover.db", nil, nil, nil)

type Datatype = enum
  Integer, Boolean, Text
  
type Format = tuple[column_name: string, width: int, datatype: Datatype]

# TODO: Not a real titlecase function, but works for us.
proc toTitleAscii(s: string) : string =
  s[0].toUpperAscii() & s[1..<s.len].toLowerAscii()

proc parseDatatype(name: string) : Datatype =
  parseEnum[Datatype](name.toTitleAscii())

proc parseRow(c: var CsvParser) : Format =
  let name = c.rowEntry("column name")
  let width = parseInt(c.rowEntry("width"))
  let datatype = parseDatatype(c.rowEntry("datatype"))
  (column_name: name, width: width, datatype: datatype)

proc readFormat(format: string) : seq[Format] =
  let path = "specs/" & format & ".csv"
  var c: CsvParser
  c.open(path)
  c.readHeaderRow()
  # TODO: Use header row instead of assuming order
  # TODO: Is there an idiomatic way to turn a while c.readRow() loop
  # into something that can be iterated in a comprehension (or otherwise
  # used immutably)? Or, alternatively, should readFormat be an iterator?
  var rows: seq[Format] = @[]
  while c.readRow():
    rows.add(parseRow(c))
  rows

proc makeTable(db: DbConn, tablename: string, format: seq[Format]) =
  # TODO: Comprehension
  var cols: seq[string] = @[]
  for col in format:
    let colstr = col.column_name & " " & $col.datatype
    cols.add(colstr)
  let colsbit = join(cols, ",\n")
  let query = "CREATE TABLE IF NOT EXISTS " & tablename & "(" & colsbit & ")"
  db.exec(sql(query))

# TODO: Iterate sequences (or, better, tables indexed by column name?) of
# (string or int or bool) instead of converting then converting back to string
iterator iterDataFile(fname: string, format: seq[Format]) : seq[string] =
  var s = newFileStream(fname, fmRead)
  if not isNil(s):
    var line = ""
    while s.readline(line):
      var pos = 0
      var row: seq[string] = @[]
      let uline = toRunes(line)
      for col in format:
        # TODO: There has to be a better way to slice unicode?
        let uvalue = uline[pos..<min(uline.len, pos+col.width)]
        let svalue = $uvalue;
        let value = svalue.strip(leading=false)
        case col.datatype
        of Text: row.add(value)
        of Integer: row.add($(parseInt(value.strip())))
        of Boolean: row.add($(parseInt(value.strip()))) # 0 or 1, not False or True
        pos = pos + col.width
      yield row
    s.close()

let rfname = re"data/(\w+?)_\d\d\d\d-\d\d-\d\d\.txt"
proc handleDataFile(db: DbConn, fname: string) =
  var matches: array[1, string]
  if fname.match(rfname, matches):
    let formatName = matches[0]
    let format = readFormat(formatName)
    makeTable(db, formatName, format)
    db.exec(sql"BEGIN")
    try:
      # TODO: comprehension
      var cols: seq[string] = @[]
      var vals: seq[string] = @[]
      for col in format:
        cols.add(col.column_name)
        vals.add("?")
      let query = "INSERT INTO " & formatName & " (" & join(cols, ", ") &
        ") VALUES (" & join(vals, ", ") & ")"
      echo query
      for row in iterDataFile(fname, format):
        echo row
        db.exec(sql(query), row)
      db.exec(sql"COMMIT")
    except:
      echo $(getCurrentException().name) & ": " & getCurrentExceptionMsg()
      db.exec(sql"ROLLBACK")
    
let db = opendb()
for fname in walkFiles("data/*.txt"):
  echo fname
  handleDataFile(db, fname)
for row in db.fastRows(sql"SELECT * FROM superheroes"):
  echo row
db.close()
