import logging

import httpx
import pytest

import gaian

from .conftest import SECRET

REQUEST_SECRET = "quote-secret-body-value"
RESPONSE_SECRET = "4111111111111111"
ERROR_SECRET = "error-body-secret-value"


@pytest.mark.parametrize("status", [200, 400], ids=["success", "error"])
async def test_debug_log_has_method_and_path_but_no_signature_or_bodies(
    httpx_mock, make_harness, caplog, capsys, status
):
    seen = {}

    def respond(request: httpx.Request) -> httpx.Response:
        seen["signature"] = request.headers["x-gaian-signature"]
        seen["timestamp"] = request.headers["x-gaian-timestamp"]
        body = (
            {"message": ERROR_SECRET}
            if status == 400
            else {"requestId": "r1", "data": {"cardPan": RESPONSE_SECRET}}
        )
        return httpx.Response(status, json=body)

    httpx_mock.add_callback(respond)
    gw = make_harness(debug=True)
    caplog.set_level(logging.DEBUG)

    if status == 400:
        with pytest.raises(gaian.GaianAPIError):
            await gw.call("place_order", quote_id=REQUEST_SECRET)
    else:
        await gw.call("place_order", quote_id=REQUEST_SECRET)

    out = capsys.readouterr()
    log = "\n".join([r.getMessage() for r in caplog.records] + [caplog.text, out.out, out.err])
    assert "/api/v2/orders" in log
    for hidden in (seen["signature"], SECRET, REQUEST_SECRET, RESPONSE_SECRET, ERROR_SECRET):
        assert hidden not in log
