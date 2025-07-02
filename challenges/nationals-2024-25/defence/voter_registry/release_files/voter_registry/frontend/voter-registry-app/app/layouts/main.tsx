import { Link, Outlet } from 'react-router';
import flag from 'public/flag.png';

export default function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-blue-800 text-white p-4 shadow-md">
        <Link to="/" className="text-white font-bold text-lg">
          <h1 className="text-xl text-center font-semibold">
            Voter Registration | Government of Val Verde <img src={flag} alt="Val Verde Logo" className="inline-block h-8 ml-1" />
          </h1>
        </Link>
      </header>

      <main className="w-full md:w-[720px] mx-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}