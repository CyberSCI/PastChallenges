import * as schema from '$lib/server/schema';
import { env } from '$env/dynamic/private';
import { drizzle } from 'drizzle-orm/node-postgres';
import { seed, reset } from 'drizzle-seed';
import { Pool } from 'pg';
import { hash } from '@node-rs/argon2';

import states from '$lib/server/data/states.json';
import parties from '$lib/server/data/parties.json';

if (!env.POSTGRES_URL) {
	throw Error('POSTGRES_URL not provided!');
}

const pool = new Pool({
	connectionString: env.POSTGRES_URL
});
export const db = drizzle({ client: pool, schema });

export async function seedDatabase() {
	const passwordHash = await hash('Password1!');
	await reset(db, schema);
	console.log('Reset database.');

	await db.transaction(async (tx) => {
		const stateInsertions = states.map(({ state }) => {
			const stateInsertion = tx
				.insert(schema.states)
				.values({ name: state })
				.returning({ id: schema.states.id });
			return stateInsertion;
		});

		console.log('Created state insertions.');

		const stateResults = await Promise.all(stateInsertions);

		const districtInsertions = stateResults.flatMap((result, index) => {
			const stateId = result[0].id;
			const state = states.at(index);
			if (state === undefined) {
				throw 'STATE UNDEFINED.';
			}

			const stateDistrictInsertions = state?.districts.map((district) => {
				return tx.insert(schema.districts).values({
					name: district.name,
					state: stateId
				});
			});

			return stateDistrictInsertions;
		});

		await Promise.all(districtInsertions);

		const partyInsertions = parties.map(({ name, short_name, leader }) => {
			return tx.insert(schema.parties).values({
				name,
				short_name,
				leader
			});
		});

		await Promise.all(partyInsertions);
	});

	await seed(db, {
		users: schema.users
	}).refine((funcs) => ({
		users: {
			count: 1,
			columns: {
				name: funcs.fullName(),
				email: funcs.default({ defaultValue: 'test@test.com' }),
				nationalId: funcs.default({ defaultValue: '123456789' }),
				passwordHash: funcs.default({ defaultValue: passwordHash })
			}
		}
	}));

	console.log('Database initialized.');
}
