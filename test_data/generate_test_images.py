"""Generate test images: 3 scanned documents + 5 teardown component photos."""
import os
from PIL import Image, ImageDraw, ImageFont
import random
import math

BASE = os.path.dirname(os.path.abspath(__file__))
SCANNED_DIR = os.path.join(BASE, "scanned")
TEARDOWN_DIR = os.path.join(BASE, "teardown")
os.makedirs(SCANNED_DIR, exist_ok=True)
os.makedirs(TEARDOWN_DIR, exist_ok=True)

def get_font(size=20):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
        except:
            return ImageFont.load_default()

# ─── SCANNED DOCUMENT 1: Clean signed memo ───
def create_signed_memo():
    img = Image.new("RGB", (850, 1100), "#f5f5f0")
    draw = ImageDraw.Draw(img)
    font_title = get_font(28)
    font_body = get_font(16)
    font_small = get_font(12)

    # Header
    draw.rectangle([40, 40, 810, 120], fill="#1a3a5c")
    draw.text((60, 55), "NEXUS AUTOMOTIVE GROUP", fill="white", font=font_title)
    draw.text((60, 90), "Internal Memorandum", fill="#cccccc", font=font_small)

    y = 150
    lines = [
        "MEMORANDUM",
        "",
        "TO:      All Department Heads",
        "FROM:    Michael Torres, CEO",
        "DATE:    June 15, 2025",
        "RE:      Data Handling Policy — Mandatory Compliance",
        "",
        "─" * 55,
        "",
        "This memo confirms the adoption of the updated Data Handling",
        "Policy (DHP v3.2) effective July 1, 2025. All personnel involved",
        "in the Cost Optimization & Sustainability Integration Program",
        "(COSIP) must comply with the following requirements:",
        "",
        "1. DOCUMENT SANITIZATION: All scanned documents uploaded to the",
        "   analytics platform must undergo PII removal before ingestion.",
        "   The approved sanitization approach uses automated redaction",
        "   with manual review for documents classified as CONFIDENTIAL.",
        "",
        "2. DATA RETENTION: Project documents are retained for 7 years.",
        "   Financial records follow SOX compliance (minimum 7 years).",
        "   Tear-down photos are retained for the product lifecycle.",
        "",
        "3. ACCESS CONTROL: Role-based access with quarterly reviews.",
        "   Engineering data: Engineering + PM teams only.",
        "   Financial data: Finance + Executive leadership only.",
        "   Sustainability data: All COSIP stakeholders.",
        "",
        "4. THIRD-PARTY SHARING: Sustainability benchmark data may be",
        "   shared with Kearney PERLab under existing NDA (signed March",
        "   2025). No other external sharing without Legal approval.",
        "",
        "Non-compliance will be addressed through the standard",
        "disciplinary process outlined in the Employee Handbook.",
        "",
        "Please acknowledge receipt by signing below and returning to",
        "the Office of the CEO by June 30, 2025.",
        "",
        "",
        "________________________________",
        "Michael Torres, CEO",
        "Nexus Automotive Group",
        "",
        "Acknowledged: ___[Signed: Sarah Chen, June 18, 2025]___",
    ]
    for line in lines:
        draw.text((60, y), line, fill="#1a1a1a", font=font_body)
        y += 22

    img.save(os.path.join(SCANNED_DIR, "signed_memo_data_policy.png"))
    print("Created: signed_memo_data_policy.png")

