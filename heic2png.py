from PIL import Image
import pillow_heif
import os


def convert_heic_to_png(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".heic"):
            heic_path = os.path.join(input_folder, filename)
            png_path = os.path.join(output_folder, filename.replace(".heic", ".png"))

            heif_file = pillow_heif.read_heif(heic_path)
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data
            )
            image.save(png_path, "PNG")
            print(f"Převedeno: {filename} → {png_path}")


# Příklad použití
convert_heic_to_png(r"C:\Users\patrikbrejla\BOBCAT_FastAPI\HEIC2PNG\input", r"C:\Users\patrikbrejla\BOBCAT_FastAPI\HEIC2PNG\output")
