from Elias import delta_encode
from Huffman import build_huffman_tree_from_freqs, generate_huffman_codes, encode_tree_structure
from typing import Tuple, List
from collections import defaultdict, deque
from tqdm import tqdm

# Configuration
WINDOW_SIZE = 4096
LOOKAHEAD_SIZE = 128  # Deflate typically uses smaller lookaheads (32-258)
MIN_MATCH_LENGTH = 3


def read_file(filename: str) -> bytes:
    with open(filename, 'rb') as f:
        return f.read()


def find_longest_match(data: bytes, i: int) -> Tuple[int, int]:
    """Same as before: returns (offset, length)"""
    window_start = max(0, i - WINDOW_SIZE)
    lookahead_end = min(len(data), i + LOOKAHEAD_SIZE)

    best_offset = 0
    best_length = 0

    # Optimization: limit search steps for speed if needed
    for search_pos in range(i - 1, window_start - 1, -1):
        if data[search_pos] != data[i]:
            continue

        match_length = 0
        while (i + match_length < lookahead_end and
               data[search_pos + match_length] == data[i + match_length]):
            match_length += 1
            if match_length >= LOOKAHEAD_SIZE: break

        if match_length > best_length:
            best_length = match_length
            best_offset = i - search_pos
            if best_length >= 64: break  # Early exit for speed

    return best_offset, best_length


def bits_to_bytes(bits: List[int]) -> bytes:
    """Helper to pack bits"""
    if not bits: return b""
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
    Smart Encoder: Tries to compress using LZSS+Huffman.
    If compression fails to reduce size, falls back to 'Raw Mode'.
    """
    data = read_file(filename)
    original_size = len(data)
    print(f"Compressing {filename}\nOriginal size: {original_size} bytes")

    # --- Pass 1: LZSS Analysis (in memory) ---
    tokens = []
    literal_freqs = defaultdict(int)
    i = 0

    # We use tqdm here to show progress during the heavy lifting
    with tqdm(total=len(data), unit='B', unit_scale=True, desc='Encoding') as pbar:
        while i < len(data):
            offset, length = find_longest_match(data, i)

            if length >= MIN_MATCH_LENGTH:
                # MATCH Found
                tokens.append(('M', length, offset))
                i += length
                pbar.update(length)
            else:
                # LITERAL
                byte_val = data[i]
                tokens.append(('L', byte_val))
                literal_freqs[byte_val] += 1
                i += 1
                pbar.update(1)

    token_count = len(tokens)
    print(f"Done encoding, total tokens: {token_count}")

    # --- Build Huffman Tree ---
    # Create a dummy entry if file was empty or only matches
    if not literal_freqs: literal_freqs[0] = 1

    huff_root = build_huffman_tree_from_freqs(literal_freqs)
    huff_codes = generate_huffman_codes(huff_root)

    # --- Pass 2: Generate Bitstream ---
    # We construct the compressed data in memory to check its size
    all_bits = []

    # Header: Token Count
    all_bits.extend(delta_encode(token_count))

    # Header: Huffman Tree Structure
    all_bits.extend(encode_tree_structure(huff_root))

    # Payload: Tokens
    for token in tokens:
        if token[0] == 'L':
            # Literal: Flag 0 + Huffman Code
            all_bits.append(0)
            all_bits.extend(huff_codes[token[1]])
        else:
            # Match: Flag 1 + Elias Length + Elias Offset
            all_bits.append(1)
            all_bits.extend(delta_encode(token[1]))
            all_bits.extend(delta_encode(token[2]))

    compressed_body = bits_to_bytes(all_bits)

    # --- Safety Check: Store Mode vs Deflate Mode ---
    final_output = bytearray()

    # Logic: 1 byte for Mode + compressed body vs Original
    if len(compressed_body) + 1 < original_size:
        # Mode 1: Compressed (Deflate)
        print("Compression successful. Using Deflate mode.")
        final_output.append(1)
        final_output.extend(compressed_body)
    else:
        # Mode 0: Raw (Fallback)
        print("Compression inefficient. Fallback to Raw Mode.")
        final_output.append(0)
        final_output.extend(data)

    # Write to File
    if output_filename is None:
        output_filename = filename + '.compressed'

    with open(output_filename, 'wb') as f:
        f.write(final_output)

    final_size = len(final_output)
    compression_ratio = (final_size / original_size) * 100

    print(f"Compressed size: {final_size} bytes")
    print(f"Compression ratio: {compression_ratio:.2f}%")
    print(f"Saved: {original_size - final_size} bytes")
    print(f"Output written to: {output_filename}")
    print(f"__________________________________")

    return final_size