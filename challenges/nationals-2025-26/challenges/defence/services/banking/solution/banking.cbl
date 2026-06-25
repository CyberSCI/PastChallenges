       *> CyberSci Nationals 2025/26
       *> 
       *> Dmitriy Beryoza (0xd13a)
       *> 
       *> Fixed version of the Banking service
       
       >>SOURCE FORMAT FREE
       IDENTIFICATION DIVISION.
       PROGRAM-ID. BANKING.
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCOUNT-FILE ASSIGN TO "accounts.csv"
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.
           *> Payment vulnerability fix
           *> Trace all variables that have "PAYEE" in the name to see logic added to make sure payee is registered
           SELECT PAYEE-FILE ASSIGN TO "payees.csv"
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS WS-PAYEE-FILE-STATUS.
       
       DATA DIVISION.
       FILE SECTION.
       FD ACCOUNT-FILE.
       01 ACCOUNT-LINE PIC X(256).

       FD PAYEE-FILE.
       01 PAYEE-LINE PIC X(128).

       WORKING-STORAGE SECTION.
       78 MAX-ACCOUNTS VALUE 1000.
       78 MAX-PAYEES VALUE 1000.
       78 MAX-TRANSACTION-AMOUNT VALUE 1000000.00.
       78 SCREEN-WIDTH VALUE 80.
       78 SCREEN-HEIGHT VALUE 25.
       78 KEY-UP VALUE 2003.
       78 KEY-DOWN VALUE 2004.
       78 KEY-ESC VALUE 2005.
       78 KEY-ENTER VALUE 0.
       78 KEY-RETURN VALUE 13.
       78 COLOR-BLACK VALUE 0.
       78 COLOR-BLUE VALUE 1.
       78 COLOR-GREEN VALUE 2.
       78 COLOR-CYAN VALUE 3.
       78 COLOR-RED VALUE 4.
       78 COLOR-MAGENTA VALUE 5.
       78 COLOR-YELLOW VALUE 6.
       78 COLOR-WHITE VALUE 7.
       
       01 WS-FILE-STATUS PIC XX VALUE "00".
       01 WS-PAYEE-FILE-STATUS PIC XX VALUE "00".
       01 WS-EOF PIC X VALUE "N".
       01 WS-PAYEE-EOF PIC X VALUE "N".
       01 WS-ACCOUNT-COUNT PIC 9(4) VALUE 0.
       01 WS-PAYEE-COUNT PIC 9(4) VALUE 0.
       01 WS-IDX PIC 9(4) VALUE 0.
       01 WS-JDX PIC 9(4) VALUE 0.
       01 WS-ROW PIC 99 VALUE 0.
       01 WS-COL PIC 99 VALUE 0.
       01 WS-FG-COLOR PIC 9 VALUE 7.
       01 WS-BG-COLOR PIC 9 VALUE 0.
       01 WS-TEXT-LENGTH PIC 99 VALUE 0.
       01 WS-PROMPT-ROW PIC 99 VALUE 0.
       01 WS-AUTHORIZED PIC X VALUE "N".
       01 WS-LOGIN-ABORT PIC X VALUE "N".
       01 WS-LOGIN-KEY PIC 9(4) VALUE 0.
       01 WS-KEYB-KEY PIC 9(4) VALUE 0.
       01 WS-DONE PIC X VALUE "N".
       01 WS-MENU-POS PIC 9 VALUE 1.
       01 WS-MENU-MAX PIC 9 VALUE 6.
       01 WS-MENU-KEY PIC 9(4) VALUE 0.
       01 WS-MENU-INPUT PIC X VALUE SPACE.
       01 WS-MENU-ANSI-1 PIC X VALUE SPACE.
       01 WS-MENU-ANSI-2 PIC X VALUE SPACE.
       01 WS-MENU-SELECTED PIC X VALUE "N".
       01 WS-CURRENT-INDEX PIC 9(4) VALUE 0.
       01 WS-SEARCH-INDEX PIC 9(4) VALUE 0.
       01 WS-SOURCE-INDEX PIC 9(4) VALUE 0.
       01 WS-DEST-INDEX PIC 9(4) VALUE 0.
       01 WS-PAYEE-INDEX PIC 9(4) VALUE 0.
       01 WS-SEARCH-PAYEE-INDEX PIC 9(4) VALUE 0.
       01 WS-SOURCE-TYPE PIC X VALUE SPACE.
       01 WS-DEST-TYPE PIC X VALUE SPACE.
       01 WS-ACCOUNT-TYPE PIC X VALUE SPACE.
       01 WS-ACCOUNT-VALID PIC X VALUE "N".
       01 WS-AMOUNT-RAW PIC X(12).
       01 WS-AMOUNT-DOLLARS PIC S9(10)V99 VALUE 0.
       01 WS-BALANCE-DOLLARS PIC S9(10)V99 VALUE 0.
       01 WS-MONEY-OUT PIC ZZZ,ZZZ,ZZ9.99.
       
       01 WS-CARD-IN PIC X(32) VALUE SPACES.
       01 WS-PIN-IN PIC X(32) VALUE SPACES.
       01 WS-SEARCH-CARD PIC X(32) VALUE SPACES.
       01 WS-CHOICE PIC X(1) VALUE SPACES.
       01 WS-DEST-CARD-IN PIC X(32) VALUE SPACES.
       01 WS-PAYEE-IN PIC X(16) VALUE SPACES.
       01 WS-SCREEN-TEXT PIC X(78) VALUE SPACES.
       01 WS-STATUS-TEXT PIC X(78) VALUE SPACES.
       
       01 WS-FRAME-BORDER.
           05 FILLER PIC X VALUE "+".
           05 FILLER PIC X(78) VALUE ALL "-".
           05 FILLER PIC X VALUE "+".
       
       01 WS-FRAME-BLANK.
           05 FILLER PIC X VALUE "|".
           05 FILLER PIC X(78) VALUE SPACES.
           05 FILLER PIC X VALUE "|".
       
           05 WS-AMOUNT-CHAR PIC X OCCURS 12 TIMES.
       
       01 WS-PARSE-FIELDS.
           05 WS-TOKEN-CARD PIC X(32).
           05 WS-TOKEN-PIN PIC X(16).
           05 WS-TOKEN-NAME PIC X(48).
           05 WS-TOKEN-CHECKING PIC X(24).
           05 WS-TOKEN-SAVINGS PIC X(24).

       01 WS-PAYEE-PARSE-FIELDS.
           05 WS-TOKEN-PAYEE-ID PIC X(16).
           05 WS-TOKEN-PAYEE-NAME PIC X(64).
       
       01 ACCOUNT-TABLE.
           05 ACCOUNT-ENTRY OCCURS MAX-ACCOUNTS TIMES.
               10 ACCT-CARD PIC X(16).
               10 ACCT-PIN PIC X(8).
               10 ACCT-NAME PIC X(40).
               10 ACCT-CHECKING PIC S9(10)V99 VALUE 0.
               10 ACCT-SAVINGS PIC S9(10)V99 VALUE 0.

       01 PAYEE-TABLE.
           05 PAYEE-ENTRY OCCURS MAX-PAYEES TIMES.
               10 PAYEE-ID PIC X(12).
               10 PAYEE-NAME PIC X(40).
       
       *> This is not needed
       *> 01 WS-TRANSFER-DOLLARS PIC S9(4)V99 VALUE 0.

       SCREEN SECTION.
           01 CLEAR-SCREEN.
           05 BLANK SCREEN.
       
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           SET ENVIRONMENT "TERM" TO "xterm"
           SET ENVIRONMENT "COB_SCREEN_EXCEPTIONS" TO "Y"
           SET ENVIRONMENT "COB_SCREEN_ESC" TO "Y"

           PERFORM LOAD-ACCOUNTS
           IF WS-ACCOUNT-COUNT = 0
               PERFORM DRAW-FRAME
               MOVE "Unable to start ATM: no accounts loaded." TO WS-SCREEN-TEXT
               MOVE 12 TO WS-ROW
               PERFORM SET-COLOR-ERROR
               PERFORM PUT-CENTERED
               PERFORM PAUSE-SCREEN
               STOP RUN
           END-IF

           PERFORM LOAD-PAYEES

           PERFORM LOGIN-PROCEDURE
       
           IF WS-LOGIN-ABORT = "Y"
               STOP RUN
           END-IF

           IF WS-AUTHORIZED NOT = "Y"
               MOVE 1 TO RETURN-CODE
               STOP RUN
           END-IF

           PERFORM ATM-SESSION UNTIL WS-DONE = "Y"
       
           STOP RUN.
       
       LOAD-ACCOUNTS.
           MOVE "N" TO WS-EOF
           OPEN INPUT ACCOUNT-FILE
           IF WS-FILE-STATUS NOT = "00"
               EXIT PARAGRAPH
           END-IF
       
           PERFORM UNTIL WS-EOF = "Y"
               READ ACCOUNT-FILE
                    AT END
                        MOVE "Y" TO WS-EOF
                    NOT AT END
                        IF ACCOUNT-LINE NOT = SPACES
                            AND ACCOUNT-LINE(1:1) NOT = "#"
                            PERFORM PARSE-ACCOUNT-LINE
                        END-IF
               END-READ
           END-PERFORM
           CLOSE ACCOUNT-FILE.
       
       PARSE-ACCOUNT-LINE.
           IF WS-ACCOUNT-COUNT >= MAX-ACCOUNTS
               EXIT PARAGRAPH
           END-IF
       
           INITIALIZE WS-PARSE-FIELDS
           UNSTRING ACCOUNT-LINE DELIMITED BY ","
               INTO WS-TOKEN-CARD
                     WS-TOKEN-PIN
                     WS-TOKEN-NAME
                     WS-TOKEN-CHECKING
                     WS-TOKEN-SAVINGS
           END-UNSTRING
       
           ADD 1 TO WS-ACCOUNT-COUNT
           MOVE FUNCTION TRIM(WS-TOKEN-CARD)
               TO ACCT-CARD(WS-ACCOUNT-COUNT)
           MOVE FUNCTION TRIM(WS-TOKEN-PIN)
               TO ACCT-PIN(WS-ACCOUNT-COUNT)
           MOVE FUNCTION TRIM(WS-TOKEN-NAME)
               TO ACCT-NAME(WS-ACCOUNT-COUNT)
           COMPUTE ACCT-CHECKING(WS-ACCOUNT-COUNT) ROUNDED =
               FUNCTION NUMVAL(WS-TOKEN-CHECKING)
           COMPUTE ACCT-SAVINGS(WS-ACCOUNT-COUNT) ROUNDED =
               FUNCTION NUMVAL(WS-TOKEN-SAVINGS)
       
           .

       LOAD-PAYEES.
           MOVE "N" TO WS-PAYEE-EOF
           OPEN INPUT PAYEE-FILE
           IF WS-PAYEE-FILE-STATUS NOT = "00"
               EXIT PARAGRAPH
           END-IF

           PERFORM UNTIL WS-PAYEE-EOF = "Y"
               READ PAYEE-FILE
                    AT END
                        MOVE "Y" TO WS-PAYEE-EOF
                    NOT AT END
                        IF PAYEE-LINE NOT = SPACES
                            AND PAYEE-LINE(1:1) NOT = "#"
                            PERFORM PARSE-PAYEE-LINE
                        END-IF
               END-READ
           END-PERFORM
           CLOSE PAYEE-FILE.

       PARSE-PAYEE-LINE.
           IF WS-PAYEE-COUNT >= MAX-PAYEES
               EXIT PARAGRAPH
           END-IF

           INITIALIZE WS-PAYEE-PARSE-FIELDS
           UNSTRING PAYEE-LINE DELIMITED BY ","
               INTO WS-TOKEN-PAYEE-ID
                    WS-TOKEN-PAYEE-NAME
           END-UNSTRING

           ADD 1 TO WS-PAYEE-COUNT
           MOVE FUNCTION TRIM(WS-TOKEN-PAYEE-ID)
               TO PAYEE-ID(WS-PAYEE-COUNT)
           MOVE FUNCTION TRIM(WS-TOKEN-PAYEE-NAME)
               TO PAYEE-NAME(WS-PAYEE-COUNT).

       LOGIN-PROCEDURE.
           MOVE 0 TO WS-CURRENT-INDEX
           MOVE "N" TO WS-LOGIN-ABORT
           MOVE SPACES TO WS-CARD-IN
           MOVE SPACES TO WS-PIN-IN

           PERFORM WELCOME-SCREEN
           MOVE 0 TO WS-LOGIN-KEY
           ACCEPT WS-CARD-IN LINE 18 COL 35
                ON EXCEPTION
                    MOVE COB-CRT-STATUS TO WS-LOGIN-KEY
           END-ACCEPT
           IF WS-LOGIN-KEY = KEY-ESC
               MOVE "Y" TO WS-LOGIN-ABORT
               EXIT PARAGRAPH
           END-IF

           MOVE 0 TO WS-LOGIN-KEY
           ACCEPT WS-PIN-IN LINE 20 COL 35
                ON EXCEPTION
                    MOVE COB-CRT-STATUS TO WS-LOGIN-KEY
           END-ACCEPT
           IF WS-LOGIN-KEY = KEY-ESC
               MOVE "Y" TO WS-LOGIN-ABORT
               EXIT PARAGRAPH
           END-IF

           MOVE WS-CARD-IN TO WS-SEARCH-CARD
           PERFORM FIND-ACCOUNT
           MOVE WS-SEARCH-INDEX TO WS-CURRENT-INDEX

           IF WS-CURRENT-INDEX > 0
                AND FUNCTION TRIM(WS-PIN-IN) =
                    FUNCTION TRIM(ACCT-PIN(WS-CURRENT-INDEX))
                MOVE "Y" TO WS-AUTHORIZED
           ELSE
                MOVE "Invalid card number or PIN." TO WS-STATUS-TEXT
                PERFORM LOGIN-STATUS-SCREEN
           END-IF.
       
       FIND-ACCOUNT.
           MOVE 0 TO WS-SEARCH-INDEX
           PERFORM VARYING WS-IDX FROM 1 BY 1
               UNTIL WS-IDX > WS-ACCOUNT-COUNT OR WS-SEARCH-INDEX > 0
               IF FUNCTION TRIM(WS-SEARCH-CARD) =
                    FUNCTION TRIM(ACCT-CARD(WS-IDX))
                    MOVE WS-IDX TO WS-SEARCH-INDEX
               END-IF
           END-PERFORM.
       
       ATM-SESSION.
           MOVE "N" TO WS-MENU-SELECTED
           PERFORM UNTIL WS-MENU-SELECTED = "Y" OR WS-DONE = "Y"
               PERFORM MENU-SCREEN
               MOVE 0 TO WS-MENU-KEY
               MOVE SPACE TO WS-MENU-INPUT
               ACCEPT WS-MENU-INPUT LINE 23 COL 78 WITH AUTO
                    ON EXCEPTION
                        MOVE COB-CRT-STATUS TO WS-MENU-KEY
                    NOT ON EXCEPTION
                        MOVE KEY-ENTER TO WS-MENU-KEY
               END-ACCEPT
               EVALUATE WS-MENU-KEY
                    WHEN KEY-UP
                        IF WS-MENU-POS > 1
                            SUBTRACT 1 FROM WS-MENU-POS
                        ELSE
                            MOVE WS-MENU-MAX TO WS-MENU-POS
                        END-IF
                    WHEN KEY-DOWN
                        IF WS-MENU-POS < WS-MENU-MAX
                            ADD 1 TO WS-MENU-POS
                        ELSE
                            MOVE 1 TO WS-MENU-POS
                        END-IF
                    WHEN KEY-ESC
                        PERFORM READ-ANSI-MENU-KEY
                    WHEN KEY-ENTER
                        MOVE "Y" TO WS-MENU-SELECTED
                    WHEN KEY-RETURN
                        MOVE "Y" TO WS-MENU-SELECTED
                    WHEN OTHER
                        CONTINUE
               END-EVALUATE
           END-PERFORM

           IF WS-MENU-SELECTED = "Y"
               PERFORM HANDLE-MENU-SELECTION
           END-IF.

       READ-ANSI-MENU-KEY.
           MOVE SPACE TO WS-MENU-ANSI-1
           MOVE SPACE TO WS-MENU-ANSI-2
           ACCEPT WS-MENU-ANSI-1 LINE 23 COL 78 WITH AUTO
                ON EXCEPTION
                    CONTINUE
           END-ACCEPT
           ACCEPT WS-MENU-ANSI-2 LINE 23 COL 78 WITH AUTO
                ON EXCEPTION
                    CONTINUE
           END-ACCEPT

           IF WS-MENU-ANSI-1 = "[" AND WS-MENU-ANSI-2 = "A"
               IF WS-MENU-POS > 1
                    SUBTRACT 1 FROM WS-MENU-POS
               ELSE
                    MOVE WS-MENU-MAX TO WS-MENU-POS
               END-IF
           END-IF

           IF WS-MENU-ANSI-1 = "[" AND WS-MENU-ANSI-2 = "B"
               IF WS-MENU-POS < WS-MENU-MAX
                    ADD 1 TO WS-MENU-POS
               ELSE
                    MOVE 1 TO WS-MENU-POS
               END-IF
           END-IF.

       HANDLE-MENU-SELECTION.
           EVALUATE WS-MENU-POS
               WHEN 1
                    PERFORM DEPOSIT-MONEY
               WHEN 2
                    PERFORM WITHDRAW-MONEY
               WHEN 3
                    PERFORM TRANSFER-MONEY
               WHEN 4
                    PERFORM SEND-MONEY
               WHEN 5
                    PERFORM PAY-BILL
               WHEN 6
                    MOVE "Y" TO WS-DONE
           END-EVALUATE.
       
       DRAW-FRAME.
           DISPLAY CLEAR-SCREEN
           DISPLAY WS-FRAME-BORDER LINE 1 COL 1
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           PERFORM VARYING WS-ROW FROM 2 BY 1
               UNTIL WS-ROW >= SCREEN-HEIGHT
               DISPLAY WS-FRAME-BLANK LINE WS-ROW COL 1
                    FOREGROUND-COLOR COLOR-CYAN
                    BACKGROUND-COLOR COLOR-BLACK
       END-PERFORM
           DISPLAY WS-FRAME-BORDER LINE 25 COL 1
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK.
       
       PUT-CENTERED.
           MOVE FUNCTION LENGTH(FUNCTION TRIM(WS-SCREEN-TEXT))
               TO WS-TEXT-LENGTH
           IF WS-TEXT-LENGTH = 0
               MOVE 1 TO WS-TEXT-LENGTH
           END-IF
           COMPUTE WS-COL = ((SCREEN-WIDTH - WS-TEXT-LENGTH) / 2) + 1
           IF WS-COL < 2
               MOVE 2 TO WS-COL
           END-IF
           DISPLAY FUNCTION TRIM(WS-SCREEN-TEXT) LINE WS-ROW COL WS-COL
               FOREGROUND-COLOR WS-FG-COLOR
               BACKGROUND-COLOR WS-BG-COLOR.

       SET-COLOR-NORMAL.
           MOVE COLOR-WHITE TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-TITLE.
           MOVE COLOR-YELLOW TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-BRAND.
           MOVE COLOR-CYAN TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-SUCCESS.
           MOVE COLOR-GREEN TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-ERROR.
           MOVE COLOR-RED TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-PROMPT.
           MOVE COLOR-CYAN TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.

       SET-COLOR-MUTED.
           MOVE COLOR-MAGENTA TO WS-FG-COLOR
           MOVE COLOR-BLACK TO WS-BG-COLOR.
       
       PAUSE-SCREEN.
           MOVE "Press ENTER to continue." TO WS-SCREEN-TEXT
           MOVE 23 TO WS-ROW
           PERFORM SET-COLOR-MUTED
           PERFORM PUT-CENTERED
           MOVE SPACES TO WS-CHOICE
           ACCEPT WS-CHOICE LINE 24 COL 4.
       
       WELCOME-SCREEN.
           PERFORM DRAW-FRAME
           PERFORM SET-COLOR-BRAND
           MOVE "'||'''|, '||'''|," TO WS-SCREEN-TEXT
           MOVE 5 TO WS-ROW
           PERFORM PUT-CENTERED
           MOVE " ||   ||  ||   ||" TO WS-SCREEN-TEXT
           MOVE 6 TO WS-ROW
           PERFORM PUT-CENTERED
           MOVE " ||...|'  ||;;;;" TO WS-SCREEN-TEXT
           MOVE 7 TO WS-ROW
           PERFORM PUT-CENTERED
           MOVE " || \\    ||   ||" TO WS-SCREEN-TEXT
           MOVE 8 TO WS-ROW
           PERFORM PUT-CENTERED
           MOVE ".||  \\. .||...|'" TO WS-SCREEN-TEXT
           MOVE 9 TO WS-ROW
           PERFORM PUT-CENTERED
       
           PERFORM SET-COLOR-TITLE
           MOVE "Welcome to Resurrection Bank ATM!" TO WS-SCREEN-TEXT
           MOVE 11 TO WS-ROW
           PERFORM PUT-CENTERED
           PERFORM SET-COLOR-NORMAL
           MOVE "The first meteor-proof bank on Earth (R)" TO WS-SCREEN-TEXT
           MOVE 13 TO WS-ROW
           PERFORM PUT-CENTERED
           PERFORM SET-COLOR-PROMPT
           MOVE "Log in to begin:" TO WS-SCREEN-TEXT
           MOVE 15 TO WS-ROW
           PERFORM PUT-CENTERED
       
           DISPLAY "Card number:" LINE 18 COL 22
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[                                ]" LINE 18 COL 34
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "PIN:" LINE 20 COL 22
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[                                ]" LINE 20 COL 34
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           PERFORM SET-COLOR-MUTED
           MOVE "Press ESC to cancel." TO WS-SCREEN-TEXT
           MOVE 22 TO WS-ROW
           PERFORM PUT-CENTERED.
       
       LOGIN-STATUS-SCREEN.
           PERFORM WELCOME-SCREEN
           MOVE WS-STATUS-TEXT TO WS-SCREEN-TEXT
           MOVE 22 TO WS-ROW
           PERFORM SET-COLOR-ERROR
           PERFORM PUT-CENTERED
           PERFORM PAUSE-SCREEN.
       
       DRAW-ACCOUNT-SCREEN.
           PERFORM DRAW-FRAME

           DISPLAY "'||'''|, '||'''|," LINE 2 COL 58
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY " ||   ||  ||   ||" LINE 3 COL 58
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY " ||...|'  ||;;;;" LINE 4 COL 58
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY " || \\    ||   ||" LINE 5 COL 58
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY ".||  \\. .||...|'" LINE 6 COL 58
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK

           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Account : " DELIMITED BY SIZE
               FUNCTION TRIM(ACCT-CARD(WS-CURRENT-INDEX)) DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           DISPLAY FUNCTION TRIM(WS-SCREEN-TEXT) LINE 2 COL 4
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK

           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Customer: " DELIMITED BY SIZE
               FUNCTION TRIM(ACCT-NAME(WS-CURRENT-INDEX)) DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           DISPLAY FUNCTION TRIM(WS-SCREEN-TEXT) LINE 3 COL 4
               FOREGROUND-COLOR COLOR-WHITE
               BACKGROUND-COLOR COLOR-BLACK
           
           *> This is not needed, it may be hiding calculation errors
           *> MOVE FUNCTION ABS(ACCT-CHECKING(WS-CURRENT-INDEX)) TO ACCT-CHECKING(WS-CURRENT-INDEX)
           MOVE ACCT-CHECKING(WS-CURRENT-INDEX) TO WS-BALANCE-DOLLARS
           PERFORM FORMAT-MONEY
           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Checking: $" DELIMITED BY SIZE
               FUNCTION TRIM(WS-MONEY-OUT) DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           DISPLAY FUNCTION TRIM(WS-SCREEN-TEXT) LINE 4 COL 4
               FOREGROUND-COLOR COLOR-GREEN
               BACKGROUND-COLOR COLOR-BLACK

           *> This is not needed, it may be hiding calculation errors
           *> MOVE FUNCTION ABS(ACCT-SAVINGS(WS-CURRENT-INDEX)) TO ACCT-SAVINGS(WS-CURRENT-INDEX)
           MOVE ACCT-SAVINGS(WS-CURRENT-INDEX) TO WS-BALANCE-DOLLARS
           PERFORM FORMAT-MONEY
           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Savings : $" DELIMITED BY SIZE
               FUNCTION TRIM(WS-MONEY-OUT) DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           DISPLAY FUNCTION TRIM(WS-SCREEN-TEXT) LINE 5 COL 4
               FOREGROUND-COLOR COLOR-GREEN
               BACKGROUND-COLOR COLOR-BLACK

           DISPLAY "------------------------------------------------------------------------"
               LINE 7 COL 5
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK.
       
       MENU-SCREEN.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Main Menu" LINE 8 COL 35
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           IF WS-MENU-POS = 1
               DISPLAY "> Deposit                      " LINE 10 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Deposit                      " LINE 10 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF

           IF WS-MENU-POS = 2
               DISPLAY "> Withdraw                     " LINE 11 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Withdraw                     " LINE 11 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF

           IF WS-MENU-POS = 3
               DISPLAY "> Transfer                     " LINE 12 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Transfer                     " LINE 12 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF

           IF WS-MENU-POS = 4
               DISPLAY "> Send money                   " LINE 13 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Send money                   " LINE 13 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF

           IF WS-MENU-POS = 5
               DISPLAY "> Pay a bill                   " LINE 14 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Pay a bill                   " LINE 14 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF

           IF WS-MENU-POS = 6
               DISPLAY "> Exit                         " LINE 16 COL 25
                    FOREGROUND-COLOR COLOR-BLACK
                    BACKGROUND-COLOR COLOR-YELLOW
           ELSE
               DISPLAY "  Exit                         " LINE 16 COL 25
                    FOREGROUND-COLOR COLOR-WHITE
                    BACKGROUND-COLOR COLOR-BLACK
           END-IF
           MOVE "Use UP/DOWN arrows to choose. Press ENTER to select."
               TO WS-SCREEN-TEXT
           MOVE 19 TO WS-ROW
           PERFORM SET-COLOR-PROMPT
           PERFORM PUT-CENTERED.
       
       ASK-ACCOUNT-TYPE.
           MOVE "N" TO WS-ACCOUNT-VALID
           MOVE SPACE TO WS-ACCOUNT-TYPE
           DISPLAY "Account (C=checking, S=savings):" LINE WS-PROMPT-ROW COL 12
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[ ]" LINE WS-PROMPT-ROW COL 45
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           ACCEPT WS-CHOICE LINE WS-PROMPT-ROW COL 46
           MOVE FUNCTION UPPER-CASE(WS-CHOICE) TO WS-CHOICE
       
           IF WS-CHOICE(1:1) = "C" OR WS-CHOICE(1:1) = "S"
               MOVE WS-CHOICE(1:1) TO WS-ACCOUNT-TYPE
               MOVE "Y" TO WS-ACCOUNT-VALID
           ELSE
               DISPLAY "Unknown account type." LINE 21 COL 28
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
           END-IF.
       
       GET-AMOUNT.
           DISPLAY "Amount (dollars):" LINE WS-PROMPT-ROW COL 12
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[            ]" LINE WS-PROMPT-ROW COL 39
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           ACCEPT WS-AMOUNT-RAW LINE WS-PROMPT-ROW COL 40.

           COMPUTE WS-AMOUNT-DOLLARS = FUNCTION NUMVAL(WS-AMOUNT-RAW).
       
       DEPOSIT-MONEY.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Deposit" LINE 8 COL 36
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Choose the destination account." LINE 10 COL 24
               FOREGROUND-COLOR COLOR-WHITE
               BACKGROUND-COLOR COLOR-BLACK
           MOVE 12 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID = "Y"
               MOVE 14 TO WS-PROMPT-ROW
               PERFORM GET-AMOUNT

               MOVE "Insert the money and enter C to continue or E to exit [C/E]:" TO WS-SCREEN-TEXT
               MOVE 17 TO WS-ROW
               PERFORM SET-COLOR-MUTED
               PERFORM PUT-CENTERED
               MOVE SPACES TO WS-CHOICE
               ACCEPT WS-CHOICE LINE 17 COL 72
               MOVE FUNCTION UPPER-CASE(WS-CHOICE) TO WS-CHOICE

               IF WS-CHOICE(1:1) NOT = "C"
                   PERFORM DRAW-ACCOUNT-SCREEN

                   EXIT PARAGRAPH
               ELSE
                   *> Deposit vulnerability fix
                   *> Only add the amount after user decided to go ahead with deposit
                   IF WS-ACCOUNT-TYPE = "C"
                       ADD WS-AMOUNT-DOLLARS TO
                           ACCT-CHECKING(WS-CURRENT-INDEX)
                   ELSE
                       ADD WS-AMOUNT-DOLLARS TO
                           ACCT-SAVINGS(WS-CURRENT-INDEX)
                   END-IF

                   PERFORM DRAW-ACCOUNT-SCREEN
                   
                   DISPLAY "Deposit complete." LINE 19 COL 31
                       FOREGROUND-COLOR COLOR-GREEN
                       BACKGROUND-COLOR COLOR-BLACK
               END-IF
           END-IF
           PERFORM PAUSE-SCREEN.
       
       WITHDRAW-MONEY.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Withdraw" LINE 8 COL 36
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Choose the account to withdraw from." LINE 10 COL 21
               FOREGROUND-COLOR COLOR-WHITE
               BACKGROUND-COLOR COLOR-BLACK
           MOVE 12 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID = "Y"
               MOVE 14 TO WS-PROMPT-ROW
               PERFORM GET-AMOUNT

               *> Withdrawal vulnerability fix
               *> Make sure the amount is positive
               IF WS-AMOUNT-DOLLARS < 0
                   DISPLAY "Amount must be positive." LINE 17 COL 31
                       FOREGROUND-COLOR COLOR-RED
                       BACKGROUND-COLOR COLOR-BLACK
                   PERFORM PAUSE-SCREEN
                   EXIT PARAGRAPH
               END-IF

               PERFORM LOAD-SOURCE-BALANCE
               IF WS-AMOUNT-DOLLARS > WS-BALANCE-DOLLARS
                   DISPLAY "Insufficient funds." LINE 17 COL 31
                       FOREGROUND-COLOR COLOR-RED
                       BACKGROUND-COLOR COLOR-BLACK
               ELSE
                   IF WS-ACCOUNT-TYPE = "C"
                       SUBTRACT WS-AMOUNT-DOLLARS FROM
                           ACCT-CHECKING(WS-CURRENT-INDEX)
                   ELSE
                       SUBTRACT WS-AMOUNT-DOLLARS FROM
                           ACCT-SAVINGS(WS-CURRENT-INDEX)
                   END-IF

                   PERFORM DRAW-ACCOUNT-SCREEN

                   DISPLAY "Please take your cash." LINE 17 COL 29
                       FOREGROUND-COLOR COLOR-GREEN
                       BACKGROUND-COLOR COLOR-BLACK
               END-IF
           END-IF
           PERFORM PAUSE-SCREEN.
       
       LOAD-SOURCE-BALANCE.
           IF WS-ACCOUNT-TYPE = "C"
               MOVE ACCT-CHECKING(WS-CURRENT-INDEX) TO WS-BALANCE-DOLLARS
           ELSE
               MOVE ACCT-SAVINGS(WS-CURRENT-INDEX) TO WS-BALANCE-DOLLARS
           END-IF.
       
       TRANSFER-MONEY.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Transfer" LINE 8 COL 36
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Move money between checking and savings." LINE 10 COL 20
               FOREGROUND-COLOR COLOR-WHITE
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Source account" LINE 12 COL 31
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           MOVE 14 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID NOT = "Y"
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF
           MOVE WS-ACCOUNT-TYPE TO WS-SOURCE-TYPE
           MOVE WS-CURRENT-INDEX TO WS-SOURCE-INDEX

           MOVE WS-CURRENT-INDEX TO WS-DEST-INDEX
           IF WS-SOURCE-TYPE = "C"
               MOVE "S" TO WS-DEST-TYPE
               DISPLAY "Destination: savings" LINE 16 COL 29
                   FOREGROUND-COLOR COLOR-MAGENTA
                   BACKGROUND-COLOR COLOR-BLACK
           ELSE
               MOVE "C" TO WS-DEST-TYPE
               DISPLAY "Destination: checking" LINE 16 COL 28
                   FOREGROUND-COLOR COLOR-MAGENTA
                   BACKGROUND-COLOR COLOR-BLACK
           END-IF
       
           MOVE 20 TO WS-PROMPT-ROW
           PERFORM GET-AMOUNT
       
           IF WS-SOURCE-TYPE = "C"
               *> Transfer vulnerability fix
               *> Make sure the amount is not higher than the account balance
               IF WS-AMOUNT-DOLLARS > ACCT-CHECKING(WS-SOURCE-INDEX)
                   DISPLAY "Amount is too large." LINE 17 COL 31
                       FOREGROUND-COLOR COLOR-RED
                       BACKGROUND-COLOR COLOR-BLACK
                   PERFORM PAUSE-SCREEN
                   EXIT PARAGRAPH
               END-IF

               SUBTRACT WS-AMOUNT-DOLLARS FROM
                   ACCT-CHECKING(WS-SOURCE-INDEX)
               ADD WS-AMOUNT-DOLLARS TO ACCT-SAVINGS(WS-DEST-INDEX)
           ELSE
               IF WS-AMOUNT-DOLLARS > ACCT-SAVINGS(WS-SOURCE-INDEX)
                   DISPLAY "Amount is too large." LINE 17 COL 31
                       FOREGROUND-COLOR COLOR-RED
                       BACKGROUND-COLOR COLOR-BLACK
                   PERFORM PAUSE-SCREEN
                   EXIT PARAGRAPH
               END-IF

               SUBTRACT WS-AMOUNT-DOLLARS FROM
                   ACCT-SAVINGS(WS-SOURCE-INDEX)
               ADD WS-AMOUNT-DOLLARS TO ACCT-CHECKING(WS-DEST-INDEX)
           END-IF
       
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Transfer complete." LINE 10 COL 31
               FOREGROUND-COLOR COLOR-GREEN
               BACKGROUND-COLOR COLOR-BLACK
           IF WS-SOURCE-TYPE = "C"
               DISPLAY "Moved from checking to savings." LINE 12 COL 24
                   FOREGROUND-COLOR COLOR-WHITE
                   BACKGROUND-COLOR COLOR-BLACK
           ELSE
               DISPLAY "Moved from savings to checking." LINE 12 COL 24
                   FOREGROUND-COLOR COLOR-WHITE
                   BACKGROUND-COLOR COLOR-BLACK
           END-IF
           PERFORM PAUSE-SCREEN.

       SEND-MONEY.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Send money" LINE 8 COL 35
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Send money to another cardholder." LINE 10 COL 23
               FOREGROUND-COLOR COLOR-WHITE
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "Source account" LINE 12 COL 31
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           MOVE 14 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID NOT = "Y"
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF
           MOVE WS-ACCOUNT-TYPE TO WS-SOURCE-TYPE
           MOVE WS-CURRENT-INDEX TO WS-SOURCE-INDEX

           MOVE SPACES TO WS-DEST-CARD-IN
           DISPLAY "Destination card:" LINE 16 COL 12
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[                                ]" LINE 16 COL 32
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           ACCEPT WS-DEST-CARD-IN LINE 16 COL 33

           MOVE WS-DEST-CARD-IN TO WS-SEARCH-CARD
           PERFORM FIND-ACCOUNT
           MOVE WS-SEARCH-INDEX TO WS-DEST-INDEX

           IF WS-DEST-INDEX = 0
               DISPLAY "Destination card not found." LINE 21 COL 27
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           IF WS-DEST-INDEX = WS-CURRENT-INDEX
               DISPLAY "Enter another user's card." LINE 21 COL 27
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Recipient: " DELIMITED BY SIZE
               FUNCTION TRIM(ACCT-NAME(WS-DEST-INDEX))
                   DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           MOVE 17 TO WS-ROW
           PERFORM SET-COLOR-MUTED
           PERFORM PUT-CENTERED

           DISPLAY "Destination account" LINE 18 COL 29
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           MOVE 19 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID NOT = "Y"
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF
           MOVE WS-ACCOUNT-TYPE TO WS-DEST-TYPE

           MOVE 20 TO WS-PROMPT-ROW
           PERFORM GET-AMOUNT

           *> Send vulnerability fix
           *> Discard intermediate variable WS-TRANSFER-DOLLARS that had 
           *> lower precision and caused the actual transfer to be smaller

           *> MOVE WS-AMOUNT-DOLLARS TO WS-TRANSFER-DOLLARS

           IF WS-SOURCE-TYPE = "C"
               MOVE ACCT-CHECKING(WS-SOURCE-INDEX) TO WS-BALANCE-DOLLARS
           ELSE
               MOVE ACCT-SAVINGS(WS-SOURCE-INDEX) TO WS-BALANCE-DOLLARS
           END-IF

           IF WS-AMOUNT-DOLLARS > WS-BALANCE-DOLLARS
               DISPLAY "Insufficient funds." LINE 21 COL 31
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           IF WS-SOURCE-TYPE = "C"
               SUBTRACT WS-AMOUNT-DOLLARS FROM
                   ACCT-CHECKING(WS-SOURCE-INDEX)
           ELSE
               SUBTRACT WS-AMOUNT-DOLLARS FROM
                   ACCT-SAVINGS(WS-SOURCE-INDEX)
           END-IF

           IF WS-DEST-TYPE = "C"
               ADD WS-AMOUNT-DOLLARS TO ACCT-CHECKING(WS-DEST-INDEX)
           ELSE
               ADD WS-AMOUNT-DOLLARS TO ACCT-SAVINGS(WS-DEST-INDEX)
           END-IF

           PERFORM DRAW-ACCOUNT-SCREEN

           MOVE WS-AMOUNT-DOLLARS TO WS-BALANCE-DOLLARS
           PERFORM FORMAT-MONEY
           
           DISPLAY "Send money complete." LINE 10 COL 30
               FOREGROUND-COLOR COLOR-GREEN
               BACKGROUND-COLOR COLOR-BLACK
           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "$" DELIMITED BY SIZE
               FUNCTION TRIM(WS-MONEY-OUT) DELIMITED BY SIZE
               " sent to " DELIMITED BY SIZE
               FUNCTION TRIM(ACCT-NAME(WS-DEST-INDEX))
                   DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           MOVE 12 TO WS-ROW
           PERFORM SET-COLOR-NORMAL
           PERFORM PUT-CENTERED
           PERFORM PAUSE-SCREEN.
       
       FIND-PAYEE.
           MOVE 0 TO WS-SEARCH-PAYEE-INDEX
           PERFORM VARYING WS-JDX FROM 1 BY 1
               UNTIL WS-JDX > WS-PAYEE-COUNT
                    OR WS-SEARCH-PAYEE-INDEX > 0
               IF FUNCTION TRIM(WS-PAYEE-IN) =
                    FUNCTION TRIM(PAYEE-ID(WS-JDX))
                    MOVE WS-JDX TO WS-SEARCH-PAYEE-INDEX
               END-IF
           END-PERFORM.

       PAY-BILL.
           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Pay a bill" LINE 8 COL 35
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK

           IF WS-PAYEE-COUNT = 0
               DISPLAY "No payees are available." LINE 11 COL 28
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           DISPLAY "Payee number:" LINE 11 COL 22
               FOREGROUND-COLOR COLOR-CYAN
               BACKGROUND-COLOR COLOR-BLACK
           DISPLAY "[            ]" LINE 11 COL 38
               FOREGROUND-COLOR COLOR-YELLOW
               BACKGROUND-COLOR COLOR-BLACK
           ACCEPT WS-PAYEE-IN LINE 11 COL 39

           *> Payment vulnerability fix
           *> Make sure the payee actually exists and is registered
           PERFORM FIND-PAYEE
           IF WS-SEARCH-PAYEE-INDEX = 0
               DISPLAY "Payee number not found." LINE 21 COL 29
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF
           MOVE WS-SEARCH-PAYEE-INDEX TO WS-PAYEE-INDEX

           MOVE SPACES TO WS-SCREEN-TEXT
           STRING "Payee: " DELIMITED BY SIZE
               FUNCTION TRIM(PAYEE-NAME(WS-PAYEE-INDEX))
                    DELIMITED BY SIZE
               INTO WS-SCREEN-TEXT
           END-STRING
           MOVE 13 TO WS-ROW
           PERFORM SET-COLOR-MUTED
           PERFORM PUT-CENTERED

           MOVE 15 TO WS-PROMPT-ROW
           PERFORM ASK-ACCOUNT-TYPE
           IF WS-ACCOUNT-VALID NOT = "Y"
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           MOVE 17 TO WS-PROMPT-ROW
           PERFORM GET-AMOUNT

           PERFORM LOAD-SOURCE-BALANCE
           IF WS-AMOUNT-DOLLARS > WS-BALANCE-DOLLARS
               DISPLAY "Insufficient funds." LINE 21 COL 31
                   FOREGROUND-COLOR COLOR-RED
                   BACKGROUND-COLOR COLOR-BLACK
               PERFORM PAUSE-SCREEN
               EXIT PARAGRAPH
           END-IF

           IF WS-ACCOUNT-TYPE = "C"
               SUBTRACT WS-AMOUNT-DOLLARS FROM
                    ACCT-CHECKING(WS-CURRENT-INDEX)
           ELSE
               SUBTRACT WS-AMOUNT-DOLLARS FROM
                    ACCT-SAVINGS(WS-CURRENT-INDEX)
           END-IF

           PERFORM DRAW-ACCOUNT-SCREEN
           DISPLAY "Bill payment complete." LINE 10 COL 29
               FOREGROUND-COLOR COLOR-GREEN
               BACKGROUND-COLOR COLOR-BLACK
           PERFORM PAUSE-SCREEN.
       
       FORMAT-MONEY.
           MOVE WS-BALANCE-DOLLARS TO WS-MONEY-OUT.
