import mqtt, { type MqttClient } from 'mqtt';
import { env } from '$env/dynamic/private';
import type { VoteCountUpdate, VotePackage } from '$lib/types';
import { db } from '$lib/server/database';
import {
	districts,
	parties,
	users,
	type Party,
	type District,
	type User,
	districtVotes
} from '$lib/server/schema';
import { eq } from 'drizzle-orm';
import * as jose from 'jose';

async function processVote(message: string, mqttClient: MqttClient) {
	const votePackage: VotePackage = JSON.parse(message);

	const voteKey = votePackage.voteKey;
	const partyId = votePackage.party;
	const districtId = votePackage.district;

	if (!(voteKey && partyId && districtId)) {
		console.error('Failed to process message: ', message);
		return null;
	}

	const { sub } = jose.decodeJwt(voteKey);

	const partyQuery = db.query.parties.findFirst({ where: eq(parties.id, partyId) });
	const districtQuery = db.query.districts.findFirst({ where: eq(districts.id, districtId) });
	const userQuery = db.query.users.findFirst({ where: eq(users.nationalId, sub ?? '') });

	const [partyResult, districtResult, userResult] = await Promise.all([
		partyQuery,
		districtQuery,
		userQuery
	]);

	if (!(partyResult && districtResult && userResult)) {
		console.error('Could not find party, district or user from message: ', message);
		return null;
	}

	const voteCountUpdate: VoteCountUpdate = { partyId, districtId };

	await mqttClient.publishAsync('vote-counts', JSON.stringify(voteCountUpdate));

	await saveVote(partyResult, districtResult, userResult);
}

async function saveVote(party: Party, district: District, user: User) {
	await db
		.insert(districtVotes)
		.values({ partyId: party.id, districtId: district.id, citizenId: user.id });
}

export async function connectMqtt() {
	const MQTT_URL = env.MQTT_URL;
	if (!MQTT_URL) {
		throw new Error('MQTT_URL environment variable not provided!');
	}
	const mqttClient = await mqtt.connectAsync(MQTT_URL);

	mqttClient.on('error', async (err) => {
		console.error('MQTT Error: ' + err.message);
	});

	console.log('MQTT connection established.');

	await mqttClient.subscribeAsync('votes');

	mqttClient.on('message', async (topic, message) => {
		switch (topic) {
			case 'votes':
				await processVote(message.toString(), mqttClient);
				break;
			default:
				console.log('Unknown topic: ', topic);
		}
	});

	return mqttClient;
}
