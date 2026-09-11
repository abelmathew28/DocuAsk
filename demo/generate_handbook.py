from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def build_handbook(path: Path) -> None:
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName="Times-Bold", fontSize=22, spaceAfter=18)
    heading = ParagraphStyle("HeadingCustom", parent=styles["Heading1"], fontName="Times-Bold", fontSize=14, spaceBefore=14, spaceAfter=8)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontName="Times-Roman", fontSize=11, leading=16, spaceAfter=8)

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch)
    story = []
    story.append(Paragraph("Northwind Labs", title))
    story.append(Paragraph("Employee Handbook — Demo Edition", heading))
    story.append(Paragraph(
        "This handbook is a public demo document created for DocuAsk. It is original sample content, not a real company policy set.",
        body,
    ))
    story.append(Paragraph("1. Welcome", heading))
    story.append(Paragraph(
        "Welcome to Northwind Labs. This handbook explains how we work, time off, remote work, and how to report an absence. "
        "If a topic is not covered here, ask your manager or email hr@northwindlabs.example.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("2. Employment classification", heading))
    story.append(Paragraph(
        "Full-time employees work at least 40 hours per week. Part-time employees work fewer than 30 hours per week. "
        "Paid time-off policies in this handbook apply to full-time employees unless a section says otherwise.",
        body,
    ))
    story.append(Paragraph("3. Work hours", heading))
    story.append(Paragraph(
        "Standard office hours are 9:00 a.m. to 5:30 p.m. local time, Monday through Friday. Teams may use flexible start times between 8:00 a.m. and 10:00 a.m. with manager approval.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("4. Vacation policy", heading))
    story.append(Paragraph(
        "Full-time employees receive 15 paid vacation days during their first year of employment. After three complete years of service, the annual vacation allotment increases to 20 paid days. "
        "Vacation is accrued monthly and should be requested at least two weeks in advance using the internal time-off form.",
        body,
    ))
    story.append(Paragraph(
        "Unused vacation may be carried over up to five days into the following calendar year. Vacation payout at departure follows applicable local law.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("5. Sick leave", heading))
    story.append(Paragraph(
        "Full-time employees receive 10 paid sick days each calendar year. Sick days may be used for personal illness, medical appointments, or to care for an immediate family member. "
        "Employees do not need to share a diagnosis. Unused sick days do not carry over.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("6. Remote work policy", heading))
    story.append(Paragraph(
        "Northwind Labs uses a hybrid schedule: three days in the office and two remote days each week. Fully remote work is available with written manager approval for roles that do not require on-site equipment. "
        "Remote employees must be available on Slack during core hours from 10:00 a.m. to 3:00 p.m. local time.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("7. Reporting an absence", heading))
    story.append(Paragraph(
        "If you cannot work, notify your manager and email hr@northwindlabs.example before 9:00 a.m. on the day of the absence. You may also send a Slack message to your manager if email is unavailable. "
        "Absences longer than three consecutive days require a brief note to HR confirming the expected return date.",
        body,
    ))
    story.append(PageBreak())
    story.append(Paragraph("8. Benefits snapshot", heading))
    story.append(Paragraph(
        "Eligible employees receive health insurance enrollment during the first 30 days of employment, a 401(k) match of up to 4 percent, and a $1,000 annual professional development stipend.",
        body,
    ))
    story.append(Paragraph("Suggested questions", heading))
    story.append(Paragraph("What is the vacation policy?", body))
    story.append(Paragraph("How many sick days are available?", body))
    story.append(Paragraph("What is the remote work policy?", body))
    story.append(Paragraph("How should employees report an absence?", body))
    doc.build(story)


if __name__ == "__main__":
    output = Path(__file__).resolve().parent / "employee-handbook-demo.pdf"
    build_handbook(output)
    print(f"Wrote {output}")
