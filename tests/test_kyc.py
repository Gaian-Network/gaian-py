import pytest

import gaian

from .conftest import body_of, sent
from .samples import KYC_BODY, KYC_KW, KYC_SUBMITTED


async def test_submit_kyc_without_phone_and_gender_omits_those_keys(httpx_mock, gw):
    httpx_mock.add_response(json=KYC_SUBMITTED)

    await gw.call("submit_kyc", **KYC_KW)

    body = body_of(sent(httpx_mock))
    assert body == KYC_BODY
    assert not {"gender", "phoneCountryCode", "phoneNumber"} & body.keys()


async def test_submit_kyc_drops_empty_string_optional_fields_but_keeps_empty_required(
    httpx_mock, gw
):
    httpx_mock.add_response(json=KYC_SUBMITTED)
    optional_empty = {
        k: ""
        for k in (
            "gender",
            "phone_country_code",
            "phone_number",
            "address_line2",
            "state",
            "zip_code",
            "issue_date",
        )
    }

    await gw.call("submit_kyc", **{**KYC_KW, "first_name": "", **optional_empty})

    body = body_of(sent(httpx_mock))
    assert body == {**KYC_BODY, "firstName": ""}


@pytest.mark.parametrize("doc_type", ["DRIVERS_LICENSE", "RESIDENCE_PERMIT"])
async def test_submit_kyc_accepts_new_document_types_and_sends_phone_gender_and_report(
    httpx_mock, gw, doc_type
):
    httpx_mock.add_response(json=KYC_SUBMITTED)

    await gw.call(
        "submit_kyc",
        **{
            **KYC_KW,
            "type": doc_type,
            "gender": "female",
            "phone_country_code": "+84",
            "phone_number": "912345678",
            "kyc_report": "report-ref",
        },
    )

    assert body_of(sent(httpx_mock)) == {
        **KYC_BODY,
        "type": doc_type,
        "gender": "female",
        "phoneCountryCode": "+84",
        "phoneNumber": "912345678",
        "kycReport": "report-ref",
    }


def test_document_type_constants_include_new_types():
    assert gaian.DocumentType.DRIVERS_LICENSE == "DRIVERS_LICENSE"
    assert gaian.DocumentType.RESIDENCE_PERMIT == "RESIDENCE_PERMIT"
    assert gaian.DocumentType.ID_CARD == "ID_CARD"
    assert gaian.DocumentType.PASSPORT == "PASSPORT"
