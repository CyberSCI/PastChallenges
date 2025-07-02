CREATE TABLE "district_vote" (
  "partyId" text NOT NULL,
  "districtId" text NOT NULL,
  "citizenId" text NOT NULL,
  "voteId" text
);

--> statement-breakpoint
CREATE TABLE "district" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text,
  CONSTRAINT "district_name_unique" UNIQUE ("name")
);

--> statement-breakpoint
CREATE TABLE "party" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text NOT NULL,
  "leader" text NOT NULL,
  CONSTRAINT "party_name_unique" UNIQUE ("name")
);

--> statement-breakpoint
CREATE TABLE "session" (
  "id" text PRIMARY KEY NOT NULL,
  "userId" text NOT NULL,
  "expires_at" timestamp
  with
    time zone NOT NULL
);

--> statement-breakpoint
CREATE TABLE "account" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text NOT NULL,
  "email" text NOT NULL,
  "nationalId" text NOT NULL,
  "passwordHash" text NOT NULL,
  "voteKey" text,
  "emailVerified" timestamp,
  "image" text,
  CONSTRAINT "account_email_unique" UNIQUE ("email")
);

--> statement-breakpoint
ALTER TABLE "district_vote" ADD CONSTRAINT "district_vote_partyId_party_id_fk" FOREIGN KEY ("partyId") REFERENCES "public"."party" ("id") ON DELETE no action ON UPDATE no action;

--> statement-breakpoint
ALTER TABLE "district_vote" ADD CONSTRAINT "district_vote_districtId_district_id_fk" FOREIGN KEY ("districtId") REFERENCES "public"."district" ("id") ON DELETE no action ON UPDATE no action;

--> statement-breakpoint
ALTER TABLE "district_vote" ADD CONSTRAINT "district_vote_citizenId_account_id_fk" FOREIGN KEY ("citizenId") REFERENCES "public"."account" ("id") ON DELETE no action ON UPDATE no action;

--> statement-breakpoint
ALTER TABLE "session" ADD CONSTRAINT "session_userId_account_id_fk" FOREIGN KEY ("userId") REFERENCES "public"."account" ("id") ON DELETE no action ON UPDATE no action;
