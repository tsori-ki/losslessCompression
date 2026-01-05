import zlib
import lzma
import os
import time
import sys

# Try to import zstandard (requires 'pip install zstandard')
try:
    import zstandard as zstd

    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False
    print("Warning: 'zstandard' library not found. Skipping Zstd benchmark.")
    print("To fix: pip install zstandard\n")


def format_size(size_bytes):
    """Helper to make file sizes readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def benchmark_compression(filename):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return

    # Read the file into memory
    with open(filename, 'rb') as f:
        original_data = f.read()

    original_size = len(original_data)
    print(f"Benchmarking: {filename}")
    print(f"Original Size: {format_size(original_size)}")
    print("-" * 65)
    print(f"{'Method':<15} | {'Size':<12} | {'Ratio':<8} | {'Time (ms)':<10}")
    print("-" * 65)

    results = []

    # --- 1. zlib (Deflate) ---
    # Level 9 is max compression (comparable to your project goal)
    start = time.time()
    compressed_zlib = zlib.compress(original_data, level=9)
    end = time.time()

    results.append({
        "name": "zlib (Deflate)",
        "data": compressed_zlib,
        "time": (end - start) * 1000
    })

    # --- 2. LZMA ---
    # Preset 9 is max compression
    start = time.time()
    compressed_lzma = lzma.compress(original_data, preset=9)
    end = time.time()

    results.append({
        "name": "LZMA",
        "data": compressed_lzma,
        "time": (end - start) * 1000
    })

    # --- 3. Zstandard (if available) ---
    if HAS_ZSTD:
        # Level 22 is ultra mode (slower, better compression)
        cctx = zstd.ZstdCompressor(level=22)
        start = time.time()
        compressed_zstd = cctx.compress(original_data)
        end = time.time()

        results.append({
            "name": "Zstandard",
            "data": compressed_zstd,
            "time": (end - start) * 1000
        })

    # --- Print Results ---
    # Sort by smallest size to see the winner
    results.sort(key=lambda x: len(x['data']))

    for res in results:
        size = len(res['data'])
        ratio = (size / original_size) * 100
        print(f"{res['name']:<15} | {format_size(size):<12} | {ratio:>6.2f}% | {res['time']:>8.2f} ms")

    print("-" * 65)

    # Verification: Save the smallest result to see it works
    best_method = results[0]
    print(f"Winner: {best_method['name']}")
    print(f"Space Saved: {format_size(original_size - len(best_method['data']))}")


# --- Generate a dummy file if you don't have one ---
def create_sample_file(filename):
    print(f"Creating sample file: {filename}...")
    with open(filename, 'wb') as f:
        # 1. Repeated text (Easy for LZSS)
        f.write(b"Hello World! " * 5000)
        # 2. Sequential numbers (Easy for Delta)
        f.write(bytes(range(256)) * 100)
        # 3. Random data (Hard for everyone)
        f.write(os.urandom(50000))


if __name__ == "__main__":
    # Change this to your actual file path (e.g., 'input_files/Samp1.bin')
    target_file = "input_files/Samp3.bin"

    # Create dummy if file doesn't exist
    if not os.path.exists(target_file):
        create_sample_file(target_file)

    benchmark_compression(target_file)