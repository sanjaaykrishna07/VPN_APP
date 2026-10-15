import fitz
import os

pdf_path = r"C:\Users\sanjaay krishna\.gemini\antigravity-ide\brain\60c4a4dd-c588-4cac-90cb-604e04a2f3d0\.user_uploaded\media_1791949743581.pdf"
doc = fitz.open(pdf_path)
print("Page count:", len(doc))
page = doc[0]
print("Page rect:", page.rect)
print("Width:", page.rect.width, "Height:", page.rect.height)
print("Width mm:", page.rect.width * 25.4 / 72, "Height mm:", page.rect.height * 25.4 / 72)
print("Rotation:", page.rotation)

# Render high-res image of page 0
pix = page.get_pixmap(dpi=300)
pix.save(r"d:\VPN_APP\poster\original_friend_page.png")
print("Saved original_friend_page.png at 300 DPI:", pix.width, "x", pix.height)

# Check images embedded
img_list = page.get_images(full=True)
print("Images count:", len(img_list))
for i, img in enumerate(img_list):
    xref = img[0]
    base_img = doc.extract_image(xref)
    ext = base_img["ext"]
    w = base_img["width"]
    h = base_img["height"]
    print(f"Img {i}: xref={xref}, ext={ext}, size={w}x{h}")
    # save extracted image
    with open(rf"d:\VPN_APP\poster\extracted_img_{i}.{ext}", "wb") as f:
        f.write(base_img["image"])

# Check text and vector graphics
text = page.get_text()
print("Text length:", len(text))
