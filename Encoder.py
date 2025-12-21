"""
Encoder.py - LZSS (Lempel-Ziv-Storer-Szymanski) implementation
Optimized for binary files using Flag bits.
"""
from Elias import delta_encode
from typing import Tuple, List
from tqdm import tqdm

# Configuration
WINDOW_SIZE = 4096      # Search window size (History)
LOOKAHEAD_SIZE = 258    # Max match length (258 is common in Deflate/Zip)
MIN_MATCH_LENGTH = 3    # Minimum match length to justify encoding overhead


def read_file(filename: str) -> bytes:
    """Read binary file and return its contents as bytes."""
    with open(filename, 'rb') as f:
        return f.read()


def find_longest_match(data: bytes, i: int) -> Tuple[int, int]:
    """
    Find the longest match in the sliding window before position i.
    Returns: (offset, length)
    """
    # Define the search window
    window_start = max(0, i - WINDOW_SIZE)
    # Don't look past the end of data
    lookahead_end = min(len(data), i + LOOKAHEAD_SIZE)

    best_offset = 0
    best_length = 0

    # Search backwards from i-1 down to window_start
    # (Searching backwards is often heuristic to find closer matches first)
    for search_pos in range(i - 1, window_start - 1, -1):

        # Optimization: Quick check if first byte matches
        if data[search_pos] != data[i]:
            continue

        match_length = 0
        while (i + match_length < lookahead_end and
               data[search_pos + match_length] == data[i + match_length]):
            match_length += 1
            if match_length >= LOOKAHEAD_SIZE:
                break

        if match_length > best_length:
            best_length = match_length
            best_offset = i - search_pos

            # Optimization: If we found a very long match, stop searching
            if best_length >= 128:
                break

    return best_offset, best_length


def encode_token(data: bytes, i: int) -> Tuple[int, List[int]]:
    """
    Encode one LZSS token starting at position i.

    Logic:
    1. Try to find a match.
    2. If match length >= MIN_MATCH_LENGTH:
       Output: [1] + [Elias(length)] + [Elias(offset)]
    3. Else:
       Output: [0] + [8-bit literal]

    Returns:
        (advance_by, bits): number of bytes consumed, and the bit list.
    """
    # Check for End of File
    if i >= len(data):
        return 0, []

    # 1. Attempt to find a match
    offset, length = find_longest_match(data, i)

    bits = []

    # 2. Decide: Match or Literal?
    if length >= MIN_MATCH_LENGTH:
        # --- MATCH CASE ---
        # Flag '1' indicates a Match follows
        bits.append(1)

        # Encode Length (using Elias Delta)
        # Note: We encode 'length' directly.
        # (Some variants encode 'length - MIN_MATCH_LENGTH' to save bits,
        # but pure Elias on 'length' is safer for now).
        bits.extend(delta_encode(length))

        # Encode Offset (using Elias Delta)
        bits.extend(delta_encode(offset))

        return length, bits

    else:
        # --- LITERAL CASE ---
        # Flag '0' indicates a Literal follows
        bits.append(0)

        # Encode the byte as 8 bits
        byte_val = data[i]
        for bit_pos in range(7, -1, -1):
            bits.append((byte_val >> bit_pos) & 1)

        return 1, bits


def bits_to_bytes(bits: List[int]) -> bytes:
    """Convert bit list to bytes, padding the end with zeros."""
    if not bits:
        return b""

    padding_needed = (8 - len(bits) % 8) % 8
    # We don't store padding size here because the Decoder
    # will stop based on 'token_count', ignoring trailing padding.
    bits_padded = bits + [0] * padding_needed

    byte_array = bytearray()
    for i in range(0, len(bits_padded), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits_padded[i + j]
        byte_array.append(byte_val)

    return bytes(byte_array)



def encoder(filename: str, output_filename: str = None) -> int:
    data = read_file(filename)
    original_size = len(data)

    print(f"\n=== Encoding: {filename} ===")
    print(f"Original size: {original_size:,} bytes")

    all_tokens = []
    i = 0

    with tqdm(total=len(data), unit='B', unit_scale=True, desc='Encoding') as pbar:
        while i < len(data):
            advance_by, bits = encode_token(data, i)
            all_tokens.append(bits)
            i += advance_by
            pbar.update(advance_by)

    token_count = len(all_tokens)
    print(f"Tokens generated: {token_count:,}")

    all_bits = []
    all_bits.extend(delta_encode(token_count))
    for token_bits in all_tokens:
        all_bits.extend(token_bits)

    compressed_data = bits_to_bytes(all_bits)

    if output_filename is None:
        output_filename = filename + '.compressed'

    with open(output_filename, 'wb') as f:
        f.write(compressed_data)

    compressed_size = len(compressed_data)
    compression_ratio = (compressed_size / original_size) * 100

    print(f"Compressed size: {compressed_size:,} bytes")
    print(f"Compression ratio: {compression_ratio:.2f}%")
    print(f"Bytes saved: {original_size - compressed_size:,}")
    print(f"Output file: {output_filename}")
    print("=" * 40 + "\n")

    return compressed_size