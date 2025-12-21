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

        identical = Decoder.files_are_equal(input_path, reconstructed_path)
        result = "SUCCESS" if identical else "FAILURE"
        print(f"Verification: {filename} -> {result}")
        print("-" * 40)

print("\n=== All files processed ===\n")