# ─── SCANNED DOCUMENT 2: Skewed whiteboard capture ───
def create_whiteboard():
    img = Image.new("RGB", (900, 700), "#e8e4d8")
    draw = ImageDraw.Draw(img)
    font = get_font(18)
    font_small = get_font(14)
    font_title = get_font(24)

    # Whiteboard frame
    draw.rectangle([20, 20, 880, 680], outline="#888888", width=3)

    # Title
    draw.text((60, 40), "SPRINT 8 - BLOCKER ANALYSIS", fill="#2222aa", font=font_title)
    draw.text((60, 75), "Whiteboard capture — Aug 15, 2025", fill="#666666", font=font_small)

    # Draw some "handwritten" content
    blockers = [
        ("R-042: HSLA Weld Validation", 120, "#cc0000"),
        ("  → Blocks: Production approval for seat track", 148, "#333333"),
        ("  → Owner: Raj Patel", 172, "#333333"),
        ("  → ETA: Aug 30, 2025", 196, "#333333"),
        ("", 220, "#333333"),
        ("R-043: SteelCraft Pricing", 240, "#cc8800"),
        ("  → Blocks: Q1 2026 supply contract", 268, "#333333"),
        ("  → Owner: David Park", 292, "#333333"),
        ("  → Dependency: Audit result (Sep 10)", 316, "#333333"),
        ("", 340, "#333333"),
        ("R-044: Spring Test Equipment", 360, "#cc8800"),
        ("  → Blocks: Wire spring material decision", 388, "#333333"),
        ("  → Owner: Tom Bradley", 412, "#333333"),
        ("  → Workaround: External lab (quote pending)", 436, "#333333"),
        ("", 460, "#333333"),
        ("R-046: Greenville Plant Capacity", 480, "#cc0000"),
        ("  → Blocks: New stamping press installation", 508, "#333333"),
        ("  → Owner: Maria Santos", 532, "#333333"),
        ("  → Mitigation: Phased install (2 weekends)", 556, "#333333"),
    ]
    for text, y_pos, color in blockers:
        draw.text((60, y_pos), text, fill=color, font=font)

    # Draw some arrows and boxes to simulate whiteboard
    draw.rectangle([600, 120, 860, 200], outline="#cc0000", width=2)
    draw.text((620, 135), "CRITICAL PATH:", fill="#cc0000", font=font_small)
    draw.text((620, 158), "R-042 → R-046", fill="#cc0000", font=font)
    draw.line([(530, 160), (600, 160)], fill="#cc0000", width=2)

    draw.rectangle([600, 240, 860, 310], outline="#00aa00", width=2)
    draw.text((620, 255), "ON TRACK:", fill="#00aa00", font=font_small)
    draw.text((620, 278), "R-045 (Sust. Report)", fill="#00aa00", font=font)

    # Apply slight rotation to simulate skew
    img = img.rotate(-2.5, expand=True, fillcolor="#d0ccc0")

    img.save(os.path.join(SCANNED_DIR, "whiteboard_sprint8_blockers.png"))
    print("Created: whiteboard_sprint8_blockers.png")

