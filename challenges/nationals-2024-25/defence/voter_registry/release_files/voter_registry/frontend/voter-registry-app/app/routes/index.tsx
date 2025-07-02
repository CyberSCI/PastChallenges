import { Link } from 'react-router';

export default function Index() {
  return (
    <>
      <div className="flex flex-col md:flex-row gap-6">
        <section className="flex-1 bg-white shadow rounded-xl p-6 border text-center">
          <h2 className="text-2xl font-semibold mb-2">Register to vote, now!</h2>
          <p className="mb-4">Click below to register online, saving you time in-person.</p>
          <Link
            to="/register"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Register
          </Link>
        </section>

        <section className="flex-1 bg-white shadow rounded-xl p-6 border text-center">
          <h2 className="text-2xl font-semibold mb-2">Where can you vote?</h2>
          <p className="mb-4">Click below to find which polling center you can vote at.</p>
          <Link
            to="/lookup"
            className="inline-block px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
          >
            Find Your Polling Station
          </Link>
        </section>
      </div>
    </>
  );
}