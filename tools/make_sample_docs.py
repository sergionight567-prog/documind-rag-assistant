"""Generate three realistic sample PDFs for a fictional company (Solvane Energy) used to demo the assistant."""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

F = '/usr/share/fonts/truetype/google-fonts/ofl/firasans/'
pdfmetrics.registerFont(TTFont('Fira', F + 'FiraSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Fira-Md', F + 'FiraSans-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Fira-SB', F + 'FiraSans-SemiBold.ttf'))
pdfmetrics.registerFont(TTFont('Fira-B', F + 'FiraSans-Bold.ttf'))

INK = colors.HexColor('#16202E')
MUTED = colors.HexColor('#5B6676')
ACC = colors.HexColor('#E8892B')
LINE = colors.HexColor('#D9DEE5')
TINT = colors.HexColor('#F4F6F9')
body = ParagraphStyle('b', fontName='Fira', fontSize=10.2, leading=15, textColor=INK, spaceAfter=7)
h1 = ParagraphStyle('h1', fontName='Fira-B', fontSize=15, leading=19, textColor=INK, spaceBefore=12, spaceAfter=8)
h2 = ParagraphStyle('h2', fontName='Fira-SB', fontSize=11.5, leading=15, textColor=INK, spaceBefore=8, spaceAfter=4)
bul = ParagraphStyle('bul', parent=body, leftIndent=12, bulletIndent=2, spaceAfter=4)
cell = ParagraphStyle('c', fontName='Fira', fontSize=9.2, leading=12.5, textColor=INK)
cellh = ParagraphStyle('ch', fontName='Fira-SB', fontSize=9.2, leading=12.5, textColor=colors.white)
note = ParagraphStyle('n', parent=body, fontSize=9.4, textColor=MUTED, leading=13.5)


def build(path, title, subtitle, doc_id, story):
    def deco(c, d):
        c.saveState()
        c.setFillColor(INK)
        c.rect(0, A4[1] - 16 * mm, A4[0], 16 * mm, fill=1, stroke=0)
        c.setFillColor(ACC)
        c.rect(0, A4[1] - 16.8 * mm, A4[0], 0.8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Fira-B', 11)
        c.drawString(18 * mm, A4[1] - 10 * mm, 'SOLVANE')
        c.setFont('Fira', 8.5)
        c.drawString(39 * mm, A4[1] - 10 * mm, 'ENERGY')
        c.setFont('Fira', 8.5)
        c.drawRightString(A4[0] - 18 * mm, A4[1] - 10 * mm, title)
        c.setFillColor(MUTED)
        c.setFont('Fira', 8)
        c.drawString(
            18 * mm,
            10 * mm,
            f'{doc_id}  ·  Sample document for demonstration purposes. Solvane Energy is a fictional company.',
        )
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, f'Page {d.page}')
        c.restoreState()

    doc = BaseDocTemplate(
        path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
        title=title,
        author='Solvane Energy (fictional)',
    )
    doc.addPageTemplates(
        [PageTemplate(frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='f')], onPage=deco)]
    )
    head = [
        Spacer(1, 6 * mm),
        Paragraph(title, ParagraphStyle('t', fontName='Fira-B', fontSize=24, leading=29, textColor=INK)),
        Paragraph(
            subtitle,
            ParagraphStyle(
                's', fontName='Fira', fontSize=11.5, leading=16, textColor=MUTED, spaceBefore=4, spaceAfter=10
            ),
        ),
    ]
    doc.build(head + story)


def P(t, s=body):
    return Paragraph(t, s)


def B(items):
    return [Paragraph(i, bul, bulletText='•') for i in items]


def T(rows, widths):
    data = [[Paragraph(str(x), cellh if r == 0 else cell) for x in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), INK),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TINT]),
                ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [t, Spacer(1, 4 * mm)]


