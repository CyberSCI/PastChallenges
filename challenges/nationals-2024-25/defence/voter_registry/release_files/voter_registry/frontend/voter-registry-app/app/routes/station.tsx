import { API_BASE_URL } from "config";
import type { Route } from "./+types/station";
import type { Station } from "~/types/api";

export async function clientLoader({
    params,
}: Route.ClientLoaderArgs) {
    const res = await fetch(`${API_BASE_URL}/PollingStation/${params.station}`);
    const station = await res.json();
    return station;
}

export default function Station({
    loaderData,
}: Route.ComponentProps) {
    const station = loaderData as Station;

    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-4 text-green-700">
                This is your assigned polling station!
            </h2>

            <p className="text-underline mb-4">
                Make sure to bring your photo ID. If you registered online, make sure to bring your registration number.
            </p>

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

            {station.advisories && station.advisories.length > 0 && (
                <div>
                    <h3 className="text-xl font-bold mt-6 mb-2">IMPORTANT ADVISORY</h3>
                    <ul className="list-none font-semibold">
                        {station.advisories.map((advisory) => (
                            <li key={advisory.id} className="mb-2">
                                { advisory.url && (
                                    <a href={advisory.url} className="text-blue-600 hover:underline">
                                        {advisory.message}
                                    </a>
                                )}
                                {!advisory.url && (
                                    <span className="text-gray-800">{advisory.message}</span>
                                )}
                                <span className="text-gray-600"> (advisory issued at {new Date(advisory.created_at).toLocaleDateString()})</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}