# ─── SCANNED DOCUMENT 3: Noisy vendor matrix table ───
def create_vendor_matrix():
    img = Image.new("RGB", (1000, 750), "#f0efe8")
    draw = ImageDraw.Draw(img)
    font = get_font(14)
    font_title = get_font(20)
    font_header = get_font(13)

    # Add some noise/speckle
    random.seed(42)
    for _ in range(800):
        x, y = random.randint(0, 999), random.randint(0, 749)
        c = random.randint(180, 220)
        draw.point((x, y), fill=(c, c, c))

    draw.text((50, 30), "VENDOR COMPARISON MATRIX — Seat Component Suppliers", fill="#111111", font=font_title)
    draw.text((50, 60), "Prepared by: David Park | Date: August 10, 2025 | CONFIDENTIAL", fill="#555555", font=font_header)

    # Table
    headers = ["Vendor", "Components", "Material", "Cost/Unit", "Lead Time", "Quality", "Emissions", "Score"]
    col_widths = [130, 120, 100, 80, 80, 70, 90, 60]
    x_start = 50
    y_start = 100
    row_height = 35

    # Draw header
    x = x_start
    draw.rectangle([x_start-5, y_start-5, x_start+sum(col_widths)+5, y_start+row_height], fill="#2c3e50")
    for i, h in enumerate(headers):
        draw.text((x+5, y_start+8), h, fill="white", font=font_header)
        x += col_widths[i]

    # Table data
    rows = [
        ["TierOne Mfg", "Seat Track,\nSlide Rail", "CR1020,\nHSLA340", "$15.50-\n$17.50", "4 weeks", "98.2%", "3.25-2.80\nkg CO2e", "92"],
        ["SteelCraft Ind.", "Seat Track,\nFrame,\nRecliner", "CR1020,\nHSLA340,\nTubular", "$14.80-\n$19.00", "3 weeks", "96.5%", "3.10-2.90\nkg CO2e", "88"],
        ["MetalWorks Co.", "Frame,\nWire Spring", "CR1020,\nSpring Wire", "$16.00-\n$18.50", "5 weeks", "94.1%", "3.50-1.90\nkg CO2e", "79"],
        ["AutoParts Ltd", "Recliner,\nSlide Rail", "CR1020,\nAluminum", "$15.00-\n$28.00", "6 weeks", "95.8%", "3.80-4.10\nkg CO2e", "74"],
        ["PrecisionSteel", "All Types", "All Types", "$16.50-\n$30.00", "4 weeks", "97.0%", "3.40-4.00\nkg CO2e", "82"],
    ]

    for r_idx, row in enumerate(rows):
        y = y_start + (r_idx + 1) * row_height + 10
        x = x_start
        bg = "#ffffff" if r_idx % 2 == 0 else "#f0f0e8"
        draw.rectangle([x_start-5, y-5, x_start+sum(col_widths)+5, y+row_height+15], fill=bg)
        for c_idx, cell in enumerate(row):
            lines = cell.split("\n")
            for li, line in enumerate(lines):
                draw.text((x+5, y+li*16), line, fill="#1a1a1a", font=font_header)
            x += col_widths[c_idx]
        # Draw row line
        draw.line([(x_start-5, y+row_height+15), (x_start+sum(col_widths)+5, y+row_height+15)], fill="#cccccc")

    # Summary at bottom
    summary_y = y_start + 7 * row_height + 30
    draw.text((50, summary_y), "RECOMMENDATION:", fill="#cc0000", font=font_title)
    draw.text((50, summary_y + 30), "Primary: TierOne Manufacturing (Score: 92) — Best quality + emissions profile", fill="#1a1a1a", font=font)
    draw.text((50, summary_y + 55), "Secondary: SteelCraft Industries (Score: 88) — Broadest component range, competitive pricing", fill="#1a1a1a", font=font)
    draw.text((50, summary_y + 80), "Note: MetalWorks and AutoParts removed from consideration for seat track (quality < 95% threshold)", fill="#555555", font=font_header)

    # Add more noise for realism
    for _ in range(500):
        x, y = random.randint(0, 999), random.randint(0, 749)
        c = random.randint(160, 200)
        draw.point((x, y), fill=(c, c, c))

    img.save(os.path.join(SCANNED_DIR, "vendor_matrix_scan.png"))
    print("Created: vendor_matrix_scan.png")

# ─── TEARDOWN PHOTOS (5 component images) ───
def create_component_photo(filename, component_name, component_details, color_scheme):
    img = Image.new("RGB", (800, 600), color_scheme["bg"])
    draw = ImageDraw.Draw(img)
    font = get_font(16)
    font_small = get_font(12)

    # Simulate a workshop/lab background
    random.seed(hash(filename))
    for _ in range(200):
        x, y = random.randint(0, 799), random.randint(0, 599)
        c = tuple(max(0, min(255, v + random.randint(-20, 20))) for v in color_scheme["bg_rgb"])
        draw.point((x, y), fill=c)

    # Draw component shape
    cx, cy = 400, 280
    shape_fn = component_details["shape_fn"]
    shape_fn(draw, cx, cy, color_scheme)

    # Add measurement ruler at bottom
    draw.rectangle([50, 530, 750, 545], fill="#333333")
    for i in range(15):
        x = 50 + i * 50
        h = 15 if i % 5 == 0 else 8
        draw.line([(x, 530-h), (x, 530)], fill="#cccccc", width=1)
        if i % 5 == 0:
            draw.text((x-5, 548), f"{i*2}cm", fill="#888888", font=font_small)

    # Add scale reference card (white card in corner)
    draw.rectangle([620, 20, 780, 80], fill="white", outline="#333333")
    draw.text((635, 30), "NEXUS AUTO", fill="#333333", font=font_small)
    draw.text((635, 48), f"TD-{random.randint(1000,9999)}", fill="#666666", font=font_small)

    # Add some workshop surface texture
    for _ in range(100):
        x1 = random.randint(0, 799)
        y1 = random.randint(0, 599)
        draw.line([(x1, y1), (x1+random.randint(1,5), y1+random.randint(1,3))], fill=color_scheme["scratch"], width=1)

    img.save(os.path.join(TEARDOWN_DIR, filename))
    print(f"Created: {filename}")