# ---------------------------------------------------------------------------------------------- handbook
def handbook(path):
    s = []
    s += [
        P('1. Welcome', h1),
        P(
            'This handbook explains how we work at Solvane Energy: our hours, time off, expenses, equipment, '
            'benefits and the rules that keep our people and our customers safe. It applies to all full-time and part-time employees '
            'from 1 January 2026. Where local law gives you more, local law wins. Questions go to People Operations at '
            'people@solvane.example or #ask-people in Slack.'
        ),
    ]
    s += [
        P('2. Working hours and remote work', h1),
        P(
            'Our standard week is 40 hours for full-time employees. We use <b>core hours from 10:00 to 15:00</b> in your local time zone; '
            'outside core hours you organise your day with your team. Customer Support and Field Service follow the shift plans '
            'published by their managers.'
        ),
        P('Hybrid work', h2),
        P(
            'Office-based roles may work remotely <b>up to 3 days per week</b>. Teams agree on one shared "anchor day" in the office. '
            'Fully remote work is possible for roles marked "remote-eligible" in the job description, with written approval from your '
            'manager and People Operations. Working from another country for more than <b>20 working days per calendar year</b> needs '
            'prior approval because of tax and insurance rules.'
        ),
        P('Overtime', h2),
        P(
            'Overtime must be agreed with your manager in advance. Hourly employees are paid 1.5x for hours above 40 per week. '
            'Salaried employees may take time off in lieu (TOIL) within 60 days.'
        ),
    ]
    s += [P('3. Paid time off', h1)]
    s += T(
        [
            ['Type', 'Allowance', 'Notes'],
            [
                'Annual leave (PTO)',
                '25 working days per year',
                'Accrues 2.08 days per month. Up to 5 unused days carry over and must be used by 31 March.',
            ],
            [
                'Public holidays',
                'According to your work location',
                'If you work on a public holiday you get a replacement day.',
            ],
            ['Sick leave', '10 paid days per year', "A doctor's note is needed from the 4th consecutive day."],
            ['Parental leave (primary carer)', '16 weeks at full pay', 'Available after 6 months of employment.'],
            [
                'Parental leave (secondary carer)',
                '6 weeks at full pay',
                'Can be taken in up to 3 blocks within the first year.',
            ],
            ['Bereavement', '5 days (close family), 2 days (other)', 'No documents required.'],
            ['Volunteering', '2 days per year', 'For registered charities; agree dates with your manager.'],
        ],
        [42, 45, 87],
    )
    s += [
        P(
            'Request leave in the HR portal (PeoplePoint) at least <b>2 weeks in advance</b> for absences longer than 3 days. '
            'Managers respond within 3 working days. Leave of more than 10 consecutive working days in December needs approval from '
            'your department head.'
        )
    ]
    s += [
        P('4. Travel and expenses', h1),
        P(
            'Book travel through our travel desk (travel@solvane.example) whenever possible. Economy class is standard for flights under '
            '6 hours; premium economy is allowed for longer flights. Train travel in second class is preferred for trips under 4 hours.'
        ),
    ]
    s += T(
        [
            ['Expense', 'Limit', 'Rule'],
            [
                'Hotel, tier-1 cities (London, Paris, New York, Munich, Zurich)',
                'up to $220 per night',
                'Book via the travel desk.',
            ],
            ['Hotel, other cities', 'up to $160 per night', ''],
            [
                'Meals while travelling',
                'up to $60 per day',
                'Alcohol is not reimbursed except at approved client dinners.',
            ],
            [
                'Client entertainment',
                'up to $90 per person',
                'Pre-approval from your manager needed above $400 in total.',
            ],
            ['Taxi / ride share', 'actual cost', 'Only when public transport is not practical or after 21:00.'],
            ['Personal car', '$0.62 per mile ($0.39 per km)', 'Log the trip in Expensa with start and end address.'],
        ],
        [62, 38, 74],
    )
    s += [
        P(
            'Submit expenses in <b>Expensa within 30 days</b> of the expense. Receipts are required for every item above $25. '
            'Approved expenses are paid with the next payroll run. Expenses submitted after 90 days are not reimbursed.'
        )
    ]
    s += [
        P('5. Equipment and home office', h1),
        *B(
            [
                'Every employee gets a laptop; it is refreshed every <b>3 years</b> or earlier if it fails.',
                'Remote and hybrid employees receive a one-time <b>$500 home office stipend</b> and <b>$40 per month</b> towards internet costs.',
                'Lost or stolen equipment must be reported to IT within 24 hours via it-help@solvane.example.',
                'Personal devices may be used for email and Slack only if enrolled in our device management (Intune).',
            ]
        ),
    ]
    s += [
        P('6. Learning and development', h1),
        P(
            'Each employee has a <b>learning budget of $1,500 per calendar year</b> for courses, books, conferences and certifications. '
            'Unused budget does not carry over. Certifications that the company requires for your role (for example electrical '
            'installer licences) are paid in full and do not count against the budget. You also get 3 learning days per year.'
        ),
    ]
    s += [
        P('7. Performance and pay', h1),
        P(
            'We run performance reviews <b>twice a year, in March and September</b>. Salary reviews happen once a year, effective 1 April. '
            'Promotions can be proposed at either review. New employees have a probation period of 6 months with a check-in after '
            '3 months.'
        ),
    ]
    s += [
        P('8. Benefits', h1),
        *B(
            [
                'Health, dental and vision insurance from day one; the company pays 90% of the employee premium and 70% for dependants.',
                'Retirement plan: the company matches <b>100% of contributions up to 4%</b> of base salary, vested immediately.',
                'Life insurance at 2x annual base salary.',
                'Employee discount of 25% on Solvane products for you and your immediate family.',
                'Wellbeing allowance of $50 per month (gym, sports clubs, mental-health apps).',
            ]
        ),
    ]
    s += [
        P('9. IT security', h1),
        *B(
            [
                'Multi-factor authentication (MFA) is mandatory on all company accounts.',
                'Use the company password manager (1Password). Never reuse passwords.',
                'Report suspected phishing with the "Report" button in Outlook or to security@solvane.example. Never forward it to colleagues.',
                'Customer data may only be stored in approved systems (Salesforce, Zendesk, the Solvane cloud). No customer data on USB drives.',
                'Lock your screen when you leave your desk. Laptops lock automatically after 5 minutes.',
            ]
        ),
    ]
    s += [
        P('10. Code of conduct', h1),
        P(
            'We expect respectful, honest behaviour towards colleagues, customers and partners. Harassment and discrimination are not '
            'tolerated. Gifts from suppliers above $75 in value must be declined or reported to Legal. Concerns can be raised '
            'anonymously through the Speak Up line (speakup.solvane.example), which is run by an independent provider.'
        ),
        P('Last updated: January 2026. Owner: People Operations.', note),
    ]
    build(
        path,
        'Employee Handbook 2026',
        'How we work at Solvane Energy: hours, leave, expenses, equipment, benefits and security.',
        'SOL-HR-001',
        s,
    )


