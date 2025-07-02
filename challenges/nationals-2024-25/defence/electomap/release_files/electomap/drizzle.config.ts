import { defineConfig } from 'drizzle-kit';
import * as dotenv from 'dotenv';
dotenv.config();

const db_url = process.env.POSTGRES_URL;
if (!db_url) {
	throw Error('POSTGRES_URL not provided!');
}

export default defineConfig({
	schema: './src/lib/server/schema.ts',
	dialect: 'postgresql',
	dbCredentials: {
		url: db_url
	}
});
