import subprocess
import os
import fitz

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
HTML_PATH = r"file:///D:/VPN_APP/poster/index_exact.html"
RAW_PDF = r"D:\VPN_APP\poster\raw_render.pdf"

print("1. Rendering HTML via Edge headless...")
cmd = [
    EDGE_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={RAW_PDF}",
    HTML_PATH
]
subprocess.run(cmd, check=True)
print("Raw PDF rendered!")

# Now process with PyMuPDF
doc_raw = fitz.open(RAW_PDF)
page_raw = doc_raw[0]
print(f"Rendered dimensions: {page_raw.rect.width} x {page_raw.rect.height} pt")

# 1. QuantumSafeVPN_Poster_Upright.pdf (Standard Upright Landscape: 841.92 x 595.32 pt)
doc_upright = fitz.open()
page_u = doc_upright.new_page(width=841.92, height=595.32)
page_u.show_pdf_page(page_u.rect, doc_raw, 0)
doc_upright.save(r"D:\VPN_APP\poster\QuantumSafeVPN_Poster_Upright.pdf")
doc_upright.save(r"D:\VPN_APP\QuantumSafeVPN_Poster_Upright.pdf")
print("Saved QuantumSafeVPN_Poster_Upright.pdf!")

# 2. QuantumSafeVPN_Poster_Exact.pdf (Exact match to friend: 595.32 x 841.92 pt Portrait, rotated sideways)
# In the friend's PDF, page is width=595.32, height=841.92.
# The landscape content is rotated 270 degrees (or 90 counter-clockwise) so that the bottom of the landscape is along the left.
doc_exact = fitz.open()
page_e = doc_exact.new_page(width=595.32, height=841.92)
# We can place the raw page with rotate=90 or rotate=270
# Let's check rotation: in friend's page, Red Card is at the bottom-left (y=615 to 809, x=82 to 380).
# In raw_render (landscape), Red Card is at (x=33 to 227, y=82 to 380).
# When rotated 90 degrees counter-clockwise (270 clockwise):
# Old x -> New y from bottom; Old y -> New x.
# PyMuPDF show_pdf_page supports rotate parameter!
# rotate=90: clockwise 90. rotate=270: clockwise 270.
# Let's use rotate=270 (90 counter-clockwise)
# Let's test target rect
page_e.show_pdf_page(page_e.rect, doc_raw, 0, rotate=270)
doc_exact.save(r"D:\VPN_APP\poster\QuantumSafeVPN_Poster_Exact.pdf")
doc_exact.save(r"D:\VPN_APP\QuantumSafeVPN_Poster_Exact.pdf")
print("Saved QuantumSafeVPN_Poster_Exact.pdf!")

# 3. QuantumSafeVPN_Poster_A3.pdf (Full A3 Landscape: 1190.55 x 841.92 pt = 420 x 297 mm)
doc_a3 = fitz.open()
page_a3 = doc_a3.new_page(width=1190.55, height=841.92)
page_a3.show_pdf_page(page_a3.rect, doc_raw, 0)
doc_a3.save(r"D:\VPN_APP\poster\QuantumSafeVPN_Poster_A3.pdf")
doc_a3.save(r"D:\VPN_APP\QuantumSafeVPN_Poster_A3.pdf")
print("Saved QuantumSafeVPN_Poster_A3.pdf!")

# Render PNG previews at high resolution (150 DPI and 300 DPI)
pix_exact = doc_exact[0].get_pixmap(dpi=150)
pix_exact.save(r"D:\VPN_APP\poster\QuantumSafeVPN_Poster_Exact.png")
pix_exact.save(r"D:\VPN_APP\QuantumSafeVPN_Poster_Exact.png")

pix_upright = doc_upright[0].get_pixmap(dpi=150)
pix_upright.save(r"D:\VPN_APP\poster\QuantumSafeVPN_Poster_Upright.png")
pix_upright.save(r"D:\VPN_APP\QuantumSafeVPN_Poster_Upright.png")

print("All posters built successfully!")
