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
    data = read_file(filename)
    original_size = len(data)
    print(f"Compressing {filename} ({original_size} bytes)")

    # --- PASS 1: LZSS Logic & Frequency Analysis ---
    # We store tokens as tuples:
    #   ('L', byte_val)        -> Literal
    #   ('M', length, offset)  -> Match

    tokens = []
    literal_freqs = defaultdict(int)
    i = 0

    with tqdm(total=len(data), desc='Analyzing (LZSS Pass 1)') as pbar:
        while i < len(data):
            offset, length = find_longest_match(data, i)

            if length >= MIN_MATCH_LENGTH:
                # Decide: MATCH
                tokens.append(('M', length, offset))
                i += length
                pbar.update(length)
            else:
                # Decide: LITERAL
                byte_val = data[i]
                tokens.append(('L', byte_val))
                literal_freqs[byte_val] += 1
                i += 1
                pbar.update(1)

    # --- BUILD HUFFMAN TREE ---
    print(f"Building Huffman Tree for {len(literal_freqs)} unique literals...")
    # If no literals (rare), add a dummy to prevent errors
    if not literal_freqs:
        literal_freqs[0] = 1

    huff_root = build_huffman_tree_from_freqs(literal_freqs)
    huff_codes = generate_huffman_codes(huff_root)

    # --- PASS 2: Encode Data ---
    all_bits = []

    # 1. Header: Total Token Count (Elias)
    all_bits.extend(delta_encode(len(tokens)))

    # 2. Header: Huffman Tree Structure
    tree_bits = encode_tree_structure(huff_root)
    all_bits.extend(tree_bits)

    # 3. Payload: The Tokens
    print("Encoding bitstream...")
    for token in tokens:
        if token[0] == 'L':
            # Format: [0] + [Huffman Code]
            all_bits.append(0)
            all_bits.extend(huff_codes[token[1]])
        else:
            # Format: [1] + [Elias Length] + [Elias Offset]
            all_bits.append(1)
            all_bits.extend(delta_encode(token[1]))  # length
            all_bits.extend(delta_encode(token[2]))  # offset

    # Write to file
    compressed_data = bits_to_bytes(all_bits)
    if output_filename is None:
        output_filename = filename + '.compressed'

    with open(output_filename, 'wb') as f:
        f.write(compressed_data)

    print(f"Saved to {output_filename}")
    print(f"Size: {len(compressed_data)} bytes (Ratio: {len(compressed_data) / original_size:.2%})")
    return len(compressed_data)