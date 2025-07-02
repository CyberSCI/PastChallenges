export type Street = {
    street_name: string;
    city: string;
    state: string;
    postal_code: string;
}

export type Advisory = {
    id: number;
    message: string;
    created_at: string;
    url: string;
};

export type Station = {
    id: number;
    street_number: number;
    street_name: string;
    city: string;
    state: string;
    postal_code: string;

    streets?: Street[];
    advisories?: Advisory[];
};

export type RegistrationFile = {
    id: number;
    first_name: string;
    last_name: string;
    birthdate: string;
    photo_id_number: string;
    registrationNumber: number;
    registrationFile: string;
    registrationFileMatchesInfo: boolean;
    registrationFileReviewed: boolean;
    registrationAddressNumber: string;
    registrationAddressStreet: Street;
}