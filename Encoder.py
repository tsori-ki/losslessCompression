"""
Encoder.py - Lempel-Ziv encoder implementation
Modified to send next byte after match instead of dummy byte
"""
from Elias import delta_encode
from typing import Tuple, List

# Configuration
WINDOW_SIZE = 4096  # Search window size
LOOKAHEAD_SIZE = 1000  # Max match length
MIN_MATCH_LENGTH = 3  # Minimum match length to encode


def read_file(filename: str) -> bytes:
    """
    Read binary file and return its contents as bytes.

    Args:
        filename: Path to the file to read

    Returns:
        bytes: File contents
    """
    with open(filename, 'rb') as f:
        return f.read()


def find_longest_match(data: bytes, i: int) -> Tuple[int, int]:
    """
    Find the longest match in the sliding window before position i.

    Args:
        data: The complete data
        i: Current position in data

    Returns:
        (j, l): where j is the offset (distance back), l is match length
                Returns (0, 0) if no match found
    """
    # Define the search window
    window_start = max(0, i - WINDOW_SIZE)
    lookahead_end = min(len(data), i + LOOKAHEAD_SIZE)

    best_offset = 0  # j - distance back
    best_length = 0  # l - match length

    # Search through the window for matches
    for search_pos in range(window_start, i):
        # Count how many consecutive bytes match
        match_length = 0

        while (i + match_length < lookahead_end and
               data[search_pos + match_length] == data[i + match_length] and
               match_length < LOOKAHEAD_SIZE):
            match_length += 1

        # Update best match if this one is longer
        if match_length > best_length:
            best_length = match_length
            best_offset = i - search_pos  # Distance back

    return best_offset, best_length


def encode(data: bytes, i: int) -> Tuple[int, int, List[int]]:
    """
    Encode one token (match or literal) starting at position i.
    Format: [j][l][byte] where:
    - If l=0: it's a literal, byte contains the literal value
    - If l>0: it's a match, byte contains the next byte after the match

    Args:
        data: Complete file data
        i: Current position in data

    Returns:
        (j, l, bits):
            j: offset (distance back to match), 0 if literal
            l: length of match, 0 if literal
            bits: encoded bits for this token
    """
    # Check if we're at end of data
    if i >= len(data):
        return 0, 0, []

    # Find longest match in the window
    j, l = find_longest_match(data, i)

    bits = []

    # Decide whether to encode as match or literal
    if l >= MIN_MATCH_LENGTH:
        # Encode as MATCH token: [offset j][length l][next byte after match]
        bits.extend(delta_encode(j))  # Encode offset
        bits.extend(delta_encode(l))  # Encode length

        # Encode the byte AFTER the match (or 0 if we're at end of data)
        next_byte_pos = i + l
        if next_byte_pos < len(data):
            byte_val = data[next_byte_pos]
            # Advance by l+1 to skip the match AND the next byte
            advance_by = l + 1
        else:
            # We're at the end, encode a null byte
            byte_val = 0
            # Only advance by l since there's no next byte
            advance_by = l

        # Encode the byte as 8 bits
        for bit_pos in range(7, -1, -1):
            bits.append((byte_val >> bit_pos) & 1)

        return j, advance_by, bits
    else:
        # Encode as LITERAL token: [j=0][l=0][8-bit byte value]
        bits.extend(delta_encode(1))  # j=0 encoded as delta(1) since delta needs n>0
        bits.extend(delta_encode(1))  # l=0 encoded as delta(1) since delta needs n>0

        # Encode the actual byte value as 8 bits
        byte_val = data[i]
        for bit_pos in range(7, -1, -1):
            bits.append((byte_val >> bit_pos) & 1)

        return 0, 1, bits  # j=0, l=1 to advance by 1 byte


def bits_to_bytes(bits: List[int]) -> bytes:
    """
    Convert a list of bits to bytes, padding the final byte with zeros if needed.
    No padding metadata is stored; callers must track the meaningful bit-length.

    Args:
        bits: List of bits (0s and 1s)

    Returns:
        bytes: Packed bytes containing the provided bits with zero padding at the end.
    """
    if len(bits) == 0:
        return b""

    padding_needed = (8 - len(bits) % 8) % 8
    bits_padded = bits + [0] * padding_needed

    byte_array = bytearray()
    for i in range(0, len(bits_padded), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits_padded[i + j]
        byte_array.append(byte_val)

    return bytes(byte_array)


def encoder(filename: str, output_filename: str = None) -> int:
    """
    Main encoder function. Reads file, encodes it using LZ77, and writes output.
    Now sends token count first instead of padding.

    Args:
        filename: Input file to compress
        output_filename: Output compressed file (default: filename + '.compressed')

    Returns:
        int: Compressed file size in bytes
    """
    # Read the input file
    data = read_file(filename)
    original_size = len(data)

    print(f"Original size: {original_size} bytes")

    # First pass: encode everything and count tokens
    all_tokens = []
    i = 0

    while i < len(data):
        j, l, bits = encode(data, i)
        all_tokens.append(bits)
        i += l

        if i % 10000 == 0:
            progress = (i / len(data)) * 100
            print(f"Progress: {progress:.1f}% ({i}/{len(data)} bytes)")

    # Now we know the token count
    token_count = len(all_tokens)
    print(f"Total tokens: {token_count}")

    # Build final bit stream
    all_bits = []

    # 1. Send token count (delta encoded, +1 because delta needs n > 0)
    all_bits.extend(delta_encode(token_count + 1))

    # 2. Send all token bits
    for token_bits in all_tokens:
        all_bits.extend(token_bits)

    # Convert bits to bytes
    compressed_data = bits_to_bytes(all_bits)

    # Determine output filename
    if output_filename is None:
        output_filename = filename + '.compressed'

    # Write compressed data to file
    with open(output_filename, 'wb') as f:
        f.write(compressed_data)

    compressed_size = len(compressed_data)
    compression_ratio = (compressed_size / original_size) * 100

    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {compression_ratio:.2f}%")
    print(f"Saved: {original_size - compressed_size} bytes")

    return compressed_size


# Example usage
if __name__ == "__main__":
    encoder("Samp4.bin", "dd.bin")