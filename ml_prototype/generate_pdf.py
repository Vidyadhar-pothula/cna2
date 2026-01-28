from reportlab.pdfgen import canvas

def create_dummy_pdf(filename):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Control Narrative Document")
    c.drawString(100, 700, "Equipment: SUSV")
    c.drawString(100, 680, "Parameter: Flow Rate")
    c.drawString(100, 660, "Tolerance: P-101")
    c.save()

if __name__ == "__main__":
    create_dummy_pdf("sample_document.pdf")
    print("Created sample_document.pdf")
