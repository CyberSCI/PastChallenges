import { API_BASE_URL } from "config";
import { useState, useMemo } from "react";
import { Form, NavLink } from "react-router";
import type { Route } from "../+types";
import type { RegistrationFile, Station } from "~/types/api";
import { getAccessToken } from "~/oidc";

async function getPollingStations() {
    const res = await fetch(`${API_BASE_URL}/PollingStation?offset=0&limit=2500`, {
        headers: {
            "Authorization": `Bearer ${getAccessToken()}`,
        },
    });
    if (res.status === 401) {
        return [];
    }
    if (!res.ok) {
        throw new Error("Failed to fetch polling stations");
    }
    const data = await res.json();
    return data?.results || [];
}

async function getRegistrationFiles() {
    const res = await fetch(`${API_BASE_URL}/Registration/Files?offset=0&limit=50`, {
        headers: {
            "Authorization": `Bearer ${getAccessToken()}`,
        },
    });
    if (res.status === 401) {
        return [];
    }
    if (!res.ok) {
        throw new Error("Failed to fetch registration files");
    }
    const data = await res.json();
    return data?.results || [];
}

async function downloadFile(fileId: string) {
    try {
        const res = await fetch(`${API_BASE_URL}/Files?` + new URLSearchParams({
            path: fileId
        }), {
            headers: {
                "Authorization": `Bearer ${getAccessToken()}`,
            },
        });
        
        if (!res.ok) {
            throw new Error("Failed to download file");
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement("a");
        a.href = url;

        const contentDisposition = res.headers.get("content-disposition");
        const filenameMatch = contentDisposition?.match(/filename="?(.+)"?/);
        a.download = filenameMatch?.[1] ?? "downloaded-file";

        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error downloading file:", error);
        alert("Failed to download file. Please try again later.");
    }
}

async function reviewFile(formData: FormData) {
    const registrationId = formData.get("registrationId");
    const approved = formData.get("approved") === "true" ? true : (formData.get("approved") === "false" ? false : null);

    if (approved === null) {
        throw new Error("Invalid approval status");
    }

    const res = await fetch(`${API_BASE_URL}/Registration/Files/${registrationId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
            approved
        })
    });

    if (!res.ok) {
        throw new Error("Failed to review file");
    }
}

export async function clientAction({
    request,
}: Route.ClientActionArgs) {
    let formData = await request.formData();

    const intent = formData.get("intent");

    switch (intent) {
        case "review-file":
            return reviewFile(formData);
    }
}

export async function clientLoader() {
    const [stations, files] = await Promise.all([
        getPollingStations(),
        getRegistrationFiles(),
    ]);

    return {
        stations,
        files,
    };
}

export default function AdminDashboard({
    loaderData,
}: Route.ComponentProps) {
    const { stations, files } = loaderData as unknown as {
        stations: Station[];
        files: RegistrationFile[];
    };

    const [search, setSearch] = useState("");
    const [page, setPage] = useState(1);
    const itemsPerPage = 10;

    const filtered = useMemo(() => {
        return stations.filter((s) =>
            `${s.street_number} ${s.street_name} ${s.city} ${s.state} ${s.postal_code}`
                .toLowerCase()
                .includes(search.toLowerCase())
        );
    }, [stations, search]);

    

    const totalPages = Math.ceil(filtered.length / itemsPerPage);
    const pageData = filtered.slice(
        (page - 1) * itemsPerPage,
        page * itemsPerPage
    );

    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-4 text-gray-800 text-center">
                Admin Dashboard
            </h2>

            <hr className="mb-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Polling Stations
            </h3>

            <input
                type="text"
                placeholder="Search stations..."
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                }}
                className="w-full mb-4 p-2 border rounded"
            />

            <table className="w-full border text-sm mb-4">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="text-left p-2 border">Address</th>
                        <th className="text-left p-2 border">City</th>
                        <th className="text-left p-2 border">State</th>
                        <th className="text-left p-2 border">Postal Code</th>
                    </tr>
                </thead>
                <tbody>
                    {pageData.map((s) => (
                        <tr key={s.id} className="hover:bg-gray-50">
                            <td className="p-2 border">
                                <NavLink
                                    to={`/admin/stations/${s.id}`}
                                    className="text-blue-600 hover:underline"
                                >
                                    {s.street_number} {s.street_name}
                                </NavLink>
                            </td>
                            <td className="p-2 border">{s.city}</td>
                            <td className="p-2 border">{s.state}</td>
                            <td className="p-2 border">{s.postal_code}</td>
                        </tr>
                    ))}
                    {pageData.length === 0 && (
                        <tr>
                            <td colSpan={4} className="text-center text-gray-500 p-4">
                                No polling stations found.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>

            <div className="flex justify-between items-center mb-4">
                <button
                    disabled={page === 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-4 py-1 border rounded disabled:opacity-50"
                >
                    Previous
                </button>
                <span className="text-sm">
                    Page {page} of {totalPages}
                </span>
                <button
                    disabled={page === totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="px-4 py-1 border rounded disabled:opacity-50"
                >
                    Next
                </button>
            </div>
            
            <hr className="mb-4 border-gray-300" />
            <h3 className="text-xl mb-2">
                Registration Files
            </h3>

            <table className="w-full border text-sm mb-4">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="text-left p-2 border">Registration #</th>
                        <th className="text-left p-2 border">Full Name</th>
                        <th className="text-left p-2 border">Address</th>
                        <th className="text-left p-2 border">Autoscan Result</th>
                        <th className="text-left p-2 border">File</th>
                        <th className="text-left p-2 border">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {files.map((file) => (
                        <tr key={file.id} className="hover:bg-gray-50">
                            <td className="p-2 border">{file.registrationNumber}</td>
                            <td className="p-2 border">
                                {file.first_name} {file.last_name}
                            </td>
                            <td className="p-2 border">
                                {file.registrationAddressNumber} {file.registrationAddressStreet.street_name}, {file.registrationAddressStreet.city}, {file.registrationAddressStreet.state} {file.registrationAddressStreet.postal_code}
                            </td>
                            <td className="p-2 border">
                                {file.registrationFileMatchesInfo ? "Matched" : "Not Matched"}
                            </td>
                            <td className="p-2 border">
                                <button
                                    onClick={() => downloadFile(file.registrationFile)}
                                    className="text-blue-600 hover:underline"
                                >
                                    Download
                                </button>
                            </td>
                            <td className="p-2 border">
                                <Form method="post" className="inline">
                                    <input type="hidden" name="registrationId" value={file.registrationNumber} />
                                    <input type="hidden" name="intent" value="review-file" />
                                    <input type="hidden" name="approved" value="true" />
                                    <button
                                        type="submit"
                                        className="text-blue-600 hover:underline"
                                    >
                                        Approve
                                    </button>
                                </Form>
                                <Form method="post" className="inline">
                                    <input type="hidden" name="registrationId" value={file.registrationNumber} />
                                    <input type="hidden" name="intent" value="review-file" />
                                    <input type="hidden" name="approved" value="false" />
                                    <button
                                        type="submit"
                                        className="text-blue-600 hover:underline"
                                    >
                                        Reject
                                    </button>
                                </Form>
                            </td>
                        </tr>
                    ))}
                    {files.length === 0 && (
                        <tr>
                            <td colSpan={6} className="text-center text-gray-500 p-4">
                                No registration files found.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}