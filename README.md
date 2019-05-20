# SQL-REMASTERED
By Re'em Kishnevsky And Maayan Kestenberg

## File Format
The table file format is as follows:
  * Each table directory contains a file for each column,<br>
    the file format is determined by the column type (INT, FLOAT, TIMESTAMP, VARCHAR):
    * INT, FLOAT, TIMESTAMP:<br>
      These types are of a fixed length: 64 bits. Therefore their values can be simply dumped
      into a file and their offsets can be calculated by the formula: i*64.
      (Where i is the index of the desired value).

      INT, FLOAT and TIMESTAMP columns are stored as a .scol file (Static Column).<br>
      .scol File Format:
        ```
        [record0][record1]...[recordN]
        ```
        N = Number of records in the table<br>
        record = 64 bit numeric value 
    * VARCHAR:<br>
      VARCHAR records are of variable length, therefore, a sequence of pointers is at the top of the file. each pointer is a 64 bit unsigned int that is an offset of a record - allowing for a maximum of about 18 quintillion varchar records in the column. In this way, the offset of the i-th record of the column is the value of the pointer at the offset i*64.

      VARCHAR columns are stored as a .dcol file (Dynamic Column).<br>
      .dcol File Format:
        ```
        [pointer0][pointer1]...[pointerN][record0][record1]...[recordN]
        ```
        N = Number of records in the table<br>
        pointer = 64 bit unsassigned int<br>
        record = variable length string