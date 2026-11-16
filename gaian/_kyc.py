from __future__ import annotations

from ._core import Call, required, without_empty
from ._models import (
    GenerateKycLinkResponse,
    ImportSharedKycResponse,
    SubmitKycResponse,
    UpdateKycResponse,
    UserResponse,
)


def submit_kyc(
    *,
    user_id: str,
    first_name: str,
    last_name: str,
    email: str,
    date_of_birth: str,
    nationality: str,
    national_id: str,
    type: str,
    expiry_date: str,
    address_line1: str,
    city: str,
    country_of_residence: str,
    occupation: str,
    gender: str | None = None,
    issue_date: str | None = None,
    address_line2: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    phone_country_code: str | None = None,
    phone_number: str | None = None,
    front_id_image: str | None = None,
    back_id_image: str | None = None,
    hold_id_image: str | None = None,
    kyc_report: str | None = None,
) -> Call[UserResponse[SubmitKycResponse]]:
    """Submits KYC information for a user, without the hosted verification flow.

    Dates are ``YYYY-MM-DD``; ``nationality`` and ``country_of_residence`` are ISO 3166-1
    alpha-2; ``type`` is a DocumentType and ``occupation`` an Occupation value.
    ``phone_country_code`` is 1-3 digits with an optional ``+``; ``phone_number`` is 6-12
    digits. Images and ``kyc_report`` are data URIs. An optional field left as None or ``""``
    is not sent.
    """
    return Call(
        "POST",
        ("users", required("user_id", user_id), "kyc"),
        UserResponse[SubmitKycResponse],
        body={
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "dateOfBirth": date_of_birth,
            "nationality": nationality,
            "nationalId": national_id,
            "type": type,
            "expiryDate": expiry_date,
            "addressLine1": address_line1,
            "city": city,
            "countryOfResidence": country_of_residence,
            "occupation": occupation,
            **without_empty(
                gender=gender,
                issueDate=issue_date,
                addressLine2=address_line2,
                state=state,
                zipCode=zip_code,
                phoneCountryCode=phone_country_code,
                phoneNumber=phone_number,
                frontIdImage=front_id_image,
                backIdImage=back_id_image,
                holdIdImage=hold_id_image,
                kycReport=kyc_report,
            ),
        },
    )


def update_kyc(
    *,
    user_id: str,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    date_of_birth: str | None = None,
    nationality: str | None = None,
    national_id: str | None = None,
    type: str | None = None,
    expiry_date: str | None = None,
    address_line1: str | None = None,
    city: str | None = None,
    country_of_residence: str | None = None,
    occupation: str | None = None,
    gender: str | None = None,
    issue_date: str | None = None,
    address_line2: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    phone_country_code: str | None = None,
    phone_number: str | None = None,
    front_id_image: str | None = None,
    back_id_image: str | None = None,
    hold_id_image: str | None = None,
    kyc_report: str | None = None,
) -> Call[UserResponse[UpdateKycResponse]]:
    """Updates part of a user's KYC information. Only the fields that are set are sent.

    Same formats as ``submit_kyc``. A field left as None or ``""`` is not sent, so this call
    cannot clear a field.
    """
    return Call(
        "PATCH",
        ("users", required("user_id", user_id), "kyc"),
        UserResponse[UpdateKycResponse],
        body=without_empty(
            firstName=first_name,
            lastName=last_name,
            email=email,
            dateOfBirth=date_of_birth,
            nationality=nationality,
            nationalId=national_id,
            type=type,
            expiryDate=expiry_date,
            addressLine1=address_line1,
            city=city,
            countryOfResidence=country_of_residence,
            occupation=occupation,
            gender=gender,
            issueDate=issue_date,
            addressLine2=address_line2,
            state=state,
            zipCode=zip_code,
            phoneCountryCode=phone_country_code,
            phoneNumber=phone_number,
            frontIdImage=front_id_image,
            backIdImage=back_id_image,
            holdIdImage=hold_id_image,
            kycReport=kyc_report,
        ),
    )


def generate_kyc_link(
    *, user_id: str, callback_url: str | None = None
) -> Call[UserResponse[GenerateKycLinkResponse]]:
    """Creates a hosted KYC session URL for a user. The URL is time-limited: do not cache it."""
    return Call(
        "POST",
        ("users", required("user_id", user_id), "kyc-url"),
        UserResponse[GenerateKycLinkResponse],
        body=without_empty(callbackUrl=callback_url),
    )


def import_shared_kyc(
    *, user_id: str, share_token: str
) -> Call[UserResponse[ImportSharedKycResponse]]:
    """Imports a verification the user completed elsewhere, using the provider's share token.

    Raises GaianAPIError with code CONFLICT when the session was already imported.
    """
    return Call(
        "POST",
        ("users", required("user_id", user_id), "kyc", "import-shared"),
        UserResponse[ImportSharedKycResponse],
        body={"shareToken": share_token},
    )
