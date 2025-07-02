import { API_BASE_URL } from "config";
import { useState } from "react";
import { Form } from "react-router";
import { NavLink } from "react-router";
import type { Route } from "./+types";

export async function clientAction({
    request
}: Route.ClientActionArgs) {
    let formData = await request.formData();

    const res = await fetch(`${API_BASE_URL}/Registration`, {
        method: "POST",
        headers: {
            "Accept": "application/json"
        },
        body: formData
    });

    const data = await res.json();

    return data;
}

export default function Register({
    actionData,
}: Route.ComponentProps) {
    let data = actionData as unknown as {
        registrationNumber: string | null | undefined;
        pollingStation: {
            id: string | null | undefined;
        } | null | undefined;
        error: string | null | undefined;
    } | null;

    const [fileName, setFileName] = useState<string | null>(null);

    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl text-center font-bold mb-4">
                Register to Vote
            </h2>

            {data?.registrationNumber && (
                <>
                    <p className="mb-4 text-center">
                        You are now registered to vote! Your registration number is: <strong>{data.registrationNumber}</strong>
                    </p>
                    <p className="mb-4 text-center">
                        Write down your registration number and bring it with you to your polling station.
                    </p>
                    <NavLink
                        to={`/stations/${data.pollingStation?.id}`}
                    >
                        <button className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition">
                            View Your Polling Station
                        </button>
                    </NavLink>
                </>
            )}

            {!data?.registrationNumber && (
                <>
                    <p className="mb-4">Please fill out the form below to register to vote.</p>

                    <Form method="post" encType="multipart/form-data" className="space-y-4 grid grid-cols-4 gap-2">
                        <h3 className="text-lg text-center font-semibold mb-2 col-span-4">
                            Personal Information
                        </h3>
                        <div className="col-span-2">
                            <label className="block font-semibold mb-1" htmlFor="firstName">
                                First Name
                            </label>
                            <input
                                id="firstName"
                                name="firstName"
                                type="text"
                                required
                                className="w-full p-2 border rounded"
                            />
                        </div>

                        <div className="col-span-2">
                            <label className="block font-semibold mb-1" htmlFor="lastName">
                                Last Name
                            </label>
                            <input
                                id="lastName"
                                name="lastName"
                                type="text"
                                required
                                className="w-full p-2 border rounded"
                            />
                        </div>

                        <div className="col-span-2">
                            <label className="block font-semibold mb-1" htmlFor="birthdate">
                                Birthdate
                            </label>
                            <input
                                id="birthdate"
                                name="birthdate"
                                type="date"
                                required
                                className="w-full p-2 border rounded"
                            />
                        </div>

                        <div className="col-span-2">
                            <label className="block font-semibold mb-1" htmlFor="photoIdNumber">
                                Photo ID Number
                            </label>
                            <input
                                id="photoIdNumber"
                                name="photoIdNumber"
                                type="text"
                                required
                                className="w-full p-2 border rounded"
                            />
                        </div>

                        <h3 className="text-lg text-center font-semibold mb-2 col-span-4">
                            Current Address
                        </h3>

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

                        <div className="col-span-4">
                            <label className="block font-semibold mb-1" htmlFor="addressProof">
                                Proof of Current Address
                                <span className="block text-sm text-gray-500">
                                    (Power Bill, Utilities Bill, Pay Stub, Lease, etc)
                                </span>
                            </label>
                            <input
                                id="addressProof"
                                name="addressProof"
                                type="file"
                                accept=".pdf,.jpg,.jpeg,.png"
                                required
                                onChange={(e) =>
                                    setFileName(e.target.files?.[0]?.name || null)
                                }
                                className="w-full p-2 border rounded bg-white"
                            />
                            {fileName && (
                                <p className="text-sm text-gray-600 mt-1">Selected: {fileName}</p>
                            )}
                        </div>

                        {data?.error && (
                            <p className="mb-4 text-red-600 font-semibold col-span-4">{data.error}</p>
                        )}

                        <button
                            type="submit"
                            className="bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition col-span-4"
                        >
                            Submit Registration
                        </button>
                    </Form>
                </>
            )}
        </div>
    );
}