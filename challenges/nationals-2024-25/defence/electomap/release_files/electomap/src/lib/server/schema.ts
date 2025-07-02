import { boolean, timestamp, pgTable, text, primaryKey, integer } from 'drizzle-orm/pg-core';

import type { InferSelectModel } from 'drizzle-orm';
export const users = pgTable('account', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	name: text('name').notNull(),
	email: text('email').unique().notNull(),
	nationalId: text('nationalId').notNull(),
	passwordHash: text('passwordHash').notNull(),
	voteKey: text('voteKey'),
	emailVerified: timestamp('emailVerified', { mode: 'date' }),
	image: text('image')
});

export const sessions = pgTable('session', {
	id: text('id').primaryKey(),
	userId: text('userId')
		.notNull()
		.references(() => users.id),
	expiresAt: timestamp('expires_at', {
		withTimezone: true,
		mode: 'date'
	}).notNull()
});

export const parties = pgTable('party', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	name: text('name').unique().notNull(),
	short_name: text('short_name').unique().notNull().default('N/A'),
	leader: text('leader').notNull()
});

export const states = pgTable('state', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	name: text('name').unique()
});

export const districts = pgTable('district', {
	id: text('id')
		.primaryKey()
		.$defaultFn(() => crypto.randomUUID()),
	name: text('name').unique(),
	state: text('stateId')
		.notNull()
		.references(() => states.id)
});

export const districtVotes = pgTable('district_vote', {
	partyId: text('partyId')
		.notNull()
		.references(() => parties.id),
	districtId: text('districtId')
		.notNull()
		.references(() => districts.id),
	citizenId: text('citizenId')
		.notNull()
		.references(() => users.id),
	voteId: text('voteId')
});

export type User = InferSelectModel<typeof users>;
export type Session = InferSelectModel<typeof sessions>;
export type Party = InferSelectModel<typeof parties>;
export type District = InferSelectModel<typeof districts>;
