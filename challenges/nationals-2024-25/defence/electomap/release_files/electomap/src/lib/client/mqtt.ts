import mqtt, { type MqttClient } from 'mqtt';
import { env } from '$env/dynamic/public';

export async function connectMqtt(): Promise<MqttClient> {
	const MQTT_URL = env.PUBLIC_MQTT_URL;
	if (!MQTT_URL) {
		throw new Error('MQTT_URL environment variable not provided!');
	}

	const mqttClient = await mqtt.connectAsync(MQTT_URL);

	return mqttClient;
}
