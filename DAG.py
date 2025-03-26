import streamlit as st
# Configure the page - this must be the first st command
st.set_page_config(
    page_title="Diegetic Artefact Generator",
    page_icon="🏛️",
    layout="wide"
)

import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
import re
import logging
import random
import pathlib

# Load CSS
def load_css():
    # Load main styles
    css_file = pathlib.Path(__file__).parent / "static" / "styles.css"
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    # Load generated content styles
    generated_css_file = pathlib.Path(__file__).parent / "static" / "generated_content.css"
    with open(generated_css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css()

# Set up logging
logging.basicConfig(
    filename='artefact_generator_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

# Load artefact categories
def load_artefact_categories():
    try:
        with open('artefact_categories.json', 'r') as f:
            data = json.load(f)
            logging.info(f"Successfully loaded artefact types: {data['artefact_types']}")
            return data['artefact_types']
    except Exception as e:
        logging.error(f"Error loading artefact categories: {str(e)}")
        st.error(f"Error loading artefact categories: {str(e)}")
        return []

# Load prompt instructions
def load_prompt_instructions():
    try:
        with open('prompt_instructions.json', 'r') as f:
            data = json.load(f)
            return data['closing_instruction']
    except Exception as e:
        st.error(f"Error loading prompt instructions: {str(e)}")
        return "The artefact should reflect the context and show how the architecture serves as a catalyst for change."

# Initialize session state
if 'artefacts' not in st.session_state:
    st.session_state.artefacts = []
if 'show_thinking' not in st.session_state:
    st.session_state.show_thinking = False

def sanitize_filename(filename):
    """Convert a string to a valid filename"""
    # Remove invalid characters and replace spaces with underscores
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename

def save_artefact(artefact_content, project_description, date, location, user_bios, themes, model_config, temperature):
    """Save the artefact as a markdown file"""
    # Create artefacts directory if it doesn't exist
    os.makedirs('artefacts', exist_ok=True)
    
    # Create a sanitized filename from project description and date
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{timestamp}_{sanitize_filename(project_description[:50])}"
    filename = f"artefacts/{base_filename}.md"
    
    # Get model information
    provider = model_config.get('provider', '')
    model_name = model_config.get('model', 'unknown')
    
    # Create markdown content with generated-content class wrapper
    markdown_content = f"""<div class="generated-content{' show-think' if st.session_state.show_thinking else ''}">

# Diegetic Artefact

## Project
{project_description}

## Location
{location}

## Date/Timeframe
{date}

## User Personas
{user_bios}

## Key Themes
{themes}

## Generated Artefact
{artefact_content}

---
*Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*  
*Model: {provider}/{model_name} (temperature: {temperature})*

</div>"""
    
    # Save the file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filename

def load_model_config():
    """Load the model configuration from JSON file"""
    try:
        with open('model_config.json', 'r') as f:
            config = json.load(f)
            current_provider = config.get('current_provider', 'perplexity')
            provider_config = config['providers'].get(current_provider)
            if not provider_config:
                raise ValueError(f"Provider {current_provider} not found in configuration")
            return provider_config
    except Exception as e:
        logging.error(f"Error loading model configuration: {str(e)}")
        st.error(f"Error loading model configuration: {str(e)}")
        return {
            "model": "r1-1776",
            "max_tokens": 1600,
            "temperature": 0.7,
            "top_p": 0.9,
            "presence_penalty": 0.1,
            "api_endpoint": "https://api.perplexity.ai/chat/completions",
            "api_key_env": "PERPLEXITY_API_KEY",
            "headers": {
                "Content-Type": "application/json"
            }
        }

def get_model_temperature():
    model_config = load_model_config()
    provider = model_config.get('provider', '')
    default_temp = model_config.get("temperature", 0.7)
    
    # Define temperature ranges per provider
    temp_ranges = {
        'anthropic': (0.0, 1.0),
        'perplexity': (0.0, 1.99),
        'openai': (0.0, 2.0),
        'ollama': (0.0, 2.0)
    }
    
    # Get min/max for current provider, default to 0-1 if provider not found
    min_temp, max_temp = temp_ranges.get(provider, (0.0, 1.0))
    
    # Ensure default temperature is within valid range
    default_temp = min(max(default_temp, min_temp), max_temp)
    
    return st.slider(
        "Model Temperature - Lower values (0) create focused outputs, higher values create more creative, varied outputs",
        min_value=min_temp,
        max_value=max_temp,
        value=default_temp,
        step=0.1,
        label_visibility="visible",
        help="Technical: Temperature controls the randomness in the model's token selection process. Lower values increase the probability of selecting the most likely next token, while higher values make the distribution more uniform across all possible tokens."
    )

def calculate_max_tokens(project_description, user_bios, themes):
    # Estimate input complexity based on length and content
    input_length = len(project_description) + len(user_bios) + len(themes)
    
    if input_length > 1000:
        # Complex project needs more concise output
        return 1400
    else:
        # Simpler project can have slightly more detailed output
        return 1600

def prepare_request_data(prompt, model_config, temperature=None):
    """Prepare the request data based on the provider's requirements"""
    if temperature is not None:
        model_config = model_config.copy()  # Create a copy to avoid modifying the original
        model_config["temperature"] = temperature
    
    provider = model_config.get('provider', '')
    
    # Calculate buffer tokens for completion
    response_tokens = model_config["max_tokens"]
    safe_tokens = int(response_tokens * 0.9)  # Use 90% of max_tokens as safe limit
    
    # Add token guidance to prompt
    enhanced_prompt = prompt + f"\n\nYour response should be complete and no longer than approximately {safe_tokens} tokens."
    
    if provider == 'anthropic':
        # Custom system prompt for Anthropic that requests thinking in <think> tags
        system_prompt = """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.
        
        IMPORTANT: In your response, first share your reasoning process within <think> tags. Use this format:
        <think>
        Here I analyze what would be most effective for this project...
        </think>
        
        Then provide your final output after the thinking section. The <think> section won't be visible to the end user unless they choose to see it."""
        
        return {
            "model": model_config["model"],
            "max_tokens": model_config["max_tokens"],
            "temperature": model_config["temperature"],
            "system": system_prompt,
            "messages": [
                {
                    "role": "user", 
                    "content": enhanced_prompt + "\n\nIMPORTANT: First explain your reasoning within <think> tags before creating the final artifact. This thinking will help me understand your creative process."
                }
            ]
        }
    elif provider == 'ollama':
        # Ollama uses a simpler format with a system prompt and messages
        system_prompt = """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.
        
        IMPORTANT: In your response, first share your reasoning process within <think> tags. Use this format:
        <think>
        Here I analyze what would be most effective for this project...
        </think>
        
        Then provide your final output after the thinking section. The <think> section won't be visible to the end user unless they choose to see it."""
        
        return {
            "model": model_config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": enhanced_prompt + "\n\nFirst explain your reasoning within <think> tags before creating the final artifact."
                }
            ],
            "stream": False,
            "options": {
                "temperature": model_config["temperature"],
                "top_p": model_config.get("top_p", 0.9),
                "num_predict": model_config["max_tokens"]
            }
        }
    else:  # Default to OpenAI/Perplexity format
        data = {
            "model": model_config["model"],
            "messages": [{
                "role": "system",
                "content": """You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.
                
                IMPORTANT: Structure your response in exactly two parts:
                1. First, a thinking section wrapped in <think> tags that explains your reasoning
                2. Then, the final artifact output after a clear closing </think> tag
                
                Example structure:
                <think>
                Your reasoning here...
                </think>
                
                Your final artifact here..."""
            },
            {
                "role": "user", 
                "content": enhanced_prompt + "\n\nIMPORTANT: Begin with your reasoning in <think> tags, then close the tag with </think> before providing the final artifact."
            }],
            "max_tokens": calculate_max_tokens(project_description, user_bios, themes),
            "temperature": model_config["temperature"],
            "top_p": model_config.get("top_p", 0.9),
            "presence_penalty": model_config.get("presence_penalty", 0.1)
        }
        
        # Remove the authorization from data - it should only be in headers
        return data

