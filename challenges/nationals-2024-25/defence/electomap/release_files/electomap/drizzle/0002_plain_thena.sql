ALTER TABLE "party" ADD COLUMN "short_name" text DEFAULT 'N/A' NOT NULL;--> statement-breakpoint
ALTER TABLE "party" ADD CONSTRAINT "party_short_name_unique" UNIQUE("short_name");