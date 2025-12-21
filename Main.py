# Main.py

import os
import Encoder
import Decoder

input_dir = 'input_files'
output_dir = 'output_files'
reconstructed_dir = 'reconstructed_files'

os.makedirs(output_dir, exist_ok=True)
os.makedirs(reconstructed_dir, exist_ok=True)

print("\n=== Batch Compression, Decompression, and Verification ===\n")
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
if __name__ == "__main__":

    for filename in os.listdir(input_dir):
        input_path = os.path.join(input_dir, filename)
        base, ext = os.path.splitext(filename)
        output_filename = base + '_compressed' + ext
        output_path = os.path.join(output_dir, output_filename)

        if os.path.isfile(input_path):
            print(f"Processing file: {filename}")
            Encoder.encoder(input_path, output_path)

            reconstructed_filename = base + '_reconstructed' + ext
            reconstructed_path = os.path.join(reconstructed_dir, reconstructed_filename)
            Decoder.decoder(output_path, reconstructed_path)

            identical = files_are_equal(input_path, reconstructed_path)
            result = "SUCCESS" if identical else "FAILURE"
            print(f"Verification: {filename} -> {result}")
            print("-" * 40)

    print("\n=== All files processed ===\n")


