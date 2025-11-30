' CyberSci Regionals 2025/26
'
' Dmitriy Beryoza (0xd13a@gmail.com)
'
' Inventory challenge

LET REGULAR_INV_FILE$ = "regular_inventory.csv"
LET RESTRICTED_INV_FILE$ = "restricted_inventory.csv"

DIM REGULAR_INV_NAMES$(1)
DIM REGULAR_INV_PRICES(1)
DIM REGULAR_INV_AMOUNTS(1)
DIM RESTRICTED_INV_NAMES$(1)
DIM RESTRICTED_INV_PRICES(1)
DIM RESTRICTED_INV_AMOUNTS(1)

' Load inventory information from a single file
SUB LOAD_FILE(FILE_NAME$, NAMES$(), PRICES(), AMOUNTS())
    OPEN FILE_NAME$ FOR READING AS #1
    LET ROW = 0
    WHILE NOT EOF(1)
        LINE INPUT #1 L$
        ROW = ROW + 1
        DIM NAMES$(ROW)
        DIM PRICES(ROW)
        DIM AMOUNTS(ROW)
        N = 1
        WHILE LEN(L$) > 0
            COMMA = INSTR(L$, ",")
            IF COMMA = 0 THEN
                FIELD$ = L$
                L$ = ""
            ELSE
                FIELD$ = LEFT$(L$, COMMA - 1)
                L$ = MID$(L$, COMMA + 1)
            END IF
            IF N = 2 THEN
                NAMES$(ROW-1) = FIELD$
            END IF
            IF N = 3 THEN
                PRICES(ROW-1) = VAL(FIELD$)
            END IF
            IF N = 4 THEN
                AMOUNTS(ROW-1) = VAL(FIELD$)
            END IF
            N = N + 1
        WEND
    WEND
    CLOSE #1
END SUB

' Load inventories
LOAD_FILE(RESTRICTED_INV_FILE$, RESTRICTED_INV_NAMES$(), RESTRICTED_INV_PRICES(), RESTRICTED_INV_AMOUNTS())
LOAD_FILE(REGULAR_INV_FILE$, REGULAR_INV_NAMES$(), REGULAR_INV_PRICES(), REGULAR_INV_AMOUNTS())

LET MODE = 1

' Pad string with characters
SUB RPAD$(ORIG_STR$, NUM, CHAR$)
    LET RET$ = ORIG_STR$
    WHILE LEN(RET$) < NUM
        RET$ = RET$ + CHAR$
    END WHILE
    RETURN RET$
END SUB

LET ADMIN_PASS$ = "UgmD6PotMAaZ55TGqyVS"

' Process login
SUB LOGIN()
    PRINT " _                        _                   __ __             _             "
    PRINT "| |._ _  _ _  ___ ._ _  _| |_  ___  _ _  _ _ |  \  \ ___  ___ _| |_  ___  _ _ "
    PRINT "| || ' || | |/ ._>| ' |  | |  / . \| '_>| | ||     |<_> |<_-<  | |  / ._>| '_>"
    PRINT "|_||_|_||__/ \___.|_|_|  |_|  \___/|_|  `_. ||_|_|_|<___|/__/  |_|  \___.|_|  "
    PRINT "                                        <___'                                 "
    PRINT ""
    PRINT "               *** Welcome to Emergency Supplies Inventory ***"
    PRINT ""
    LINE INPUT "Enter your username: " USERNAME$
    LET MODE = 1
    IF USERNAME$ = "admin" THEN
        LINE INPUT "Administrator, enter your password: " PASS$
        IF PASS$ <> ADMIN_PASS$ THEN
            RETURN false
        END IF 
        MODE = 0
    END IF

    PRINT ""
    PRINT "Welcome ", USERNAME$, "!"
    PRINT ""

    LET PROMPT$ = EVAL$("\""+USERNAME$+"> \"")
    RETURN true
END SUB

DIM PURCHASE_NAMES$(1)
DIM PURCHASE_PRICES(1)

' Print purchase receipt
SUB PRINT_RECEIPT()

    LET TOTAL_SUM = 0
    PRINT ""
    PRINT "Give this receipt to the cashier to receive your item(s) and pay:"
    PRINT ""
    PRINT "+-Item-------------------------------------+-Price-----+"
    FOR PURCH_ITEM = 0 TO (ARRAYSIZE(PURCHASE_NAMES$(), 1) - 1)
        PRINT "| ";
        PRINT RPAD$(PURCHASE_NAMES$(PURCH_ITEM), 40, " ");
        PRINT " | $";
        PRINT PURCHASE_PRICES(PURCH_ITEM) USING "#####.##";
        PRINT " |"
        TOTAL_SUM = TOTAL_SUM + PURCHASE_PRICES(PURCH_ITEM)
    NEXT PURCH_ITEM
    PRINT "+------------------------------------------+-$";
    PRINT TOTAL_SUM USING "#####.##";
    PRINT "-+"
    PRINT ""

END SUB

