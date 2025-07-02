CREATE TABLE "state" (
  "id" text PRIMARY KEY NOT NULL,
  "name" text,
  CONSTRAINT "state_name_unique" UNIQUE ("name")
);

--> statement-breakpoint
ALTER TABLE "district"
ADD COLUMN "stateId" text NOT NULL;

--> statement-breakpoint
ALTER TABLE "district" ADD CONSTRAINT "district_stateId_state_id_fk" FOREIGN KEY ("stateId") REFERENCES "public"."state" ("id") ON DELETE no action ON UPDATE no action;

