from Elias import delta_decode_stream
from Huffman import decode_tree_structure, HuffmanNode
from typing import List, Tuple
import sys

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
    # Read file and convert to bits (same as before)
    with open(compressed_filename, 'rb') as f:
        data = f.read()

    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    index = 0
    output = bytearray()

    # 1. Read Token Count
    token_count, index = delta_decode_stream(bits, index)
    print(f"Tokens: {token_count}")

    # 2. Read Huffman Tree
    huff_root, index = decode_tree_structure(bits, index)

    # 3. Decode Loop
    for _ in range(token_count):
        # Read Flag
        flag, index = read_bit(bits, index)

        if flag == 0:
            # LITERAL: Use Huffman Tree
            byte_val, index = decode_huffman_symbol(huff_root, bits, index)
            output.append(byte_val)
        else:
            # MATCH: Use Elias
            length, index = delta_decode_stream(bits, index)
            offset, index = delta_decode_stream(bits, index)

            start = len(output) - offset
            for i in range(length):
                output.append(output[start + i])

    # Save
    if output_filename is None:
        output_filename = compressed_filename + '.decompressed'

    with open(output_filename, 'wb') as f:
        f.write(output)

    return len(output)
