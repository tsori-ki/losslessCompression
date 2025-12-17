from typing import List, Tuple


def gamma_encode(n: int) -> List[int]:
    """
    Encodes a positive integer n using Elias gamma coding.
    Returns a list of bits (0s and 1s).
    """
    if n <= 0:
        raise ValueError("Elias coding only supports positive integers (n > 0).")

    # Binary representation of n
    binary_str = bin(n)[2:]
    # Prefix: (length of binary - 1) zeros
    prefix = [0] * (len(binary_str) - 1)
    # Value: binary digits as integers
    payload = [int(bit) for bit in binary_str]

    return prefix + payload


def delta_encode(n: int) -> List[int]:
    """
    Encodes a positive integer n using Elias delta coding.
    Useful for larger integers to save prefix space.
    """
    if n <= 0:
        raise ValueError("Elias coding only supports positive integers (n > 0).")

    binary_str = bin(n)[2:]
    n_bits = len(binary_str)

    # Part 1 & 2: Gamma encode the length of the binary representation
    length_prefix = gamma_encode(n_bits)
    # Part 3: The original binary representation without the leading '1'
    suffix = [int(bit) for bit in binary_str[1:]]

    return length_prefix + suffix


def delta_decode_stream(bit_stream: List[int], index: int) -> Tuple[int, int]:
    """
    Decodes an Elias delta code starting from a specific index in a bit list.
    Returns: (decoded_integer, next_index_in_stream)
    """
    # 1. Decode Gamma part to find 'N' (the length of the value)
    # Count leading zeros
    zero_count = 0
    while bit_stream[index + zero_count] == 0:
        zero_count += 1

    # Move pointer to the start of Gamma binary part
    index += zero_count
    # Read the length value (Gamma binary part)
    # The length of this part is zero_count + 1
    bits_for_length = bit_stream[index: index + zero_count + 1]
    length_val = int("".join(map(str, bits_for_length)), 2)
    index += len(bits_for_length)

    # 2. Use 'length_val' to extract the actual Elias Delta value
    # We read (length_val - 1) bits and prepend the hidden '1'
    if length_val == 1:
        return 1, index

    remaining_bits = bit_stream[index: index + length_val - 1]
    value_binary = "1" + "".join(map(str, remaining_bits))
    decoded_value = int(value_binary, 2)

    return decoded_value, index + (length_val - 1)