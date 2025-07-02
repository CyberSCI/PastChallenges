"use client";

import { Fragment } from "react";
import { useRouter } from "next/navigation";
import { getCookie } from "cookies-next/client";

export default function Home() {
  const router = useRouter();
  const accessToken = getCookie("accessToken")?.toString();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl text-center">Val Verde Election Badge Scanner</h1>
      {accessToken ? (
        <div className="flex flex-col gap-2">
          <button className="button" onClick={() => router.push("/login")}>
            Log In
          </button>
          <button className="button" onClick={() => router.push("/register")}>
            Register
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <button className="button" onClick={() => router.push("/badge")}>
            Badges
          </button>
          <button className="button" onClick={() => router.push("/scanner")}>
            Scanner
          </button>
        </div>
      )}
    </div>
  );
}
