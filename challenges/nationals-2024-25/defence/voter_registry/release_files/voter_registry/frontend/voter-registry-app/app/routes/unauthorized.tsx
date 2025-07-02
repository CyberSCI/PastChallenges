export default function Unauthorized() {
    return (
        <div className="w-full bg-white p-6 rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-4 text-gray-800 text-center">
                Unauthorized
            </h2>
            <p className="mb-4 text-center text-red-600">
                You do not have permission to access this page. Please contact your system administrator if you believe this is an error.
            </p>
        </div>
    );
}