' Process inventory item selection
SUB PROCESS_ITEM(ID$)
    LET ERROR_MSG$ = "*** Incorrect item ID!"

    LET ITEM$ = TRIM$(ID$)
    IF LEN(ITEM$) < 1 THEN
        PRINT ERROR_MSG$
        RETURN
    END IF

    LET ADMIN = false
    IF UPPER$(MID$(ITEM$,1,1)) = "R" THEN
        ADMIN = true
        ITEM$ = MID$(ITEM$,2)
    END IF

    ITEM_NO = VAL(ITEM$) - 1

    IF ADMIN = true THEN
        IF ITEM_NO < 0 OR ITEM_NO >= ARRAYSIZE(RESTRICTED_INV_NAMES$(), 1) THEN
            PRINT ERROR_MSG$
            RETURN
        END IF

        ARR_SIZE = ARRAYSIZE(PURCHASE_NAMES$(), 1)
        IF PURCHASE_NAMES$(0) <> "" THEN
            ARR_SIZE = ARR_SIZE + 1
        END IF
        DIM PURCHASE_NAMES$(ARR_SIZE)
        DIM PURCHASE_PRICES(ARR_SIZE)
        PURCHASE_NAMES$(ARR_SIZE - 1) = RESTRICTED_INV_NAMES$(ITEM_NO)
        PURCHASE_PRICES(ARR_SIZE - 1) = RESTRICTED_INV_PRICES(ITEM_NO)
        RESTRICTED_INV_AMOUNTS(ITEM_NO) = RESTRICTED_INV_AMOUNTS(ITEM_NO) - 1
    ELSE
        IF ITEM_NO < 0 OR ITEM_NO >= ARRAYSIZE(REGULAR_INV_NAMES$(), 1) THEN
            PRINT ERROR_MSG$
            RETURN
        END IF

        ARR_SIZE = ARRAYSIZE(PURCHASE_NAMES$(), 1)
        IF PURCHASE_NAMES$(0) <> "" THEN
            ARR_SIZE = ARR_SIZE + 1
        END IF
        DIM PURCHASE_NAMES$(ARR_SIZE)
        DIM PURCHASE_PRICES(ARR_SIZE)
        PURCHASE_NAMES$(ARR_SIZE - 1) = REGULAR_INV_NAMES$(ITEM_NO)
        PURCHASE_PRICES(ARR_SIZE - 1) = REGULAR_INV_PRICES(ITEM_NO)
        REGULAR_INV_AMOUNTS(ITEM_NO) = REGULAR_INV_AMOUNTS(ITEM_NO) - 1
    END IF

    PRINT_RECEIPT()
END SUB

LET SCREEN_ROWS = 10

' Process browsing of the inventory
SUB PROCESS_INVENTORY(NAMES$(), PRICES(), AMOUNTS(), PREFIX$)

    LET MOVE = false
    LET START = 0

    WHILE true
        IF MOVE = true THEN
            MOVE = false
            IF MODE = 0 THEN
                IF START - SCREEN_ROWS >= 0 THEN
                    START = START - SCREEN_ROWS
                END IF
            ELSE
                IF START + SCREEN_ROWS < ARRAYSIZE(NAMES$(),1) THEN
                    START = START + SCREEN_ROWS
                END IF
            END IF
        END IF
        
        PRINT ""
        PRINT "+-ID--+-Name-------------------------------------+-Price----+-Inventory-+"
        FOR R = 0 TO SCREEN_ROWS-1
            LET IDX = START + R
            IF IDX >= ARRAYSIZE(NAMES$(),1) THEN
                BREAK
            END IF

            PRINT "| ", PREFIX$;
            LET RENDERED_ID$ = STR$(IDX + 1)
            PRINT RPAD$(RENDERED_ID$, 2, " ");
            PRINT " | ", RPAD$(NAMES$(IDX), 40, " ");
            PRINT " | $";
            PRINT PRICES(IDX) USING "####.##";
            PRINT " | ", AMOUNTS(IDX) USING "#########", " |"
        NEXT R
        PRINT "+-----+------------------------------------------+ ---------+-----------+"

        PRINT ""
        PRINT "Enter item number, N for next page, P for previous, X to exit"
        PRINT PROMPT$ ;
        INPUT "" COMMAND$

        IF UPPER$(COMMAND$) = "X" THEN
            RETURN
        ELSEIF UPPER$(COMMAND$) = "N" THEN
            LET MOVE = true
            LET MODE = 1
        ELSEIF UPPER$(COMMAND$) = "P" THEN
            LET MOVE = true
            LET MODE = 0
        ELSE
            PROCESS_ITEM(COMMAND$)
        END IF
    END WHILE
END SUB

' Process main menu
SUB MAIN_MENU()

    WHILE true

        PRINT "Please select an operation:"
        PRINT ""
        PRINT "I - Browse Emergency Supplies Inventory"
        PRINT "R - Browse Dangerous Goods Inventory (RESTRICTED)"
        PRINT "X - Exit"
        PRINT ""
        PRINT PROMPT$ ;
        INPUT "" COMMAND$

        IF UPPER$(COMMAND$) = "X" THEN
            RETURN
        END IF

        IF UPPER$(COMMAND$) = "I" THEN
            PROCESS_INVENTORY(REGULAR_INV_NAMES$(), REGULAR_INV_PRICES(), REGULAR_INV_AMOUNTS(), " ")
        END IF

        IF UPPER$(COMMAND$) = "R" THEN
            IF MODE <> 0 THEN
                PRINT ""
                PRINT "*** Restricted area, you need to be an admin to enter!"
                PRINT ""
            ELSE
                PROCESS_INVENTORY(RESTRICTED_INV_NAMES$(), RESTRICTED_INV_PRICES(), RESTRICTED_INV_AMOUNTS(), "R")
            END IF

        END IF

    END WHILE

END SUB

' Main routine
SUB MAIN()
    LET RESULT = LOGIN()
    IF RESULT = false THEN
        PRINT "*** Invalid login!"
        RETURN
    END IF

    MAIN_MENU()

    PRINT ""
    PRINT "Goodbye."

END SUB

MAIN()