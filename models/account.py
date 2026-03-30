class Account:
    """Expert pattern: Account is the expert on fund sufficiency because it owns the balance data."""

    def __init__(self, balance: float):
        self.balance = balance

    def is_funds_sufficient(self, amount: float) -> bool:
        """Expert pattern: only Account checks fund sufficiency."""
        return self.balance >= amount

    def debit(self, amount: float) -> None:
        if not self.is_funds_sufficient(amount):
            raise ValueError("Insufficient funds")
        self.balance -= amount

    def credit(self, amount: float) -> None:
        self.balance += amount
