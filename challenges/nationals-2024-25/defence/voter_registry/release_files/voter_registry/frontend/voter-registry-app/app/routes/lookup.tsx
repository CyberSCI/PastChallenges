import { API_BASE_URL } from "config";
import { Form, redirect } from "react-router";
import type { Route } from "./+types";

export async function clientAction({
    request
}: Route.ClientActionArgs) {
    let formData = await request.formData();

    let streetNumber = formData.get("streetNumber") as string;
    let streetName = formData.get("streetName") as string;
    let city = formData.get("city") as string;
    let state = formData.get("state") as string;
    let postalCode = formData.get("postalCode") as string;

    const res = await fetch(`${API_BASE_URL}/PollingStation/lookup`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            streetNumber,
            streetName,
            city,
            state,
            postalCode
        })
    });

    const station = await res.json();

    if (station?.id) {
        return redirect(`/stations/${station.id}`);
    }

    return station;
}

export default function Lookup({
    actionData,
}: Route.ComponentProps) {
    let data = actionData as unknown as {
        error: string | null | undefined;
    } | null;

    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl text-center font-bold mb-4">Find Your Polling Station</h2>
            <p className="mb-4">
                Enter your address below to find out where you can vote. Make sure to provide accurate information to get the correct polling station.
            </p>
            {data?.error && (
                <p className="mb-4 text-red-600 font-semibold">{data.error}</p>
            )}
            <Form method="post" className="space-y-4 grid grid-cols-4 gap-2">
                <div className="col-span-1">
                    <label className="block font-semibold mb-1" htmlFor="streetNumber">
                        Street Number
                    </label>
                    <input
                        id="streetNumber"
                        name="streetNumber"
                        type="text"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <div className="col-span-3">
                    <label className="block font-semibold mb-1" htmlFor="streetName">
                        Street Name
                    </label>
                    <input
                        id="streetName"
                        name="streetName"
                        type="text"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <div className="col-span-2">
                    <label className="block font-semibold mb-1" htmlFor="city">
                        City
                    </label>
                    <input
                        id="city"
                        name="city"
                        type="text"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <div className="col-span-1">
                    <label className="block font-semibold mb-1" htmlFor="state">
                        State
                    </label>
                    <input
                        id="state"
                        name="state"
                        type="text"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <div className="col-span-1">
                    <label className="block font-semibold mb-1" htmlFor="postalCode">
                        Postal Code
                    </label>
                    <input
                        id="postalCode"
                        name="postalCode"
                        type="text"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <button
                    type="submit"
                    className="col-span-4 bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition"
                >
                    Find Polling Station
                </button>
            </Form>
        </div>
    );
}