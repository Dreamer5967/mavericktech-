#!/usr/bin/env python3
"""
AEGIS Presentation Deck Generator
Generates an editable PowerPoint deck (AEGIS_Pitch_Deck.pptx)
strictly matching the 6-slide master specification.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path: str):
    prs = Presentation()
    # 16:9 widescreen layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Styling colors
    NAVY = RGBColor(11, 15, 25)
    LIGHT_BG = RGBColor(245, 247, 250)
    DARK_TEXT = RGBColor(15, 23, 42)
    MUTED_TEXT = RGBColor(100, 116, 139)
    ACCENT_BLUE = RGBColor(2, 132, 199)
    ACCENT_GREEN = RGBColor(22, 163, 74)
    ACCENT_RED = RGBColor(220, 38, 38)
    CARD_BG = RGBColor(255, 255, 255)
    BORDER_COLOR = RGBColor(226, 232, 240)

    slides_data = [
        {
            "slide_num": "01",
            "title": "When Vision Fails, Traffic Shouldn't Collapse",
            "subtitle": "The Problem — Perception Blackouts in Smart Traffic Systems",
            "points": [
                ("The Failure Mode", "Modern smart traffic controllers rely on edge cameras. When rain, glare, or camera dropouts occur, systems either blind-revert to rigid timers or dangerously treat missing cameras as '0 vehicles', starving congested approaches."),
                ("The AEGIS Approach", "Fuses PS1 (CARLA 0.9.15 + SUMO + YOLOv10n digital twin) and PS3 (Multimodal VQA + Security Firewall)."),
                ("Uncertainty Data Contract", "Missing data is strictly preserved as null with bounded belief intervals [lower, upper] — preventing catastrophic blind decisions."),
                ("Emergency Green Corridor (AEGIS-EVC)", "Predictive preemption flushes queues ahead of ambulances, delivering zero-stop waves while protecting cross-traffic safety."),
            ],
            "footer": "AEGIS · Smart Technologies PS1 & PS3 · Team Build 2026"
        },
        {
            "slide_num": "02",
            "title": "Three Isolated Planes, One Verified Clock Owner",
            "subtitle": "Architecture & Strict Privilege Boundaries",
            "points": [
                ("Control Plane (CARLA + SUMO)", "Synchronized micro-traffic simulation in Town10HD_Opt across 4 signalized junctions (cam_g1=719, cam_g3=23, cam_g4=189, cam_g5=468). Single clock owner advances time at 0.05s steps."),
                ("Safety Phase Guard (Amal)", "Strictly enforces minimum green (10.0s), maximum green timeout (60.0s), and mandatory clearance sequences [NS_YELLOW -> ALL_RED -> Target]. Rejects stale state revisions."),
                ("Operator & VQA Plane", "Mission Control dashboard for operators. External VQA and query endpoints possess ZERO actuation privileges."),
                ("Security Firewall (Amal)", "Screens every prompt against 6 adversarial patterns (direct override, jailbreak, unauthorized actuation). 100% defense rate on benchmark fixtures."),
            ],
            "footer": "AEGIS Architecture · Commit 25d3530 & PR #3 Verified"
        },
        {
            "slide_num": "03",
            "title": "Real-Time Adaptation Under Sensor Loss & Zero-Stop Waves",
            "subtitle": "Interactive Live Demonstration & Emergency Corridor",
            "points": [
                ("Arterial Corridor Setup", "4 synchronized intersections along arterial Town10HD_Opt with live camera feeds and telemetry."),
                ("Interactive Trigger 1 — Camera Dropout", "Judges select any junction camera to drop (e.g. J2). System immediately records null count and expands uncertainty bounds [3.5, 7.5]. Safe clearance sequence verified before any transition."),
                ("Interactive Trigger 2 — Emergency Corridor (EVC)", "Dispatch Priority 1 Ambulance (AMB-101). Real-time V2X predictive queue flushing clears approaches 15 seconds ahead of arrival."),
                ("Zero-Stop Wave + MAPPO Recovery", "Ambulance traverses all 4 junctions without stopping. Intersections automatically return to balanced signal control upon vehicle exit."),
            ],
            "footer": "Interactive Mission Control · starter/web/index.html · Port 8000"
        },
        {
            "slide_num": "04",
            "title": "Measured Telemetry Across Seeded Demand",
            "subtitle": "Quantitative Verification — Bridge & Perception Metrics",
            "points": [
                ("Controlled Seed Demand", "Demand seed 42: 12 passenger routes, 48 scheduled vehicles. Seed splits: Train [1..5], Dev [6..7], Test [8..10] reserved for benchmarks."),
                ("Simulation Hardware", "Vast.ai NVIDIA RTX 3090 Ti. 30s co-simulation bridge run (SUMO finished at 29.95s, up to 14 mirrored CARLA vehicle actors)."),
                ("Perception Performance", "4 angled cameras on YOLOv10n; frame latency 0.13–0.25s (median 0.15–0.20s). Max inter-camera skew 0.094s. Decoded JPEGs at 960x540."),
                ("Honest Engineering Limitation", "Fixed-time synchronization with camera perception is fully validated. Lane queue counting and live learned-policy MARL control remain unverified pending compatible Town10 checkpoint."),
            ],
            "footer": "Evidence: cosim-smoke/test-20261112T081204Z-6199.jsonl & p2-smoke"
        },
        {
            "slide_num": "05",
            "title": "100% Defense on Adversarial Injection & Strict RBAC",
            "subtitle": "Security Benchmark — Prompt Injection & Firewall Defense",
            "points": [
                ("Adversarial Benchmark Suite", "11 offline test fixtures evaluating direct overrides, instruction bypasses, persona jailbreaks, and unauthorized actuation commands (evaluation/prompt_injection.csv)."),
                ("Benchmark Results", "Attack Defense Rate: 6/6 blocked (100.0%). False Alarm Rate: 0/5 benign blocked (0.0%). Security Accuracy: 100.0% (11/11)."),
                ("Role-Based Access Control (RBAC)", "Operator role required for state changes with valid secret. VQA reader and viewer roles return PERMISSION_DENIED on actuation attempts."),
                ("Media Header Sanitization", "5MB file cap and binary magic number verification for PNG (\\x89PNG) and JPEG (\\xff\\xd8\\xff)."),
            ],
            "footer": "Benchmark: evaluation/prompt_injection.csv · tests/test_firewall.py (16/16 Passed)"
        },
        {
            "slide_num": "06",
            "title": "Transparent Verification, Cloud Budget & Team Handoff",
            "subtitle": "Engineering Scope, Limitations & Production Roadmap",
            "points": [
                ("Verified Deliverables", "Synchronous co-simulation bridge, 4-camera YOLOv10n pipeline, Safety Phase Guard (12/12 test cases), Security Firewall (16/16 tests), and AEGIS-EVC Emergency Corridor."),
                ("Budget Compliance ($5.00 Grant)", "Total Spend: $1.66 ($1.35 compute + $0.18 storage + $0.13 transfer). Remaining Reserve: $3.34 intact (66.8% under budget, zero overrun)."),
                ("Declared Limitations", "Live MARL policy control gated until Town10 checkpoint and 24-lane mapping alignment are resolved. Production deployment requires physical induction loop validation."),
                ("Presentation Team Choreography", "P1 (Amal): Architecture, Phase Guard, Security, EVC · P4: Operator Dashboard, Speech, VQA · P2: Cloud runtime, Co-sim, Perception."),
            ],
            "footer": "Budget Log: manifests/cost_log.csv · Balance $3.34 · Zero Overrun"
        }
    ]

    for data in slides_data:
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

        # Background shape
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = LIGHT_BG
        bg.line.fill.background()

        # Top Banner / Header Accent
        header_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
        header_bar.fill.solid()
        header_bar.fill.fore_color.rgb = ACCENT_BLUE
        header_bar.line.fill.background()

        # Slide Number Badge
        num_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(1.5), Inches(0.4))
        tf_num = num_box.text_frame
        tf_num.word_wrap = True
        p_num = tf_num.paragraphs[0]
        p_num.text = f"SLIDE {data['slide_num']} / 06"
        p_num.font.size = Pt(11)
        p_num.font.bold = True
        p_num.font.color.rgb = ACCENT_BLUE

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.9), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = data["title"]
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_TEXT

        # Slide Subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(11.5), Inches(0.5))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = data["subtitle"]
        p_sub.font.size = Pt(14)
        p_sub.font.bold = True
        p_sub.font.color.rgb = ACCENT_BLUE

        # 4 Content Cards (2x2 grid)
        card_w = Inches(5.6)
        card_h = Inches(1.9)
        coords = [
            (Inches(0.8), Inches(2.3)),
            (Inches(6.8), Inches(2.3)),
            (Inches(0.8), Inches(4.5)),
            (Inches(6.8), Inches(4.5)),
        ]

        for idx, (point_title, point_desc) in enumerate(data["points"]):
            cx, cy = coords[idx]
            # Card background
            card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, card_w, card_h)
            card.fill.solid()
            card.fill.fore_color.rgb = CARD_BG
            card.line.color.rgb = BORDER_COLOR
            card.line.width = Pt(1)

            # Card text
            cbox = slide.shapes.add_textbox(cx + Inches(0.25), cy + Inches(0.2), card_w - Inches(0.5), card_h - Inches(0.4))
            ctf = cbox.text_frame
            ctf.word_wrap = True
            
            cp1 = ctf.paragraphs[0]
            cp1.text = point_title
            cp1.font.size = Pt(13)
            cp1.font.bold = True
            cp1.font.color.rgb = DARK_TEXT
            cp1.space_after = Pt(4)

            cp2 = ctf.add_paragraph()
            cp2.text = point_desc
            cp2.font.size = Pt(11)
            cp2.font.color.rgb = MUTED_TEXT

        # Footer
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.5), Inches(0.4))
        ftf = footer_box.text_frame
        fp = ftf.paragraphs[0]
        fp.text = data["footer"]
        fp.font.size = Pt(10)
        fp.font.color.rgb = MUTED_TEXT

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs.save(output_path)
    print(f"✅ Editable PowerPoint presentation saved to: {output_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AEGIS_Pitch_Deck.pptx")
    create_deck(out)
