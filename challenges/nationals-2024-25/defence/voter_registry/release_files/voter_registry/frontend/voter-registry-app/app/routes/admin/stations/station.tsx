import { API_BASE_URL } from "config";
import type { Route } from "./+types/station";
import type { Station } from "~/types/api";
import { Form, NavLink } from "react-router";
import { TrashIcon } from "@heroicons/react/24/solid";
import { getAccessToken } from "~/oidc";

export async function clientLoader({
    params,
}: Route.ClientLoaderArgs) {
    const res = await fetch(`${API_BASE_URL}/PollingStation/${params.station}`);
    const station = await res.json();
    return station;
}

async function addAdvisoryAction(formData: FormData) {
    const stationId = formData.get("station");
    const message = formData.get("message");
    const url = formData.get("url");

    const res = await fetch(`${API_BASE_URL}/PollingStation/${stationId}/advisory`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
            message,
            url
        })
    });

    if (!res.ok) {
        throw new Error("Failed to add advisory");
    }
}

async function deleteAdvisoryAction(formData: FormData) {
    const stationId = formData.get("station");
    const advisoryId = formData.get("advisory");

    const res = await fetch(`${API_BASE_URL}/PollingStation/${stationId}/advisory/${advisoryId}`, {
        method: "DELETE",
        headers: {
            "Authorization": `Bearer ${getAccessToken()}`,
        }
    });

    if (!res.ok) {
        throw new Error("Failed to delete advisory");
    }
}

export async function clientAction({
    request,
}: Route.ClientActionArgs) {
    let formData = await request.formData();

    const intent = formData.get("intent");

    switch (intent) {
        case "add-advisory":
            return addAdvisoryAction(formData);
        case "delete-advisory":
            return deleteAdvisoryAction(formData);
    }
}

export default function Station({
    loaderData,
}: Route.ComponentProps) {
    const station = loaderData as Station;

    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-4 text-gray-800 text-center">
                <NavLink
                    to={'/admin'}
                    className="text-blue-800 hover:underline"
                >
                    Admin Dashboard
                </NavLink> &rarr; View Station
            </h2>

            <hr className="mb-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Station Address
            </h3>
            <div className="grid grid-cols-4 gap-2 text-gray-800">
                <div className="font-semibold">Address:</div>
                <div className="col-span-3">{station.street_number} {station.street_name}</div>

                <div className="font-semibold">City:</div>
                <div className="col-span-3">{station.city}</div>

                <div className="font-semibold">State:</div>
                <div className="col-span-3">{station.state}</div>

                <div className="font-semibold">Postal Code:</div>
                <div className="col-span-3">{station.postal_code}</div>
            </div>

            <hr className="my-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Assigned Streets
            </h3>
            <ul className="list-disc pl-6 text-gray-800">
                {station.streets?.map((street, index) => (
                    <li key={index} className="mb-1">
                        {street.street_name}, {street.city}, {street.state} {street.postal_code}
                    </li>
                ))}
            </ul>

            <hr className="my-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Advisories
            </h3>
            <div className="mb-4">
                {station.advisories && station.advisories.length > 0 ? (
                    <>
                        {station.advisories.map((advisory, index) => (
                            <div key={advisory.id} className="flex flex-row mb-1">
                                <Form className="mt-0.5" method="post">
                                    <input type="hidden" name="station" value={station.id} />
                                    <input type="hidden" name="advisory" value={advisory.id} />
                                    <button
                                        type="submit"
                                        className="h-6 w-6 p-1 rounded bg-red-300 hover:bg-red-400"
                                        name="intent"
                                        value="delete-advisory"
                                    >
                                        <TrashIcon />
                                    </button>
                                </Form>
                                <div className="ml-2">
                                    <p>
                                        <span className="font-semibold">URL: </span>
                                        <a href={advisory.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                            {advisory.url}
                                        </a>
                                    </p>
                                    <p>
                                        <span className="font-semibold">Created: </span>
                                        {new Date(advisory.created_at).toLocaleString()}
                                    </p>
                                    <p>
                                        <span className="font-semibold">Message: </span>
                                        {advisory.message}
                                    </p>

                                </div>
                            </div>
                        ))}
                    </>
                ) : (
                    <span className="text-gray-500">No advisories.</span>
                )}
            </div>

            <hr className="my-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Add New Advisory
            </h3>
            <Form method="post" className="space-y-4">
                <input type="hidden" name="station" value={station.id} />
                <div>
                    <label className="block font-semibold mb-1" htmlFor="message">
                        Message
                    </label>
                    <textarea
                        id="message"
                        name="message"
                        required
                        className="w-full p-2 border rounded"
                    />
                </div>
                <div>
                    <label className="block font-semibold mb-1" htmlFor="url">
                        URL
                    </label>
                    <input
                        id="url"
                        name="url"
                        type="text"
                        className="w-full p-2 border rounded"
                    />
                </div>
                <button
                    type="submit"
                    className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition"
                    name="intent"
                    value="add-advisory"
                >
                    Add Advisory
                </button>
            </Form>
        </div>
    );
}