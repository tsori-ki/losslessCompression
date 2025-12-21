import heapq
from collections import defaultdict
from typing import List, Dict, Optional, Tuple


class HuffmanNode:
    def __init__(self, byte_val, freq):
        self.byte_val = byte_val
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree_from_freqs(freq_table: Dict[int, int]) -> Optional[HuffmanNode]:
    """Build Huffman tree from a frequency dictionary."""
    if not freq_table:
        return None

    heap = []
    for byte_val, freq in freq_table.items():
        node = HuffmanNode(byte_val, freq)
        heapq.heappush(heap, node)

    # Handle single byte case (rare but possible)
    if len(heap) == 1:
        root = HuffmanNode(None, heap[0].freq)
        root.left = heapq.heappop(heap)
        return root

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        parent = HuffmanNode(None, left.freq + right.freq)
        parent.left = left
        parent.right = right

        heapq.heappush(heap, parent)

    return heap[0]


def generate_huffman_codes(root: HuffmanNode) -> List[List[int]]:
    """
    Generate codes for all bytes.
    Returns: List of 256 items. Index i is the list of bits for byte i.
    """
    # Initialize with empty lists (or None)
    codes = [[] for _ in range(256)]

    if root is None:
        return codes

    # Edge case: Tree has only one node (the root is a leaf)
    if root.left is None and root.right is None:
        if root.byte_val is not None:
            codes[root.byte_val] = [0]
        return codes

    def traverse(node, current_bits):
        if node is None:
            return

        if node.byte_val is not None:
            codes[node.byte_val] = current_bits[:]
            return

        current_bits.append(0)
        traverse(node.left, current_bits)
        current_bits.pop()

        current_bits.append(1)
        traverse(node.right, current_bits)
        current_bits.pop()

    traverse(root, [])
    return codes


# --- Tree Serialization (Saving/Loading) ---

def encode_tree_structure(node: HuffmanNode) -> List[int]:
    """
    Serialize the tree structure to bits so the Decoder can rebuild it.
    Format:
    - Internal Node: 0
    - Leaf Node: 1 + [8-bit byte value]
    """
    bits = []

    def traverse(n):
        if n is None:
            return

        # Check if leaf
        if n.left is None and n.right is None:
            # Mark as Leaf (1)
            bits.append(1)
            # Write the byte value (8 bits)
            val = n.byte_val
            for i in range(7, -1, -1):
                bits.append((val >> i) & 1)
        else:
            # Mark as Internal Node (0)
            bits.append(0)
            traverse(n.left)
            traverse(n.right)

    traverse(node)
    return bits


def decode_tree_structure(bit_stream: List[int], index: int) -> Tuple[Optional[HuffmanNode], int]:
    """
    Reconstruct the Huffman Tree from the bit stream.
    Returns: (Root Node, new_index)
    """
    # Read "type" bit
    if index >= len(bit_stream):
        return None, index

    bit_val = bit_stream[index]
    index += 1

    if bit_val == 1:
        # It's a LEAF: Read next 8 bits as the byte value
        byte_val = 0
        for _ in range(8):
            byte_val = (byte_val << 1) | bit_stream[index]
            index += 1

        # Create leaf node (freq doesn't matter for decoding)
        return HuffmanNode(byte_val, 0), index
    else:
        # It's an INTERNAL NODE: Recursively read left and right children
        node = HuffmanNode(None, 0)
        node.left, index = decode_tree_structure(bit_stream, index)
        node.right, index = decode_tree_structure(bit_stream, index)
        return node, index