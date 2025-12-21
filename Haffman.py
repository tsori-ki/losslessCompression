import heapq
from collections import defaultdict
import pickle


class HuffmanNode:
    def __init__(self, byte_val, freq):
        self.byte_val = byte_val
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_frequency_table(data):
    """Build frequency table for all bytes in data"""
    freq_table = defaultdict(int)
    for byte in data:
        freq_table[byte] += 1
    return freq_table


def build_huffman_tree(freq_table):
    """Build Huffman tree from frequency table"""
    if not freq_table:
        return None

    # Create a min heap with all bytes
    heap = []
    for byte_val, freq in freq_table.items():
        node = HuffmanNode(byte_val, freq)
        heapq.heappush(heap, node)

    # Handle single byte case
    if len(heap) == 1:
        root = HuffmanNode(None, heap[0].freq)
        root.left = heapq.heappop(heap)
        return root

    # Build tree by combining nodes
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)

        parent = HuffmanNode(None, left.freq + right.freq)
        parent.left = left
        parent.right = right

        heapq.heappush(heap, parent)

    return heap[0]


def generate_huffman_codes(root):
    """Generate Huffman codes for all bytes (returns array of 256 strings)"""
    codes = [''] * 256  # Initialize array for all possible byte values (0-255)

    if root is None:
        return codes

    # Handle single node case
    if root.left is None and root.right is None:
        codes[root.byte_val] = '0'
        return codes

    def traverse(node, code):
        if node is None:
            return

        # Leaf node - store the code
        if node.byte_val is not None:
            codes[node.byte_val] = code
            return

        # Traverse left and right
        traverse(node.left, code + '0')
        traverse(node.right, code + '1')

    traverse(root, '')
    return codes


def get_huffman_codes_array(filename):
    """
    Read a file and return an array of 256 Huffman codes.
    Index i contains the Huffman code for byte value i.

    Example:
        codes[0] = Huffman code for byte 00000000
        codes[1] = Huffman code for byte 00000001
        codes[255] = Huffman code for byte 11111111
    """
    # Read file as bytes
    with open(filename, 'rb') as f:
        data = f.read()

    if not data:
        return [''] * 256

    # Build frequency table
    freq_table = build_frequency_table(data)

    # Build Huffman tree
    tree = build_huffman_tree(freq_table)

    # Generate codes
    codes = generate_huffman_codes(tree)

    return codes

check_arr = get_huffman_codes_array('Samp1.bin')
print(check_arr)