# ---------------------------------------------------------------------------------------------- manual
def manual(path):
    s = []
    s += [
        P('1. About the SV-10', h1),
        P(
            'The Solvane SV-10 is a wall- or floor-mounted home battery that stores energy from rooftop solar '
            'or the grid and powers your home during the evening, at night and during power cuts. It uses lithium iron phosphate (LFP) '
            'cells, which are among the safest battery chemistries available for homes.'
        ),
    ]
    s += [P('2. Technical specifications', h1)]
    s += T(
        [
            ['Parameter', 'Value'],
            ['Usable capacity', '10.2 kWh (10.8 kWh nominal)'],
            ['Continuous power (charge/discharge)', '5.0 kW'],
            ['Peak power', '7.6 kW for 10 seconds'],
            ['Round-trip efficiency', '91%'],
            ['Cell chemistry', 'Lithium iron phosphate (LFP)'],
            ['Cycle life', '6,000 cycles to 80% capacity'],
            ['Dimensions (H x W x D)', '1150 x 740 x 190 mm'],
            ['Weight', '112 kg'],
            ['Protection rating', 'IP55 (indoor and sheltered outdoor installation)'],
            ['Operating temperature', '-10 °C to 50 °C (charging from 0 °C to 45 °C)'],
            ['Noise', 'Below 30 dB(A) at 1 m'],
            ['Communication', 'Wi-Fi 2.4 GHz, Ethernet, RS485'],
            ['Backup switchover time', 'under 20 ms (with the Solvane Gateway G2)'],
            ['Warranty', '10 years (see Support & Warranty Policy)'],
        ],
        [70, 104],
    )
    s += [
        P('3. Installation requirements', h1),
        P(
            'The SV-10 must be installed by a Solvane-certified installer. Installation by anyone else voids the warranty.'
        ),
        *B(
            [
                'Mount on a solid wall or on the floor stand (FS-1). The wall must carry at least 4 times the battery weight.',
                'Keep at least <b>30 cm of clearance on each side</b> and 50 cm above the unit for airflow.',
                'Do not install in direct sunlight, in living or sleeping rooms, or in locations where water can collect.',
                'Up to <b>2 units can be stacked</b> on the floor stand (20.4 kWh usable). Up to <b>4 units can run in parallel</b> '
                '(40.8 kWh usable) with one Gateway G2.',
                'Ambient temperature at the installation site should stay between 5 °C and 30 °C for the longest battery life.',
            ]
        ),
        P('4. Setting up the Solvane Home app', h1),
        *B(
            [
                'Download the Solvane Home app (iOS 16+ or Android 11+).',
                'Create an account and scan the QR code on the right side of the battery.',
                'Connect the battery to Wi-Fi. <b>Only 2.4 GHz networks are supported</b>; 5 GHz networks will not appear in the list.',
                'Choose an operating mode (see section 5). The default mode is Self-consumption with a 20% backup reserve.',
                'Firmware updates install automatically between 02:00 and 04:00 local time.',
            ]
        ),
    ]
    s += [P('5. Operating modes', h1)]
    s += T(
        [
            ['Mode', 'What it does', 'Best for'],
            [
                'Self-consumption (default)',
                'Stores surplus solar energy during the day and uses it in the evening to minimise grid import.',
                'Homes with rooftop solar and flat tariffs.',
            ],
            [
                'Time-of-use',
                'Charges when electricity is cheap (for example at night) and discharges during peak-price hours you set in the app.',
                'Homes on dynamic or time-of-use tariffs.',
            ],
            [
                'Backup only',
                'Keeps the battery full and only discharges during a power cut.',
                'Areas with frequent outages.',
            ],
        ],
        [38, 88, 48],
    )
    s += [
        P(
            'The <b>backup reserve</b> is the share of capacity that is always kept for power cuts. The default is <b>20%</b>; you can set '
            'it anywhere from 0% to 100% in Settings > Backup reserve. During a power cut the battery can power essential loads '
            'connected to the backup circuit for roughly 8 to 12 hours at a typical load of 800 W.'
        )
    ]
    s += [P('6. LED status indicator', h1)]
    s += T(
        [
            ['LED', 'Meaning'],
            ['Solid green', 'Normal operation.'],
            ['Breathing green', 'Charging.'],
            ['Breathing blue', 'Discharging.'],
            ['Solid blue', 'Backup mode active (grid outage).'],
            ['Flashing yellow', 'Warning: check the app for details. The system keeps running.'],
            ['Solid red', 'Fault: the battery has stopped. See error codes below.'],
            ['Off', 'Battery switched off or in deep sleep.'],
        ],
        [45, 129],
    )
    s += [P('7. Error codes', h1)]
    s += T(
        [
            ['Code', 'Meaning', 'What to do'],
            [
                'E01',
                'Cell over-temperature (above 55 °C)',
                'The battery pauses until it cools down. Check clearance and ventilation. If it repeats, contact support.',
            ],
            [
                'E02',
                'Cell under-temperature (below -10 °C)',
                'Charging is blocked until the temperature rises. Consider moving the unit to a warmer location.',
            ],
            [
                'E03',
                'Over-voltage on the DC bus',
                'Restart the system (section 8). If it persists, a technician visit is needed.',
            ],
            ['E04', 'Communication lost with the Gateway', 'Check the RS485 cable and that the Gateway is powered on.'],
            [
                'E05',
                'Wi-Fi disconnected for more than 24 hours',
                'Reconnect in the app. Remember that only 2.4 GHz Wi-Fi is supported.',
            ],
            [
                'E06',
                'Insulation fault detected',
                '<b>Do not touch the unit.</b> Switch it off at the isolator and call support immediately.',
            ],
            [
                'E07',
                'Firmware update failed',
                'The battery keeps working on the old firmware. The update will retry the next night.',
            ],
            ['E08', 'Fan fault', 'The battery limits power to 2.5 kW. Contact support to arrange a replacement fan.'],
            [
                'E09',
                'Cell imbalance',
                'The battery runs a balancing cycle automatically (up to 12 hours). No action needed unless it lasts longer than 48 hours.',
            ],
            [
                'E10',
                'Grid frequency out of range',
                'Usually caused by the grid. The battery reconnects automatically after 5 minutes.',
            ],
            [
                'E11',
                'Ground fault',
                '<b>Do not touch the unit.</b> Switch off at the isolator and call support immediately.',
            ],
            [
                'E12',
                'Internal self-test failed',
                'Restart the system. If the code returns, contact support with the serial number.',
            ],
        ],
        [14, 52, 108],
    )
    s += [
        P('8. Restarting the system', h1),
        *B(
            [
                'Switch off the AC isolator next to the battery.',
                'Press and hold the power button for 5 seconds until the LED turns off.',
                'Wait 60 seconds.',
                'Switch the AC isolator back on and press the power button once. The LED turns solid green within 2 minutes.',
            ]
        ),
    ]
    s += [
        P('9. Maintenance', h1),
        P(
            'The SV-10 does not need routine maintenance. Wipe the cover with a dry cloth if it gets dusty and keep the air vents clear. '
            'Do not use water jets or solvents. The battery runs a self-check every 30 days and reports the result in the app.'
        ),
    ]
    s += [
        P('10. Safety', h1),
        *B(
            [
                'Never open the battery enclosure. There are no user-serviceable parts inside.',
                'In case of fire, use a CO2 or dry powder extinguisher and call emergency services. Do not use water on a burning battery.',
                'Keep children and pets away from the installation area.',
            ]
        ),
    ]
    s += [
        P('11. Frequently asked questions', h1),
        P('Can I install the SV-10 myself?', h2),
        P('No. Installation must be done by a Solvane-certified installer, otherwise the warranty is void.'),
        P('Does the SV-10 work without solar panels?', h2),
        P('Yes. In Time-of-use mode it charges from the grid when prices are low.'),
        P('Can I add a second battery later?', h2),
        P('Yes. You can add units at any time, up to 4 in parallel, as long as they run the same firmware generation.'),
        P('Manual version 3.2, February 2026.', note),
    ]
    build(
        path,
        'SV-10 Home Battery Manual',
        'Installation requirements, app setup, operating modes, LED codes, error codes and safety.',
        'SOL-SV10-MAN-3.2',
        s,
    )


