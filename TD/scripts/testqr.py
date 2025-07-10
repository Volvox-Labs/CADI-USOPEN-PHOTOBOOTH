import qrcode
from PIL import Image

# Generate QR code
qr = qrcode.QRCode(
    version=1,  # Controls the size of the QR code
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
    box_size=10,  # Size of each box in the QR code grid
    border=4,  # Border size
)
qr.add_data("www.volvoxlabs.com")
qr.make(fit=True)

# Create QR code image
qr_img = qr.make_image(fill_color="black", back_color="white").resize((720, 720))  # Resize to 540x540
# qr_img = qr.make_image(fill_color="black", back_color="white")  # White foreground, transparent background

# Convert to RGBA mode for alpha transparency
qr_img = qr_img.convert("RGBA")

# Save or display the QR code
qr_img.save("volvoxlabs_qr.png")
qr_img.show()