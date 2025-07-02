"use client";

import { useState } from "react";

import api, { login, signup } from "@/lib/api";
import { useRouter } from "next/navigation";
import { setCookie } from "cookies-next";

interface SignupFormData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  national_id: string;
  date_of_birth: string;
}
interface FormField {
  label: string;
  name: string;
  type: string;
  placeholder: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState<SignupFormData>({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    national_id: "",
    date_of_birth: "",
  });
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });

    setFormError(null);
  };

  const renderField = ({ label, name, type, placeholder }: FormField) => {
    return (
      <div key={name} className="flex flex-col gap-1">
        <label>{label}</label>
        <input
          name={name}
          onChange={handleChange}
          type={type}
          placeholder={placeholder}
          className="border p-2 rounded-md"
        />
      </div>
    );
  };

  const handleSubmit = async () => {
    const {
      email,
      password,
      first_name,
      last_name,
      national_id,
      date_of_birth,
    } = formData;

    try {
      await signup(
        email,
        password,
        first_name,
        last_name,
        national_id,
        date_of_birth,
      );
    } catch {
      setFormError("Could not create an account.");
      return;
    }

    try {
      const res = await login(email, password);
      setCookie("accessToken", res.data.access_token);
    } catch {
      setFormError("Could not log in to the service.");
      return;
    }

    router.push("/badge");
  };

  const fields: FormField[] = [
    {
      label: "First Name",
      name: "first_name",
      type: "text",
      placeholder: "Juan",
    },
    {
      label: "Last Name",
      name: "last_name",
      type: "text",
      placeholder: "Perez",
    },
    {
      label: "Email",
      name: "email",
      type: "email",
      placeholder: "juanperez@mail.vv",
    },
    {
      label: "Password",
      name: "password",
      type: "password",
      placeholder: "",
    },
    {
      label: "National ID",
      name: "national_id",
      type: "text",
      placeholder: "123456789",
    },
    {
      label: "Date of Birth",
      name: "date_of_birth",
      type: "date",
      placeholder: "01/01/1970",
    },
  ];

  return (
    <form
      method="POST"
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit().catch();
      }}
      className="flex flex-col gap-4 container max-w-[400px]"
    >
      <div>
        <h2 className="text-2xl">Register</h2>
        <p className="text-red-500">{formError}</p>
      </div>
      {fields.map(renderField)}
      <button type="submit" className="button">
        Register
      </button>
    </form>
  );
}