# ---------------------------------------------------------------------------------------------- policy
def policy(path):
    s = []
    s += [
        P('1. Contacting support', h1),
        P(
            'Our support team is available by phone (+1 555 0142 300), chat in the Solvane Home app and email '
            '(support@solvane.example).'
        ),
    ]
    s += T(
        [
            ['Channel', 'Hours (CET)'],
            ['Phone and chat', 'Monday to Friday 08:00-20:00, Saturday 09:00-14:00'],
            ['Email', 'Answered within 1 business day'],
            ['Emergency line (E06 / E11 faults, smoke, fire risk)', '24/7, +1 555 0142 911'],
        ],
        [80, 94],
    )
    s += [P('2. Service levels', h1)]
    s += T(
        [
            ['Priority', 'Example', 'First response', 'Resolution target'],
            [
                'Critical',
                'System offline, safety fault (E06, E11)',
                'within 4 hours',
                'technician on site within 2 business days',
            ],
            ['High', 'Reduced power (E08), backup not working', 'within 8 business hours', 'within 5 business days'],
            ['Standard', 'App questions, settings, billing', 'within 1 business day', 'within 10 business days'],
        ],
        [24, 60, 36, 54],
    )
    s += [
        P('3. Returns', h1),
        *B(
            [
                'Accessories (cables, floor stand FS-1, wall brackets) can be returned within <b>30 days</b> if unopened and unused.',
                'An SV-10 battery can be returned within <b>14 days of delivery</b> only if it has <b>not been installed</b>. '
                'A restocking fee of <b>15%</b> applies to opened batteries.',
                'Installed batteries cannot be returned, but are covered by the warranty below.',
                'Return shipping is free for faulty items. For change-of-mind returns the customer pays shipping (typically $95 for a battery).',
            ]
        ),
    ]
    s += [
        P('4. Refunds', h1),
        P(
            'Refunds are issued to the original payment method within <b>5 to 10 business days</b> after the returned '
            'item passes inspection at our warehouse. Installation fees are refundable only if the installation has not started.'
        ),
    ]
    s += [
        P('5. Warranty', h1),
        P(
            'The SV-10 is covered for <b>10 years from the installation date or 37.8 MWh of energy throughput, whichever comes first</b>. '
            'During this period we guarantee that the battery keeps at least <b>70% of its usable capacity</b>. The Gateway G2 and '
            'accessories have a 5-year warranty. Repairs or replacement units do not extend the original warranty period.'
        ),
        P('What is not covered', h2),
        *B(
            [
                'Installation by someone who is not Solvane-certified.',
                'Damage from flooding, fire, lightning or other force majeure.',
                'Operation outside the specified temperature range or with blocked ventilation.',
                'Cosmetic damage that does not affect performance.',
                'Units whose serial number label has been removed or altered.',
            ]
        ),
    ]
    s += [
        P('6. How to make a warranty claim', h1),
        *B(
            [
                'Open the Solvane Home app and go to Support > Warranty claim, or email support@solvane.example.',
                'Provide the serial number (on the QR label), the installation date and the error code or a description of the problem.',
                'Our team runs remote diagnostics within 2 business days.',
                'If a repair is needed, a certified technician visits; parts, labour and travel are free under warranty.',
                'If the unit cannot be repaired, we replace it with a new or refurbished unit of equal or better capacity.',
            ]
        ),
    ]
    s += [
        P('7. Shipping', h1),
        P(
            'Standard delivery of a battery takes 5 to 7 business days within the continental US and EU, by freight '
            'carrier with a 2-hour delivery window. Express delivery (2 to 3 business days) costs $149. We do not ship batteries to P.O. boxes.'
        ),
    ]
    s += [
        P('8. Escalation', h1),
        P(
            'If you are not happy with how your case was handled, ask for escalation. A team lead will contact you '
            'within 2 business days. You can also write to our Customer Experience Manager at cx@solvane.example. We aim to close every '
            'escalated case within 15 business days.'
        ),
        P('Policy version 2026-01. Applies to purchases made from 1 January 2026.', note),
    ]
    build(
        path,
        'Customer Support & Warranty Policy',
        'Support hours, service levels, returns, refunds, warranty terms and claims.',
        'SOL-CS-POL-2026',
        s,
    )


if __name__ == '__main__':
    out = os.path.join(os.path.dirname(__file__), '..', 'sample_docs')
    os.makedirs(out, exist_ok=True)
    handbook(os.path.join(out, 'Solvane_Employee_Handbook_2026.pdf'))
    manual(os.path.join(out, 'Solvane_SV-10_Battery_Manual.pdf'))
    policy(os.path.join(out, 'Solvane_Support_and_Warranty_Policy.pdf'))
    print('ok')
