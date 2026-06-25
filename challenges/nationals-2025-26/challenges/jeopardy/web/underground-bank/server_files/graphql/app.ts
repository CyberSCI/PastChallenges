import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { randomBytes } from 'node:crypto';

type MoneyRequest = {
	id: string,
	requested_by: string,
	requested_from: string,
	amount: number,
	fee: number
}

type User = {
	username: string,
	password: string,
	balance: number,
	webhook: string
}

type Context = {
	user?: string
}

let users: Map<string, User> = new Map();
let requests: MoneyRequest[] = [];

try {
	users = new Map(JSON.parse(new TextDecoder().decode(Deno.readFileSync('users.json'))));
} catch {}

try {
	requests = JSON.parse(new TextDecoder().decode(Deno.readFileSync('requests.json')));
} catch {}

if (users.size === 0) {
	users.set('admin', {
		username: 'admin',
		password: randomBytes(32).toString('hex'),
		balance: 0,
		webhook: ''
	});
}

const typeDefs = `#graphql
	type MoneyRequest {
		id: String
		requested_by: String
		requested_from: String
		amount: Float
		fee: Float
	}

	type Query {
		requests: [MoneyRequest]
		login(username: String!, password: String!): Boolean
	}

	type Mutation {
		register(username: String!, password: String!): Boolean
		setWebhook(webhook: String!): Boolean
		requestMoney(from: String!, amount: Float!): MoneyRequest!
		sendMoney(to: String!, amount: Float!): Boolean!
		acceptRequest(id: String!): Boolean!
		flag: String
	}
`;

const save = () => {
	Deno.writeFileSync('users.json', new TextEncoder().encode(JSON.stringify(Array.from(users.entries()))));
	Deno.writeFileSync('requests.json', new TextEncoder().encode(JSON.stringify(requests)));
};

const triggerWebhook = async (webhook: string, request: MoneyRequest) => {
	await fetch(webhook, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(request)
	});
};

const server = new ApolloServer<Context>({
	typeDefs,
	resolvers: {
		Query: {
			requests: (_, __, ctx) => {
				if (!ctx.user) throw new Error('Not authenticated');
				return requests.filter(request => request.requested_from === ctx.user);
			},
			login: (_, { username, password }) => {
				if (!users.has(username) || users.get(username)?.password !== password) return false;
				return true;
			}
		},
		Mutation: {
			register: (_, { username, password }) => {
				if (users.has(username)) throw new Error('User already exists');
				users.set(username, { username, password, balance: 0, webhook: '' });
				
				save();
				
				return true;
			},
			setWebhook: (_, { webhook }, ctx) => {
				if (!ctx.user) throw new Error('Not authenticated');
				const me = users.get(ctx.user)!;
				const url = new URL(webhook);
				if (url.protocol !== 'https:') {
					throw new Error('Invalid protocol');
				}
				me.webhook = url.toString();
				save();
				return true;
			},
			requestMoney: (_, { from, amount }, ctx) => {
				if (!ctx.user) throw new Error('Not authenticated');
				if (amount <= 0) throw new Error('Invalid amount');
				const to = users.get(from);
				if (!to) throw new Error('User not found');

				const fee = Math.min(amount * 0.05, 100);

				requests.push({
					id: randomBytes(16).toString('hex'),
					requested_by: ctx.user,
					requested_from: from,
					amount: amount,
					fee
				});

				save();

				if (to.webhook) {
					triggerWebhook(to.webhook, requests[requests.length - 1]);
				}
				
				return requests[requests.length - 1];
			},
			acceptRequest: (_, { id }, ctx) => {
				if (!ctx.user) throw new Error('Not authenticated');

				const request = requests.find(r => r.id === id && r.requested_from === ctx.user);
				if (!request) return false;

				const requester = users.get(request.requested_by)!;
				const requestedFrom = users.get(request.requested_from)!;
				if (requestedFrom.balance < request.amount) return false;

				requestedFrom.balance -= request.amount;
				requestedFrom.balance -= request.fee;
				requester.balance += request.amount;
				users.get('admin')!.balance += request.fee;
				
				requests = requests.filter(r => r.id !== request.id);

				save();

				return true;
			},
			flag: (_, __, ctx) => {
				if (!ctx.user) throw new Error('Not authenticated');
				const me = users.get(ctx.user)!;
				if (me.balance > 1337) {
					return Deno.env.get('FLAG') || 'CyberSci{flag2}';
				}
				return "Not rich enough :(";
			},
		}
	}
});

await startStandaloneServer(server, {
	context: async ({ req }) => {
		const user = req.headers['x-request-user'];
		if (!user || typeof user !== 'string' || !users.has(user)) return {};
		return { user };
	}
});