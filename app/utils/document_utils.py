def _only_digits(value: str) -> str:
    return ''.join(ch for ch in value if ch.isdigit())


def _is_repeated_digits(numbers: str) -> bool:
    return numbers and all(ch == numbers[0] for ch in numbers)


def _validate_cpf(numbers: str) -> bool:
    if len(numbers) != 11 or _is_repeated_digits(numbers):
        return False

    digits = [int(ch) for ch in numbers]

    total = sum(digits[i] * (10 - i) for i in range(9))
    first_digit = (total * 10) % 11
    if first_digit == 10:
        first_digit = 0
    if digits[9] != first_digit:
        return False

    total = sum(digits[i] * (11 - i) for i in range(10))
    second_digit = (total * 10) % 11
    if second_digit == 10:
        second_digit = 0

    return digits[10] == second_digit


def _validate_cnpj(numbers: str) -> bool:
    if len(numbers) != 14 or _is_repeated_digits(numbers):
        return False

    digits = [int(ch) for ch in numbers]
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    total = sum(digits[i] * weights1[i] for i in range(12))
    first_digit = total % 11
    first_digit = 0 if first_digit < 2 else 11 - first_digit
    if digits[12] != first_digit:
        return False

    total = sum(digits[i] * weights2[i] for i in range(13))
    second_digit = total % 11
    second_digit = 0 if second_digit < 2 else 11 - second_digit

    return digits[13] == second_digit


def is_valid_cpf_cnpj(value: str) -> bool:
    numbers = _only_digits(value)
    return _validate_cpf(numbers) or _validate_cnpj(numbers)