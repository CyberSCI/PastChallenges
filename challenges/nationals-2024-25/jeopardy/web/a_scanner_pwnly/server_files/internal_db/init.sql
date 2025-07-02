CREATE TABLE "employees" (
    "id" SERIAL PRIMARY KEY,
    "first_name" VARCHAR(150),
    "last_name" VARCHAR(150),
    "title" VARCHAR(150),
    "salary" VARCHAR(50),
    "national_id" CHAR(9),
    "joined" DATE
);


CREATE TABLE "transactions" (
    "id" SERIAL PRIMARY KEY,
    "sender" VARCHAR(150),
    "receiver" VARCHAR(150),
    "amount" BIGINT,
    "conducted_on" DATE,
    "notes" TEXT
);


CREATE TABLE "memos" (
    "id" SERIAL PRIMARY KEY,
    "author" VARCHAR(150),
    "text" TEXT
);


COPY employees
FROM
    '/docker-entrypoint-initdb.d/employees.csv' CSV HEADER;


COPY transactions
FROM
    '/docker-entrypoint-initdb.d/transactions.csv' CSV HEADER;


COPY memos
FROM
    '/docker-entrypoint-initdb.d/memos.csv' CSV HEADER;
