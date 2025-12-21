from Elias import delta_decode_stream
from Huffman import decode_tree_structure, HuffmanNode
from typing import List, Tuple
import sys
from tqdm import tqdm

# Recursion limit for deep Huffman trees
sys.setrecursionlimit(2500)


def read_bit(bits: List[int], index: int) -> Tuple[int, int]:
    if index >= len(bits): raise ValueError("End of stream")
    return bits[index], index + 1


def decode_huffman_symbol(root: HuffmanNode, bits: List[int], index: int) -> Tuple[int, int]:
    """Traverse the tree bit-by-bit until a leaf is found."""
    current = root
    while current.left is not None or current.right is not None:
        bit, index = read_bit(bits, index)
        if bit == 0:
            current = current.left
        else:
            current = current.right

        if current is None:
            raise ValueError("Invalid Huffman path")

    return current.byte_val, index


def decoder(compressed_filename: str, output_filename: str = None) -> int:
    """
    Smart Decoder: Reads the mode byte first to decide between
    Raw copy or LZSS+Huffman inflation.
    """
    with open(compressed_filename, 'rb') as f:
        file_data = f.read()

    if len(file_data) == 0:
        return 0

    print(f"Reading {compressed_filename} ({len(file_data)} bytes)")

    # Read the Mode Header (First byte)
    mode = file_data[0]
    payload = file_data[1:]  # The rest of the file

    output_data = bytearray()

    if mode == 0:
        # --- Mode 0: RAW ---
        print("Detected Raw Mode (Store). Copying data...")
        output_data = payload

    elif mode == 1:
        # --- Mode 1: COMPRESSED ---
        print("Detected Compressed Mode (Deflate). Inflating...")

        # Convert payload to bits
        bits = []
        for byte in payload:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        # Run decoding logic
        index = 0
        token_count, index = delta_decode_stream(bits, index)
        huff_root, index = decode_tree_structure(bits, index)

        print(f"Tokens to decode: {token_count}")

        # We use tqdm here for the decompression loop
        with tqdm(total=token_count, unit='token', desc='Decoding') as pbar:
            for _ in range(token_count):
                flag, index = read_bit(bits, index)

                if flag == 0:
                    # LITERAL
                    val, index = decode_huffman_symbol(huff_root, bits, index)
                    output_data.append(val)
                else:
                    # MATCH
                    length, index = delta_decode_stream(bits, index)
                    offset, index = delta_decode_stream(bits, index)

                    start = len(output_data) - offset
                    for i in range(length):
                        output_data.append(output_data[start + i])

                pbar.update(1)

    else:
        raise ValueError(f"Unknown compression mode: {mode}")

    # Save Output
    if output_filename is None:
        if compressed_filename.endswith('.compressed'):
            output_filename = compressed_filename[:-11] + '.decompressed'
        else:
            output_filename = compressed_filename + '.decompressed'

    with open(output_filename, 'wb') as f:
        f.write(output_data)

    decompressed_size = len(output_data)
    print(f"Decompressed size: {decompressed_size} bytes")
    print(f"Decoding complete!")
    print(f"Output written to: {output_filename}")

    return decompressed_size