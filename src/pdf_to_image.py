from pdf2image import convert_from_path
from PIL import Image
import os


def pdf_to_images(pdf_path, output_folder=None, dpi=200, fmt='PNG'):
    """
    Convert PDF to images

    Parameters:
    -----------
    pdf_path : str
        Path to the PDF file
    output_folder : str, optional
        Output folder for images (if not specified, saves in same folder as PDF)
    dpi : int, optional
        Image resolution (default: 200)
    fmt : str, optional
        Image format such as 'PNG', 'JPEG' (default: 'PNG')

    Returns:
    --------
    list
        List of paths to created images
    """
    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Set output folder
    if output_folder is None:
        output_folder = os.path.dirname(pdf_path)

    # Create folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Convert PDF to images
    print(f"Converting PDF: {pdf_path}")
    images = convert_from_path(pdf_path, dpi=dpi)

    # Save images
    saved_paths = []
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    for i, image in enumerate(images, start=1):
        image_path = os.path.join(output_folder, f"{pdf_name}_page_{i}.{fmt.lower()}")
        image.save(image_path, fmt)
        saved_paths.append(image_path)
        print(f"Saved page {i}/{len(images)}: {image_path}")

    print(f"Conversion complete! Total {len(images)} pages")
    return saved_paths


def pdf_to_single_image(pdf_path, output_path=None, dpi=200, orientation='vertical'):
    """
    Convert multi-page PDF to a single image (combine all pages)

    Parameters:
    -----------
    pdf_path : str
        Path to the PDF file
    output_path : str, optional
        Path for output image
    dpi : int, optional
        Image resolution (default: 200)
    orientation : str, optional
        Image orientation 'vertical' or 'horizontal' (default: 'vertical')

    Returns:
    --------
    str
        Path to created image
    """
    # Check if PDF file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Convert PDF to images
    print(f"Converting PDF: {pdf_path}")
    images = convert_from_path(pdf_path, dpi=dpi)

    # Calculate size of combined image
    if orientation == 'vertical':
        total_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
    else:  # horizontal
        total_width = sum(img.width for img in images)
        total_height = max(img.height for img in images)

    # Create new image
    combined_image = Image.new('RGB', (total_width, total_height), 'white')

    # Paste each page
    current_pos = 0
    for img in images:
        if orientation == 'vertical':
            # Place centered horizontally
            x_offset = (total_width - img.width) // 2
            combined_image.paste(img, (x_offset, current_pos))
            current_pos += img.height
        else:  # horizontal
            # Place centered vertically
            y_offset = (total_height - img.height) // 2
            combined_image.paste(img, (current_pos, y_offset))
            current_pos += img.width

    # Set output path
    if output_path is None:
        pdf_name = os.path.splitext(pdf_path)[0]
        output_path = f"{pdf_name}_combined.png"

    # Save image
    combined_image.save(output_path)
    print(f"Saved combined image: {output_path}")

    return output_path


# Usage examples
if __name__ == "__main__":
    # Example 1: Convert PDF to separate page images
    # pdf_path = "example.pdf"
    # images = pdf_to_images(pdf_path, output_folder="output", dpi=300)

    # Example 2: Convert PDF to single combined image
    # pdf_path = "example.pdf"
    # combined = pdf_to_single_image(pdf_path, output_path="combined.png", orientation='vertical')

    pass
