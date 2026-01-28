from reportlab.pdfgen import canvas
import os

def create_pdf(filename, title, content_lines):
    c = canvas.Canvas(filename)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, title)
    
    c.setFont("Helvetica", 12)
    y = 700
    for line in content_lines:
        c.drawString(50, y, line)
        y -= 20
    
    c.save()
    print(f"Created: {filename}")

def main():
    # Sample 1: SUSV (The original scenario)
    create_pdf("sample_1_susv.pdf", "Control Narrative: SUSV Operation", [
        "Equipment: SUSV-110",
        "Parameter: Incoming Flow Rate (FT-201.IN)",
        "Parameter: Outgoing Flow Rate (FT-201.OUT)",
        "Variable: Weight Change Rate (V-110.dWT)",
        "Condition: IF deviation > Tolerance (P-TOL)",
        "Action: Trigger Alarm (V-110.Alarm_Deviation)"
    ])

    # Sample 2: Pump Control (Different equipment)
    create_pdf("sample_2_pump.pdf", "Control Narrative: Feed Pump Logic", [
        "Equipment: Pump P-501",
        "Parameter: Discharge Pressure (PT-501)",
        "Parameter: Motor Current (IT-501)",
        "Variable: Vibration Level (VT-501)",
        "Condition: IF Vibration > High Limit (P-VIB_HIGH)",
        "Action: Trip Pump (P-501.Trip)"
    ])

    # Sample 3: Tank Level (Another scenario)
    create_pdf("sample_3_tank.pdf", "Control Narrative: Storage Tank Level", [
        "Equipment: Tank T-300",
        "Parameter: Liquid Level (LT-300)",
        "Parameter: Temperature (TT-300)",
        "Condition: IF Level > 90% (P-L_HIGH)",
        "Action: Close Inlet Valve (XV-301.Close)",
        "Action: Sound High Level Alarm (L-ALM-HIGH)"
    ])

if __name__ == "__main__":
    main()
