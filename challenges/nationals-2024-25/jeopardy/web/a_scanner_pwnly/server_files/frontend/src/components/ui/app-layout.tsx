"use client";

import { logout } from "@/lib/api";
import { deleteCookie, getCookie } from "cookies-next/client";
import { useRouter } from "next/navigation";
import { Fragment } from "react";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const router = useRouter();
  const accessToken = getCookie("accessToken")?.toString();

  function renderMenu() {
    if (accessToken) {
      return (
        <Fragment>
          <a href="/badge">Badges</a>
          <a href="/scanner">Scanner</a>
          <button className="button" onClick={handleLogout}>
            Logout
          </button>
        </Fragment>
      );
    }
    return (
      <Fragment>
        <a href="/login">Login</a>
        <a href="/register">Register</a>
      </Fragment>
    );
  }

  async function handleLogout() {
    await logout();
    deleteCookie("accessToken");
    router.push("/login");
  }

  return (
    <div className="flex h-dvh flex-col overflow-x-clip p-2">
      <header className="flex justify-between">
        <h1 className="text-xl">Val Verde Badge Scanner</h1>
        <nav className="flex items-center gap-4">{renderMenu()}</nav>
      </header>
      <main className="flex justify-center">{children}</main>
      <footer></footer>
    </div>
  );
}
