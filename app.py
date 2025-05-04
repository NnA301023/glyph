import streamlit as st
from dotenv import load_dotenv
import traceback
from agents import create_workflow

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Article Generator",
    page_icon="📝",
    layout="wide"
)

# Initialize session state
if 'generated_article' not in st.session_state:
    st.session_state.generated_article = None

# Initialize workflow
workflow = create_workflow()

# Sidebar for input parameters
with st.sidebar:

    st.title("✍️ Article Generator")
    st.subheader("Parameter Configuration")
    
    # Content input
    content = st.text_area(
        "Brief Content",
        placeholder="Enter the main points or topic for the article...",
        height=150
    )
    
    # Tone selection
    tone = st.selectbox(
        "Tone of Article",
        options=["Professional", "Casual", "Academic", "Conversational", "Technical"]
    )
    
    # Length selection
    length = st.selectbox(
        "Article Length",
        options=[
            ("Short (500 words)", 500),
            ("Medium (1200 words)", 1200),
            ("Long (2500 words)", 2500)
        ],
        format_func=lambda x: x[0]
    )
    
    # Citation checkbox
    include_citations = st.checkbox("Include Citations from Internet")
    
    # Generate button
    generate_button = st.button("Generate Article", type="primary")

# Article preview area
if st.session_state.generated_article:

    # Parse the article due it has metadata article on beginning for SEO support.
    st.markdown(
        st.session_state.generated_article.split("---")[2].split("Internal Linking Suggestions")[0]
    )
    
    # Download button
    st.download_button(
        label="Download as Markdown",
        data=st.session_state.generated_article,
        file_name="generated_article.md",
        mime="text/markdown"
    )

# Handle generate button click
if generate_button and content:
    with st.spinner("Generating article..."):
        # Prepare input state
        input_state = {
            "content": content,
            "tone": tone,
            "length": length[1],
            "include_citations": include_citations
        }
        
        # Run the workflow
        try:
            result = workflow.invoke(input_state)
            st.session_state.generated_article = result["final_article"]
            st.rerun()
            
        except Exception as e:
            traceback.print_exc()
            st.error(f"An error occurred during article generation: {str(e)}")

elif generate_button and not content:
    st.error("Please enter some content to generate an article.")
