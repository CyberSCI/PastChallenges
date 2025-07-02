export interface QRCode {
  id: string;
  data: string;
  image_url: string | null;
}

export interface ScanInput {
  data: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