def extract_response(response, model_config):
    """Extract the response content based on the provider's response format"""
    provider = model_config.get('provider', '')
    
    # Log the response structure to help with debugging
    response_json = response.json()
    logging.debug(f"Response keys: {list(response_json.keys())}")
    
    if provider == 'anthropic':
        # Anthropic response structure is different
        try:
            return response_json['content'][0]['text']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting Anthropic response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"
    elif provider == 'ollama':
        # Ollama response structure
        try:
            return response_json['message']['content']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting Ollama response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"
    else:  # Default to OpenAI/Perplexity format
        try:
            return response_json['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            logging.error(f"Error extracting response: {str(e)}")
            logging.debug(f"Response content: {response_json}")
            return f"Error parsing response: {str(e)}"

def generate_artefact(project_description, date, user_bios, themes, location, selected_type, temperature=None):
    """Generate a diegetic artefact using the configured API provider"""
    # Load model configuration
    model_config = load_model_config()
    
    # Get API key if required
    provider = model_config.get('provider', '')
    api_key = None
    if provider != 'ollama':  # Ollama doesn't require an API key
        api_key = os.getenv(model_config['api_key_env'])
        if not api_key:
            return f"Error: {model_config['api_key_env']} not found in environment variables"

    # Prepare headers
    headers = model_config['headers'].copy()
    
    # Handle provider-specific authorization formats
    if provider == 'anthropic':
        # Anthropic uses x-api-key instead of Authorization: Bearer
        headers["x-api-key"] = api_key
    elif provider != 'ollama':  # Ollama doesn't require authorization
        # Default Bearer format for other providers
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Log which provider we're using
    logging.info(f"Using provider: {provider if provider else 'default'}")

    # Get the selected artefact type
    artefact_type = selected_type['category']

    closing_instruction = load_prompt_instructions()

    prompt = f"""You are a dramatalurgical expert that creates diegetic artefacts for architectural projects.
    Your task is to imagine and create a specific diegetic artefact within the category of '{artefact_type}' that exists within the narrative world of this project.
    First, decide on an appropriate specific artefact type within this category that would be meaningful for this project.

    Project Information:
    Description: {project_description}
    Location: {location}
    Date/Timeframe: {date}
    User Personas: {user_bios}
    Key Themes: {themes}

    Instructions:
    1. Begin by briefly explaining (100-150 words) your choice of specific artefact within the {artefact_type} category.
    2. Add a brief summary (2-3 sentences) explaining how this artefact relates to the project's themes and context.
    3. Pose 2-3 thought-provoking questions for the user to consider about the relationship between this artefact and the architecture project.
    4. Finally, create the diegetic artefact itself (500-750 words) in the appropriate format and style using markdown syntax to ensure it is visibly distinct. Refer to {closing_instruction} for additional abductive thinking opportunities. Ensure content is not truncated by the target word count and token limit. Rewrite to avoid this if necessary.   

    Markdown Formatting Guidelines:
    - Use proper heading hierarchy (# for main title, ## for sections, ### for subsections)
    - Format emphasis appropriately (* for italic, ** for bold)
    - Use proper list formatting (- for unordered lists, 1. for ordered lists)
    - Include line breaks between paragraphs for readability
    - Use horizontal rules (---) to separate major sections

    IMPORTANT: Your entire response must fit within {model_config["max_tokens"]} tokens. 
    Structure your response to ensure your artefact is complete and not cut off.
    The most important parts should come first, and conclude with a proper ending.

    Begin your response:"""

    # Prepare request data based on provider
    data = prepare_request_data(prompt, model_config, temperature)
    
    # Log request information (without sensitive data)
    logging.debug(f"Sending request to: {model_config['api_endpoint']}")
    logging.debug(f"Request data keys: {list(data.keys())}")

    try:
        response = requests.post(
            model_config["api_endpoint"],
            headers=headers,
            json=data
        )
        
        # Log response information
        logging.debug(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            error_message = f"API Error: {response.status_code} - {response.text}"
            logging.error(error_message)
            st.error(error_message)
            return error_message
            
        response_content = extract_response(response, model_config)
        response_length = len(response_content)
        if response_length > (model_config["max_tokens"] * 0.9):
            logging.warning(f"Response approaching token limit: {response_length} tokens")
        return response_content
    except Exception as e:
        error_message = f"Error generating artefact: {str(e)}"
        logging.error(error_message)
        st.error(error_message)
        return error_message

# Main interface
st.title("🏛️ Diegetic Artefact Generator")
st.markdown("""
This tool helps architects generate diegetic artefacts—speculative objects that exist within the narrative world of an architectural project.""")

# Sidebar controls
with st.sidebar:
    st.header("Model Settings")
    
    # Load model configurations
    with open('model_config.json', 'r') as f:
        config = json.load(f)
    
    # Model selection
    current_provider = st.selectbox(
        "Choose Model Provider",
        options=list(config['providers'].keys()),
        index=list(config['providers'].keys()).index(config['current_provider']),
        help="Select which AI model to use for generation"
    )
    
    # Update the current provider in the config
    config['current_provider'] = current_provider
    
    # Save the updated config
    with open('model_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Add a separator
    st.markdown("---")
    
    # Move temperature slider to sidebar
    temperature = get_model_temperature()

# Input form
with st.form("artefact_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        project_description = st.text_area(
            "Project Description",
            placeholder="Describe your architectural project...",
            height=150
        )
        location = st.text_input(
            "Project Location",
            placeholder="e.g., London, UK or specific address"
        )
        date = st.text_input(
            "Date/Timeframe",
            placeholder="e.g., 2025, 2030, or 'Alternative Present'"
        )
    
    with col2:
        user_bios = st.text_area(
            "User Personas",
            placeholder="Describe the key users or inhabitants of the space...",
            height=150
        )
        themes = st.text_area(
            "Key Themes",
            placeholder="List the main themes, socioeconomic contexts, and political frameworks...",
            height=150
        )
    
    # Add category selection dropdown
    artefact_types = load_artefact_categories()
    selected_category = st.selectbox(
        "Choose Artefact Category",
        options=artefact_types,
        help="Select the category of diegetic artefact you want to generate"
    )
    
    # Center and style the generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.form_submit_button(
            "Generate Artefact",
            use_container_width=True,
            type="primary"
        )

# Generate and display results
if submitted:
    if not all([project_description, date, user_bios, themes, location, selected_category]):
        st.warning("Please fill in all fields before generating an artefact.")
    else:
        with st.spinner("Generating your diegetic artefact..."):
            selected_type = {"category": selected_category, "items": [selected_category]}
            
            # Use the temperature value from outside the form
            st.session_state.current_artefact = generate_artefact(
                project_description,
                date,
                user_bios,
                themes,
                location,
                selected_type,
                temperature=temperature
            )
            if not st.session_state.current_artefact.startswith("Error"):
                # Save the artefact to a file
                model_config = load_model_config()  # Get current model config
                filename = save_artefact(
                    st.session_state.current_artefact,
                    project_description,
                    date,
                    location,
                    user_bios,
                    themes,
                    model_config,
                    temperature
                )
                st.session_state.current_filename = filename
                st.success(f"Artefact saved to: {filename}")

# Display section (outside the form and submit block)
if 'current_artefact' in st.session_state and not st.session_state.current_artefact.startswith("Error"):
    show_thinking = st.checkbox("Show AI thinking process", value=st.session_state.show_thinking)
    st.session_state.show_thinking = show_thinking
    
    # Process the artefact content to handle think blocks
    content_parts = []
    for line in st.session_state.current_artefact.split('\n'):
        if '<think>' in line:
            content_parts.append('<div class="think-block">')
        elif '</think>' in line:
            content_parts.append('</div>')
        else:
            content_parts.append(line)
    
    # Combine the content and wrap it in a container with generated-content class
    container_classes = ["generated-content"]
    if show_thinking:
        container_classes.append("show-think")
    
    content = '\n'.join(content_parts)
    st.markdown(
        f'<div class="{" ".join(container_classes)}">{content}</div>',
        unsafe_allow_html=True
    )
    
    # Add a download button
    st.download_button(
        label="Download Artefact",
        data=st.session_state.current_artefact,
        file_name=os.path.basename(st.session_state.current_filename),
        mime="text/markdown"
    )

# Footer
st.markdown("---")
st.markdown("Built for exploring novel, prefigurative architectural practice through narrative artefacts") 