import axios, { AxiosResponse } from "axios";
import { LoginResponse, QRCode } from "@/lib/types";
import { getCookie } from "cookies-next";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL, //your api URL
});

export default api;

export async function signup(
  email: string,
  password: string,
  first_name: string,
  last_name: string,
  national_id: string,
  date_of_birth: string,
): Promise<AxiosResponse> {
  const res = await api.post("/auth/register", {
    email,
    password,
    first_name,
    last_name,
    national_id,
    date_of_birth,
  });
  return res;
}

export async function login(
  username: string,
  password: string,
): Promise<AxiosResponse<LoginResponse>> {
  const formData = new FormData();
  formData.set("username", username);
  formData.set("password", password);
  const res = await api.post<LoginResponse>("/auth/jwt/login", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return res;
}

export async function logout() {
  const accessToken = await getCookie("accessToken");
  const res = await api.post("/auth/jwt/logout", null, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return res;
}

export async function createBadge(): Promise<QRCode> {
  const accessToken = await getCookie("accessToken");
  const res = await api.post<QRCode>("/scanner/qr_code", null, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return res.data;
}

export async function scanBadge(data: string) {
  const res = await api.post("/scanner", { data });
  return res;
}
