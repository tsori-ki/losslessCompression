from Elias import delta_decode_stream
from typing import List, Tuple
import os


def read_byte(bits: List[int], bit_index: int) -> Tuple[int, int]:
    """
    Read the next 8 bits as a single byte.

    Args:
        bits: Complete bit stream
        bit_index: Current position in the stream

    Returns:
        (byte_value, new_bit_index)

    Raises:
        ValueError: If there are not enough bits remaining to read a byte.
    """
    if bit_index + 8 > len(bits):
        raise ValueError("Not enough bits remaining to read a full byte.")
    byte_val = 0
    for i in range(8):
        byte_val = (byte_val << 1) | bits[bit_index + i]

    return byte_val, bit_index + 8


def read_compressed_file(filename: str) -> bytes:
    """
    Read compressed file and return its contents as bytes.

    Args:
        filename: Path to the compressed file

    Returns:
        bytes: Compressed file contents
    """
    with open(filename, 'rb') as f:
        return f.read()


def bytes_to_bits(data: bytes) -> List[int]:
    """
    Convert bytes to a list of bits.

    Args:
        data: Packed byte data

    Returns:
        List[int]: List of bits (0s and 1s)
    """
    bits = []
    for byte in data:
        for bit_pos in range(7, -1, -1):
            bits.append((byte >> bit_pos) & 1)
    return bits


def files_are_equal(original_path: str, reconstructed_path: str, chunk_size: int = 65536) -> bool:
    """
    Compare two files byte-for-byte to verify lossless reconstruction.

    Args:
        original_path: Path to the original file.
        reconstructed_path: Path to the reconstructed/decompressed file.
        chunk_size: Number of bytes to read at a time (defaults to 64 KiB).

    Returns:
        True if files are identical, False otherwise.
    """
    if os.path.getsize(original_path) != os.path.getsize(reconstructed_path):
        return False

    with open(original_path, "rb") as f_orig, open(reconstructed_path, "rb") as f_new:
        while True:
            original_chunk = f_orig.read(chunk_size)
            reconstructed_chunk = f_new.read(chunk_size)

            if not original_chunk and not reconstructed_chunk:
                return True

            if original_chunk != reconstructed_chunk:
                return False


def decode_token(bits: List[int], bit_index: int) -> Tuple[int, int, int, int, int]:
    """
    Decode one token (match or literal) from the bit stream.

    Encoder format:
    - Literal: delta(1) delta(1) [8-bit byte]  (represents j=0, l=0)
    - Match: delta(j) delta(l) [8-bit next_byte]

    Args:
        bits: Complete bit stream
        bit_index: Current position in bit stream

    Returns:
        (marker, j, l, byte_val, new_bit_index):
            marker: 1 for match, 0 for literal
            j: offset (distance back) for matches, 0 for literal
            l: length of match, 0 for literal
            byte_val: the byte value
            new_bit_index: Updated bit position after reading token
    """
    try:
        j_encoded, bit_index = delta_decode_stream(bits, bit_index)
        l_encoded, bit_index = delta_decode_stream(bits, bit_index)
    except IndexError as exc:
        raise ValueError("Unexpected end of bit stream while decoding token.") from exc

    # Read the 8-bit byte
    byte_val, bit_index = read_byte(bits, bit_index)

    # Check if it's a literal (j=1, l=1 means j=0, l=0 in actual values)
    if j_encoded == 1 and l_encoded == 1:
        # Literal token
        return 0, 0, 0, byte_val, bit_index
    else:
        # Match token: j_encoded is offset, l_encoded is length
        return 1, j_encoded, l_encoded, byte_val, bit_index


def decoder(compressed_filename: str, output_filename: str = None) -> int:
    """
    Main decoder function. Reads compressed file and reconstructs original.

    Args:
        compressed_filename: Input compressed file
        output_filename: Output decompressed file (default: compressed_filename + '.decompressed')

    Returns:
        int: Decompressed file size in bytes
    """
    # Read compressed file
    compressed_data = read_compressed_file(compressed_filename)
    print(f"Compressed file size: {len(compressed_data)} bytes")

    # Convert to bits
    bits = bytes_to_bits(compressed_data)
    print(f"Total bits available: {len(bits)}")
    bit_index = 0

    # 1. Read token count (encoded as token_count + 1)
    token_count_plus_one, bit_index = delta_decode_stream(bits, bit_index)
    token_count = token_count_plus_one - 1
    print(f"Token count: {token_count}")

    # 2. Decode all tokens
    output_data = bytearray()

    for token_num in range(token_count):
        try:
            marker, j, l, byte_val, bit_index = decode_token(bits, bit_index)
        except ValueError as exc:
            print(f"ERROR decoding token {token_num}: {exc}")
            break

        if marker == 1:
            # MATCH: copy l bytes from position (current_pos - j)
            # Validate the match
            if j > len(output_data):
                print(f"ERROR at token {token_num}: offset j={j} > current output size {len(output_data)}")
                print(f"This suggests a decoding error. Stopping.")
                break

            # Copy l bytes from position (current_pos - j)
            start_pos = len(output_data) - j
            for i in range(l):
                output_data.append(output_data[start_pos + i])

            # Append the next byte after the match (unless it's 0 and we're at the end)
            # The encoder sends 0 only when it's at the end of file
            if not (byte_val == 0 and token_num == token_count - 1):
                output_data.append(byte_val)

        else:
            # LITERAL: byte_val holds the literal value
            output_data.append(byte_val)

        # Progress indicator
        if (token_num + 1) % 1000 == 0:
            progress = ((token_num + 1) / token_count) * 100
            print(
                f"Progress: {progress:.1f}% ({token_num + 1}/{token_count} tokens), Output size: {len(output_data)} bytes")

    # Determine output filename
    if output_filename is None:
        if compressed_filename.endswith('.compressed'):
            output_filename = compressed_filename[:-11] + '.decompressed'
        else:
            output_filename = compressed_filename + '.decompressed'

    # Write decompressed data
    with open(output_filename, 'wb') as f:
        f.write(bytes(output_data))

    decompressed_size = len(output_data)
    print(f"Decompressed size: {decompressed_size} bytes")
    print(f"Decoding complete!")

    return decompressed_size


# Example usage
if __name__ == "__main__":
    decoder("dd.bin", "output.bin")
    print(files_are_equal('Samp4.bin', 'output.bin'))