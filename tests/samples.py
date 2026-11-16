"""Response and request samples shaped like the service schemas (see the TS SDK types)."""

USER = {
    "id": "usr_1",
    "firstName": "Nguyen",
    "lastName": "Van A",
    "email": "a@example.com",
    "gender": "male",
    "dateOfBirth": "1990-01-15",
    "nationality": "VN",
    "nationalId": "012345678901",
    "type": "ID_CARD",
    "issueDate": "2020-01-01",
    "expiryDate": "2030-01-01",
    "addressLine1": "123 Le Loi",
    "addressLine2": "",
    "city": "HCMC",
    "state": "",
    "zipCode": "",
    "phoneCountryCode": "+84",
    "phoneNumber": "912345678",
    "kycStatus": "APPROVED",
    "rejectReason": "",
}

QR_INFO = {
    "isValid": True,
    "encodedString": "qr",
    "country": "VN",
    "qrProvider": "VIETQR",
    "bankBin": "970436",
    "accountNumber": "0123456789",
    "beneficiaryName": "NGUYEN VAN A",
}

QUOTE = {
    "quoteId": "q1",
    "route": {"routeId": 7},
    "fiatAmount": 150000,
    "fiatCurrency": "VND",
    "settlementAmount": "6.0",
    "settlementCurrency": "USDC",
    "chainId": 101,
    "exchangeRate": "25000",
    "protocolFeeUsd": "0.1",
    "minimumFeeUsd": "0.01",
    "settlementBaseUsd": "6.0",
    "tenantFeeUsd": "0.1",
    "qrInfo": QR_INFO,
    "expiresAt": "2026-11-16T10:02:00Z",
}

DIRECT_QUOTE = {
    **QUOTE,
    "qrInfo": {
        "accountNumber": "0123456789",
        "beneficiaryName": "NGUYEN VAN A",
        "bankBin": "970436",
        "country": "VN",
    },
}

PLACE_ORDER = {
    "orderId": "ord_1",
    "status": 1,
    "statusLabel": "awaiting_deposit",
    "chainId": 101,
    "depositAddress": "0xdeposit",
    "encodedTransaction": "base64tx",
    "expiresAt": "2026-11-16T10:02:00Z",
    "tokenAddress": "0xtoken",
    "settlementAmount": "6.0",
    "settlementAmountBaseUnits": "6000000",
    "settlementCurrency": "USDC",
}

USER_ORDER = {
    "orderId": "ord_1",
    "status": "completed",
    "fiatAmount": "150000",
    "fiatCurrency": "VND",
    "cryptoAmount": "6.0",
    "cryptoCurrency": "USDC",
    "exchangeRate": "25000",
    "protocolFee": "0.1",
    "expiresAt": "2026-11-16T10:02:00Z",
    "createdAt": "2026-11-16T10:00:00Z",
    "payment": {
        "amount": "150000",
        "currency": "VND",
        "status": "paid",
        "provider": "bank",
        "providerRef": "ref1",
    },
    "cryptoTransfer": {
        "amount": "6.0",
        "chain": "solana",
        "token": "USDC",
        "fromAddress": "0xfrom",
        "toAddress": "0xto",
        "txHash": "0xhash",
        "status": "confirmed",
        "isConfirmed": True,
    },
}

KYC_KW = {
    "user_id": "usr_1",
    "first_name": "Nguyen",
    "last_name": "Van A",
    "email": "a@example.com",
    "date_of_birth": "1990-01-15",
    "nationality": "VN",
    "national_id": "012345678901",
    "type": "ID_CARD",
    "expiry_date": "2030-01-01",
    "address_line1": "123 Le Loi",
    "city": "HCMC",
    "country_of_residence": "VN",
    "occupation": "OCC9",
}

KYC_BODY = {
    "firstName": "Nguyen",
    "lastName": "Van A",
    "email": "a@example.com",
    "dateOfBirth": "1990-01-15",
    "nationality": "VN",
    "nationalId": "012345678901",
    "type": "ID_CARD",
    "expiryDate": "2030-01-01",
    "addressLine1": "123 Le Loi",
    "city": "HCMC",
    "countryOfResidence": "VN",
    "occupation": "OCC9",
}

KYC_SUBMITTED = {
    "requestId": "r1",
    "data": {"userId": "usr_1", "email": "a@example.com", "kycStatus": "PROCESSING"},
}