def draw_seat_track(draw, cx, cy, cs):
    # Two parallel rails with cross-members
    draw.rectangle([cx-250, cy-30, cx+250, cy-10], fill=cs["metal"], outline=cs["edge"], width=2)
    draw.rectangle([cx-250, cy+10, cx+250, cy+30], fill=cs["metal"], outline=cs["edge"], width=2)
    # Cross members
    for i in range(-200, 201, 80):
        draw.rectangle([cx+i-8, cy-30, cx+i+8, cy+30], fill=cs["metal_dark"], outline=cs["edge"])
    # Mounting holes
    for x_off in [-220, -100, 100, 220]:
        draw.ellipse([cx+x_off-8, cy-25, cx+x_off+8, cy-15], fill=cs["hole"])
        draw.ellipse([cx+x_off-8, cy+15, cx+x_off+8, cy+25], fill=cs["hole"])
    # Locking tab
    draw.polygon([(cx+260, cy-20), (cx+290, cy), (cx+260, cy+20)], fill=cs["metal_dark"], outline=cs["edge"])

def draw_slide_rail(draw, cx, cy, cs):
    # Single rail with ball bearing track
    draw.rectangle([cx-200, cy-15, cx+200, cy+15], fill=cs["metal"], outline=cs["edge"], width=2)
    # Ball bearing groove
    draw.rectangle([cx-190, cy-5, cx+190, cy+5], fill=cs["metal_dark"])
    # Ball bearings
    for i in range(-180, 181, 30):
        draw.ellipse([cx+i-6, cy-6, cx+i+6, cy+6], fill="#888888", outline="#666666")
    # End caps
    draw.rectangle([cx-210, cy-20, cx-195, cy+20], fill=cs["metal_dark"], outline=cs["edge"], width=2)
    draw.rectangle([cx+195, cy-20, cx+210, cy+20], fill=cs["metal_dark"], outline=cs["edge"], width=2)

def draw_seat_frame(draw, cx, cy, cs):
    # U-shaped frame
    draw.rectangle([cx-180, cy-120, cx-160, cy+120], fill=cs["metal"], outline=cs["edge"], width=2)
    draw.rectangle([cx+160, cy-120, cx+180, cy+120], fill=cs["metal"], outline=cs["edge"], width=2)
    draw.rectangle([cx-180, cy+100, cx+180, cy+120], fill=cs["metal"], outline=cs["edge"], width=2)
    # Cross brace
    draw.line([(cx-160, cy-80), (cx+160, cy+80)], fill=cs["metal_dark"], width=4)
    draw.line([(cx-160, cy+80), (cx+160, cy-80)], fill=cs["metal_dark"], width=4)
    # Mounting tabs
    for x_off in [-180, 180]:
        for y_off in [-100, 100]:
            draw.rectangle([cx+x_off-15, cy+y_off-10, cx+x_off+15, cy+y_off+10], fill=cs["metal_dark"], outline=cs["edge"])
            draw.ellipse([cx+x_off-5, cy+y_off-5, cx+x_off+5, cy+y_off+5], fill=cs["hole"])

