from dataclasses import dataclass

@dataclass
class Stock:
    ticker: str
    company_name: str
    price: float
    previous_price: float = 0.0

    @property
    def change_pct(self) -> float:
        if self.previous_price == 0:
            return 0.0
        return ((self.price - self.previous_price) / self.previous_price) * 100
