import fitz

pdf_path = r"C:\Users\sanjaay krishna\.gemini\antigravity-ide\brain\60c4a4dd-c588-4cac-90cb-604e04a2f3d0\.user_uploaded\media_1791949743581.pdf"
doc = fitz.open(pdf_path)
page = doc[0]

print("Page MediaBox:", page.mediabox)
print("Page Rect:", page.rect)

# Inspect background cards
cards = []
for d in page.get_drawings():
    r = d["rect"]
    # Look for cards with border or fill
    if r.width > 50 and r.height > 50:
        fill = d.get("fill")
        color = d.get("color")
        cards.append((r, fill, color))

print(f"Found {len(cards)} large drawing rects:")
for r, fill, color in cards:
    print(f"Rect: x0={r.x0:.1f}, y0={r.y0:.1f}, x1={r.x1:.1f}, y1={r.y1:.1f}, w={r.width:.1f}, h={r.height:.1f}, fill={fill}")