def draw_recliner(draw, cx, cy, cs):
    # Gear mechanism
    draw.ellipse([cx-80, cy-80, cx+80, cy+80], fill=cs["metal"], outline=cs["edge"], width=3)
    draw.ellipse([cx-50, cy-50, cx+50, cy+50], fill=cs["metal_dark"], outline=cs["edge"], width=2)
    draw.ellipse([cx-15, cy-15, cx+15, cy+15], fill=cs["hole"])
    # Gear teeth
    for angle in range(0, 360, 20):
        rad = math.radians(angle)
        x1 = cx + int(75 * math.cos(rad))
        y1 = cy + int(75 * math.sin(rad))
        x2 = cx + int(90 * math.cos(rad))
        y2 = cy + int(90 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=cs["edge"], width=3)
    # Lever arm
    draw.rectangle([cx+80, cy-12, cx+220, cy+12], fill=cs["metal"], outline=cs["edge"], width=2)
    draw.ellipse([cx+210, cy-15, cx+240, cy+15], fill=cs["metal_dark"], outline=cs["edge"])

def draw_wire_spring(draw, cx, cy, cs):
    # Serpentine spring pattern
    points = []
    for i in range(0, 400, 4):
        x = cx - 200 + i
        y = cy + int(40 * math.sin(i * 0.08))
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=cs["metal"], width=4)
    # Second spring
    points2 = []
    for i in range(0, 400, 4):
        x = cx - 200 + i
        y = cy + 60 + int(40 * math.sin(i * 0.08 + 1.5))
        points2.append((x, y))
    if len(points2) > 1:
        draw.line(points2, fill=cs["metal"], width=4)
    # Attachment clips at ends
    for x_off in [-210, 200]:
        draw.rectangle([cx+x_off-10, cy-10, cx+x_off+10, cy+70], fill=cs["metal_dark"], outline=cs["edge"], width=2)

# Color schemes for different "lighting" conditions
schemes = [
    {"bg": "#3a3632", "bg_rgb": (58,54,50), "metal": "#b0b0b0", "metal_dark": "#808080", "edge": "#505050", "hole": "#2a2a2a", "scratch": "#4a4642"},
    {"bg": "#4a4540", "bg_rgb": (74,69,64), "metal": "#c0c0c0", "metal_dark": "#909090", "edge": "#606060", "hole": "#303030", "scratch": "#5a5550"},
    {"bg": "#353030", "bg_rgb": (53,48,48), "metal": "#a8a8a8", "metal_dark": "#787878", "edge": "#484848", "hole": "#222222", "scratch": "#454040"},
    {"bg": "#3d3a35", "bg_rgb": (61,58,53), "metal": "#b8b8b0", "metal_dark": "#888880", "edge": "#585850", "hole": "#282828", "scratch": "#4d4a45"},
    {"bg": "#423e3a", "bg_rgb": (66,62,58), "metal": "#a0a098", "metal_dark": "#707068", "edge": "#404038", "hole": "#252525", "scratch": "#524e4a"},
]

components = [
    ("teardown_seat_track.jpg", "Seat Track Assembly", {"shape_fn": draw_seat_track}),
    ("teardown_slide_rail.jpg", "Slide Rail Mechanism", {"shape_fn": draw_slide_rail}),
    ("teardown_seat_frame.jpg", "Seat Frame Structure", {"shape_fn": draw_seat_frame}),
    ("teardown_recliner.jpg", "Recliner Mechanism", {"shape_fn": draw_recliner}),
    ("teardown_wire_spring.jpg", "Wire Spring Support", {"shape_fn": draw_wire_spring}),
]

if __name__ == "__main__":
    print("Generating scanned documents...")
    create_signed_memo()
    create_whiteboard()
    create_vendor_matrix()

    print("\nGenerating teardown component photos...")
    for i, (fname, name, details) in enumerate(components):
        create_component_photo(fname, name, details, schemes[i])

    print("\nAll test data generated!")
