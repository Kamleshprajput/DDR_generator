"""
DDR Report Generator - Streamlit Application
Main entry point for the application.
"""
import streamlit as st
import io
import json
from pdf_extractor import PDFExtractor, ExtractedImage
from gemini_client import GeminiClient
from report_parser import parse_report, DDRReport
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .severity-critical {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: 2px solid #dc2626;
        font-weight: bold;
        display: inline-block;
    }
    .severity-high {
        background-color: #fed7aa;
        color: #9a3412;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: 2px solid #ea580c;
        font-weight: bold;
        display: inline-block;
    }
    .severity-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: 2px solid #f59e0b;
        font-weight: bold;
        display: inline-block;
    }
    .severity-low {
        background-color: #d1fae5;
        color: #065f46;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: 2px solid #10b981;
        font-weight: bold;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)


def get_severity_class(level: str) -> str:
    """Get CSS class for severity level."""
    level_lower = level.lower()
    if level_lower == 'critical':
        return 'severity-critical'
    elif level_lower == 'high':
        return 'severity-high'
    elif level_lower == 'medium':
        return 'severity-medium'
    elif level_lower == 'low':
        return 'severity-low'
    return ''


def create_pdf_report(report: DDRReport, thermal_images: list) -> bytes:
    """Create a PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        spaceBefore=20,
    )
    
    # Title
    story.append(Paragraph("Detailed Diagnostic Report (DDR)", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Property Summary
    story.append(Paragraph("Property Summary", heading_style))
    ps = report.property_summary
    summary_text = f"""
    <b>Property Type:</b> {ps.get('property_type', 'Not Available')}<br/>
    <b>Floors:</b> {ps.get('floors', 'Not Available')}<br/>
    <b>Inspection Date:</b> {ps.get('inspection_date', 'Not Available')}<br/>
    <b>Inspected By:</b> {ps.get('inspected_by', 'Not Available')}<br/>
    <b>Customer Name:</b> {ps.get('customer_name', 'Not Available')}<br/>
    <b>Address:</b> {ps.get('address', 'Not Available')}<br/>
    <b>Previous Audit:</b> {ps.get('previous_audit', 'Not Available')}<br/>
    <b>Previous Repair:</b> {ps.get('previous_repair', 'Not Available')}<br/>
    <b>Overall Score:</b> {ps.get('overall_score', 'Not Available')}<br/>
    <b>Overview:</b> {ps.get('overview', 'Not Available')}
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Severity
    story.append(Paragraph("Severity Assessment", heading_style))
    severity = report.severity
    severity_text = f"<b>{severity.get('level', 'Unknown')}</b><br/>{severity.get('reasoning', '')}"
    story.append(Paragraph(severity_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Area Observations
    story.append(Paragraph("Area Observations", heading_style))
    for obs in report.area_observations:
        obs_text = f"""
        <b>{obs.get('area', 'Unknown Area')}</b><br/>
        <b>Negative Side (Interior):</b> {obs.get('negative_side', 'Not Available')}<br/>
        <b>Positive Side (Exterior):</b> {obs.get('positive_side', 'Not Available')}<br/>
        <b>Thermal Data:</b> {obs.get('thermal_data', 'Not Available')}<br/>
        """
        story.append(Paragraph(obs_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Root Causes
    story.append(Paragraph("Root Causes", heading_style))
    if isinstance(report.root_causes, list) and len(report.root_causes) > 0:
        for cause in report.root_causes:
            story.append(Paragraph(f"• {cause}", styles['Normal']))
    else:
        root_causes_text = report.root_causes if isinstance(report.root_causes, str) else "Not Available"
        story.append(Paragraph(root_causes_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Recommended Actions
    story.append(Paragraph("Recommended Actions", heading_style))
    if isinstance(report.recommended_actions, list) and len(report.recommended_actions) > 0:
        for action in report.recommended_actions:
            story.append(Paragraph(f"• {action}", styles['Normal']))
    else:
        recommended_text = report.recommended_actions if isinstance(report.recommended_actions, str) else "Not Available"
        story.append(Paragraph(recommended_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Additional Notes
    if report.additional_notes != 'Not Available':
        story.append(Paragraph("Additional Notes", heading_style))
        story.append(Paragraph(report.additional_notes, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Missing Information
    if report.missing_information and isinstance(report.missing_information, list) and len(report.missing_information) > 0:
        story.append(Paragraph("Missing Information", heading_style))
        for item in report.missing_information:
            story.append(Paragraph(f"• {item}", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def display_report(report: DDRReport, thermal_images: list):
    """Display the DDR report in Streamlit."""
    st.markdown("## Detailed Diagnostic Report (DDR)")
    st.markdown(f"*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    
    # Property Summary
    st.markdown("### Property Summary")
    ps = report.property_summary
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Property Type:** {ps.get('property_type', 'Not Available')}")
        st.write(f"**Floors:** {ps.get('floors', 'Not Available')}")
        st.write(f"**Inspection Date:** {ps.get('inspection_date', 'Not Available')}")
        st.write(f"**Inspected By:** {ps.get('inspected_by', 'Not Available')}")
        st.write(f"**Customer Name:** {ps.get('customer_name', 'Not Available')}")
    with col2:
        st.write(f"**Address:** {ps.get('address', 'Not Available')}")
        st.write(f"**Previous Audit:** {ps.get('previous_audit', 'Not Available')}")
        st.write(f"**Previous Repair:** {ps.get('previous_repair', 'Not Available')}")
        st.write(f"**Overall Score:** {ps.get('overall_score', 'Not Available')}")
    
    st.write(f"**Overview:** {ps.get('overview', 'Not Available')}")
    st.divider()
    
    # Severity
    st.markdown("### Severity Assessment")
    severity = report.severity
    level = severity.get('level', 'Unknown')
    severity_class = get_severity_class(level)
    st.markdown(f'<div class="{severity_class}">{level}</div>', unsafe_allow_html=True)
    st.write(severity.get('reasoning', ''))
    st.divider()
    
    # Area Observations
    st.markdown("### Area Observations")
    for obs in report.area_observations:
        with st.expander(f"📍 {obs.get('area', 'Unknown Area')}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Negative Side (Interior):**")
                st.write(obs.get('negative_side', 'Not Available'))
            with col2:
                st.write(f"**Positive Side (Exterior):**")
                st.write(obs.get('positive_side', 'Not Available'))
            
            st.write(f"**Thermal Data:** {obs.get('thermal_data', 'Not Available')}")
            
            # Display thermal image if available
            page_num = obs.get('thermal_image_page')
            if page_num:
                matching_image = next(
                    (img for img in thermal_images if img.page_num == page_num),
                    None
                )
                if matching_image:
                    st.write(f"**Thermal Image (Page {page_num}):**")
                    img_data = base64.b64decode(matching_image.base64_data)
                    st.image(img_data, use_container_width=True)
    st.divider()
    
    # Root Causes
    st.markdown("### Root Causes")
    if isinstance(report.root_causes, list) and len(report.root_causes) > 0:
        for cause in report.root_causes:
            st.write(f"• {cause}")
    else:
        st.write(report.root_causes if isinstance(report.root_causes, str) else "Not Available")
    st.divider()
    
    # Recommended Actions
    st.markdown("### Recommended Actions")
    if isinstance(report.recommended_actions, list) and len(report.recommended_actions) > 0:
        for action in report.recommended_actions:
            st.write(f"• {action}")
    else:
        st.write(report.recommended_actions if isinstance(report.recommended_actions, str) else "Not Available")
    st.divider()
    
    # Additional Notes
    if report.additional_notes != 'Not Available':
        st.markdown("### Additional Notes")
        st.write(report.additional_notes)
        st.divider()
    
    # Missing Information
    if report.missing_information and isinstance(report.missing_information, list) and len(report.missing_information) > 0:
        st.markdown("### Missing Information")
        for item in report.missing_information:
            st.write(f"• {item}")
        st.divider()
    
    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        # PDF Export
        pdf_bytes = create_pdf_report(report, thermal_images)
        st.download_button(
            label="📥 Export as PDF",
            data=pdf_bytes,
            file_name=f"DDR_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
    with col2:
        # JSON Export
        json_str = json.dumps(report.to_dict(), indent=2)
        st.download_button(
            label="📋 Copy JSON",
            data=json_str,
            file_name=f"DDR_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )


def main():
    """Main application function."""
    # Header
    st.markdown('<div class="main-header"><h1>📋 DDR Report Generator</h1></div>', unsafe_allow_html=True)
    st.markdown("Upload Inspection and Thermal Image Reports to generate a Detailed Diagnostic Report")
    st.divider()
    
    # Initialize session state
    if 'report' not in st.session_state:
        st.session_state.report = None
    if 'thermal_images' not in st.session_state:
        st.session_state.thermal_images = []
    
    # File upload section
    if st.session_state.report is None:
        st.markdown("### Upload PDF Documents")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Inspection Report")
            inspection_file = st.file_uploader(
                "Upload Inspection Report PDF",
                type=['pdf'],
                key='inspection',
                help="Upload the main inspection report PDF"
            )
        
        with col2:
            st.markdown("#### Thermal Images Report")
            thermal_file = st.file_uploader(
                "Upload Thermal Images Report PDF",
                type=['pdf'],
                key='thermal',
                help="Upload the thermal images report PDF"
            )
        
        # Generate button
        if st.button("🚀 Generate Report", type="primary", use_container_width=True):
            if not inspection_file or not thermal_file:
                st.error("Please upload both PDF files to generate the report.")
                return
            
            # Check file sizes (20MB limit)
            max_size = 20 * 1024 * 1024  # 20MB
            if inspection_file.size > max_size or thermal_file.size > max_size:
                st.error("File size must be less than 20MB. Please upload smaller files.")
                return
            
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Extract PDFs
                status_text.text("📄 Extracting text and images from PDFs...")
                progress_bar.progress(20)
                
                extractor = PDFExtractor()
                inspection_text, inspection_images = extractor.extract_all(inspection_file)
                thermal_text, thermal_images = extractor.extract_all(thermal_file)
                
                # Store images for later use
                st.session_state.thermal_images = thermal_images
                
                # Step 2: Send to Gemini
                status_text.text("🤖 Analyzing documents with Gemini AI...")
                progress_bar.progress(50)
                
                # Get API key
                api_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, 'secrets') else None
                if not api_key:
                    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
                
                if not api_key:
                    st.error("Please provide a Gemini API key. You can enter it in the sidebar or set it as a secret.")
                    return
                
                # Read file bytes for Gemini
                inspection_file.seek(0)
                thermal_file.seek(0)
                inspection_bytes = inspection_file.read()
                thermal_bytes = thermal_file.read()
                
                # Generate report
                gemini_client = GeminiClient(api_key=api_key)
                response_text = gemini_client.generate_report(
                    inspection_bytes,
                    thermal_bytes,
                    inspection_text,
                    thermal_text
                )
                
                # Step 3: Parse response
                status_text.text("📊 Parsing report...")
                progress_bar.progress(80)
                
                report = parse_report(response_text)
                st.session_state.report = report
                
                # Step 4: Complete
                progress_bar.progress(100)
                status_text.text("✅ Report generated successfully!")
                st.success("Report generated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")
                st.exception(e)
                progress_bar.empty()
                status_text.empty()
    
    else:
        # Display report
        display_report(st.session_state.report, st.session_state.thermal_images)
        
        # Reset button
        if st.button("🔄 Upload New Reports", use_container_width=True):
            st.session_state.report = None
            st.session_state.thermal_images = []
            st.rerun()


if __name__ == "__main__":
    main()

