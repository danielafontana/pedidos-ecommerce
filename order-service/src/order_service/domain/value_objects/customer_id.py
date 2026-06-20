from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerId:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Customer id cannot be empty")

    def __str__(self) -> str:
        return self.value
