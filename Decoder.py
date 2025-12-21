from Elias import delta_decode_stream
from typing import List, Tuple
import os
import sys

# Increase recursion depth just in case, though not used here directly.
sys.setrecursionlimit(2000)


def read_byte(bits: List[int], bit_index: int) -> Tuple[int, int]:
    """Read the next 8 bits as a single byte value."""
    if bit_index + 8 > len(bits):
        raise ValueError("Not enough bits remaining to read a full byte.")
    byte_val = 0
    for i in range(8):
        byte_val = (byte_val << 1) | bits[bit_index + i]

    return byte_val, bit_index + 8


def read_bit(bits: List[int], bit_index: int) -> Tuple[int, int]:
    """Read a single bit."""
    if bit_index >= len(bits):
        raise ValueError("Unexpected end of stream reading flag bit.")
    return bits[bit_index], bit_index + 1


def read_compressed_file(filename: str) -> bytes:
    """Read compressed file and return its contents as bytes."""
    with open(filename, 'rb') as f:
        return f.read()


def bytes_to_bits(data: bytes) -> List[int]:
    """Convert bytes to a list of bits."""
    bits = []
    for byte in data:
        # Standard big-endian bit extraction for each byte
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def files_are_equal(original_path: str, reconstructed_path: str, chunk_size: int = 65536) -> bool:
    """Compare two files byte-for-byte."""
    if os.path.getsize(original_path) != os.path.getsize(reconstructed_path):
        print(f"Size mismatch: {os.path.getsize(original_path)} vs {os.path.getsize(reconstructed_path)}")
        return False

    with open(original_path, "rb") as f_orig, open(reconstructed_path, "rb") as f_new:
        while True:
            original_chunk = f_orig.read(chunk_size)
            reconstructed_chunk = f_new.read(chunk_size)
            if not original_chunk and not reconstructed_chunk:
                return True
            if original_chunk != reconstructed_chunk:
                return False


def decode_lzss_token(bits: List[int], bit_index: int) -> Tuple[bool, int, int, int, int]:
    """
    Decode one LZSS token (Literal or Match).

    Returns:
        (is_match, length, offset, literal_val, new_bit_index)
        - is_match: True if match, False if literal
        - length: Match length (if match)
        - offset: Match offset (if match)
        - literal_val: Byte value (if literal)
        - new_bit_index: Updated position
    """
    # 1. Read Flag Bit
    flag, bit_index = read_bit(bits, bit_index)

    if flag == 0:
        # --- LITERAL CASE (0) ---
        # Format: [0] [8-bit literal]
        byte_val, bit_index = read_byte(bits, bit_index)
        return False, 0, 0, byte_val, bit_index
    else:
        # --- MATCH CASE (1) ---
        # Format: [1] [Elias Length] [Elias Offset]

        # Read Length
        length, bit_index = delta_decode_stream(bits, bit_index)

        # Read Offset
        offset, bit_index = delta_decode_stream(bits, bit_index)

        return True, length, offset, 0, bit_index


# Decoder.py

def decoder(compressed_filename: str, output_filename: str = None) -> int:
    print(f"\n=== Decoding: {compressed_filename} ===")
    compressed_data = read_compressed_file(compressed_filename)
    print(f"Compressed file size: {len(compressed_data):,} bytes")

    bits = bytes_to_bits(compressed_data)
    print(f"Total bits: {len(bits):,}")

    bit_index = 0
    output_data = bytearray()

    try:
        token_count, bit_index = delta_decode_stream(bits, bit_index)
    except Exception as e:
        print("Error: Could not decode token count header. File may be empty or corrupted.")
        return 0

    print(f"Tokens to decode: {token_count:,}")

    for token_num in range(token_count):
        try:
            is_match, length, offset, literal_val, bit_index = decode_lzss_token(bits, bit_index)
            if not is_match:
                output_data.append(literal_val)
            else:
                if offset > len(output_data):
                    print(f"Error at token {token_num}: Offset {offset} > History {len(output_data)}")
                    break
                start_pos = len(output_data) - offset
                for i in range(length):
                    output_data.append(output_data[start_pos + i])
        except ValueError as e:
            print(f"Decoding error at token {token_num}: {e}")
            break
        if token_num % 10000 == 0 and token_num > 0:
            print(f"  Decoded {token_num:,}/{token_count:,} tokens...")

    print("Decoding complete.")

    if output_filename is None:
        if compressed_filename.endswith('.compressed'):
            output_filename = compressed_filename[:-11] + '.decompressed'
        else:
            output_filename = compressed_filename + '.decompressed'

    with open(output_filename, 'wb') as f:
        f.write(bytes(output_data))

    print(f"Reconstructed file: {output_filename}")
    print(f"Reconstructed size: {len(output_data):,} bytes")
    print("=" * 40 + "\n")
    return len(output_data)
