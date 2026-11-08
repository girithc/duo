"""Test 1 sample — the three Interceptor inputs (money-transfer PR).

Same sample as 01-intercept/subq/contract/input.txt, stored here as data so
Interceptor tests can build the SubQ `state` from it.
"""

TICKET = """\
Issue #42: Add money transfer between accounts

Users must be able to transfer an amount from one account to another.
- Transfer must be atomic: both accounts update or neither does.
- Reject transfers with insufficient balance.
- Amount must be positive.

Acceptance criteria:
- POST endpoint accepts from_account, to_account, amount
- Returns new balances on success
"""

SIGNATURES_SKELETON = """\
# POST /api/transfer  {from_account, to_account, amount} -> {status, balances}
def transfer(from_account: str, to_account: str, amount: Decimal) -> TransferResult: ...
def get_balance(account_id: str) -> Decimal: ...

class InsufficientFundsError(Exception): ...
class InvalidAmountError(Exception): ...

class TransferResult:  # schema only
    status: str
    balances: dict[str, Decimal]
"""

FILE_MANIFEST = """\
A  src/api/routes_transfer.py      (new endpoint)
M  src/services/accounts.py        (modified service)
A  src/models/transfer_result.py   (new schema)
M  requirements.txt                (+1 dependency)
"""
