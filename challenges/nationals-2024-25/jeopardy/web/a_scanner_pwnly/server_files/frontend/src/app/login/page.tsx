"use client";

import { useState } from "react";

import api, { login } from "@/lib/api";
import { useRouter } from "next/navigation";
import { getCookie, setCookie } from "cookies-next/client";

interface LoginFormData {
  username: string;
  password: string;
}

export default function LoginPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginFormData>({
    username: "",
    password: "",
  });

  const [formError, setFormError] = useState<string | null>(null);
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    setFormError(null);
  };

  const handleSubmit = async () => {
    const { username, password } = formData;
    try {
      const res = await login(username, password);

      if (res.status !== 200) {
        return;
      }
      console.debug(res.data);
      setCookie("accessToken", res.data.access_token);
      router.push("/badge");
    } catch {
      setFormError(
        "Could not log in to your account. Please try again, and confirm you have the correct account details.",
      );
    }
  };

  return (
    <form
      method="POST"
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      className="flex flex-col gap-4 container max-w-[400px]"
    >
      <div>
        <h2 className="text-2xl">Log In</h2>
        <p className="text-red-500">{formError}</p>
      </div>
      <div className="flex flex-col gap-1">
        <label>Username (Email)</label>
        <input
          name="username"
          onChange={handleChange}
          className="border p-2 rounded-md"
        ></input>
      </div>
      <div className="flex flex-col gap-1">
        <label>Password</label>
        <input
          name="password"
          type="password"
          onChange={handleChange}
          className="border p-2 rounded-md"
        ></input>
      </div>
      <button type="submit" className="button">
        Log In
      </button>
    </form>
  );
}
