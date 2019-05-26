# SQL-REMASTERED
By Re'em Kishnevsky And Maayan Kestenberg

## File Format
The table file format is as follows:
  * Each table directory contains a .col file for each column, and an additional .pointers file for each VARCHAR column.
    
    * .col Files:<br>
      .col files are merely the entire column values dumped into a file, one after the other.
      If the column is of a fixed-length type (INT | FLOAT | TIMESTAMP)
      then the offsets can be calculated by the formula: i*64. (Where i is the index of the desired value).
      If the column is of a variable-length type (VARCHAR)
      then the offsets cannot be calculated and thus stored in a .pointers file.
      INT, FLOAT and TIMESTAMP columns are stored as a .scol file (Static Column).<br>
      .col file format:
        ```
        [record(0)][record(1)]...[record(N-1)]
        ```
        N = Number of records in the table<br>
        record(X) = value of the X-th record in the column  
        
    * .pointers Files:<br>
      .pointers files contain a sequence of pointers (addresses / offsets). each pointer is a 64 bit unsigned int that is an address of a record value in the .col file that coresponds to the column - allowing for a maximum of about 18 quintillion varchar records in the column. In this way, the address of the i-th record of the column is the value of the pointer at the address i*64.<br>
      .pointers File Format:
        ```
        [pointer(1)][pointer(2)]...[pointer(N-1)]
        ```
        N = Number of records in the table<br>
        pointerX = 64 bit unsigned int address of the X-th record in the column<br>
        (first pointer points to record(1) since record(0) is always at offset 0).