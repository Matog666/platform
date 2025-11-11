import streamlit as st
import anthropic
import pandas as pd
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# .\venv\Scripts\Activate

# Your API key
key = "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"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# ========== GOOGLE DRIVE FUNCTIONS ==========

def authenticate_google_drive():
    """Authenticate with Google Drive"""
    creds = None
    
    # Check for existing token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Token refresh failed: {e}")
                if os.path.exists('token.pickle'):
                    os.remove('token.pickle')
                return authenticate_google_drive()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', 
                SCOPES,
                redirect_uri='http://localhost:8080'
            )
            
            try:
                creds = flow.run_local_server(
                    port=8080,
                    prompt='consent',
                    authorization_prompt_message='Please visit this URL to authorize the application: {url}',
                    success_message='The auth flow is complete; you may close this window.',
                    open_browser=True
                )
            except Exception as e:
                st.error(f"Authentication failed: {e}")
                return None
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Failed to build service: {e}")
        return None

def get_folder_id(service, folder_name):
    """Find folder ID by name"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    
    results = service.files().list(
        q=query,
        pageSize=10,
        fields="files(id, name)"
    ).execute()
    
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    else:
        return None

def list_target_files(service, folder_id):
    """List all .docx and .csv files in the Oilbot folder"""
    query = f"'{folder_id}' in parents and trashed=false"
    
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, mimeType, modifiedTime, size)",
        orderBy="modifiedTime desc"
    ).execute()
    
    files = results.get('files', [])
    
    # Filter for .docx and .csv files only
    target_files = []
    for file in files:
        if (file['name'].endswith('.docx') or 
            file['name'].endswith('.csv') or
            file['mimeType'] == 'application/vnd.google-apps.document' or
            file['mimeType'] == 'text/csv'):
            target_files.append(file)
    
    return target_files

def download_and_process_file(service, file_id, file_name, mime_type):
    """Download file from Google Drive and process based on type"""
    
    try:
        # Handle Google Docs export to docx
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        else:
            request = service.files().get_media(fileId=file_id)
        
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        file_content.seek(0)
        
        # Process based on file type
        if file_name.endswith('.csv') or mime_type == 'text/csv':
            df = pd.read_csv(file_content)
            return f"CSV data from {file_name}:\n{df.head(10).to_string()}\n{df.describe().to_string()}\n"
            
        elif file_name.endswith('.docx') or mime_type == 'application/vnd.google-apps.document':
            # For docx, try to extract text (you may need python-docx library)
            try:
                from docx import Document
                doc = Document(file_content)
                text = "\n".join([para.text for para in doc.paragraphs])
                if len(text) > 3000:
                    text = text[:3000] + "... [truncated]"
                return f"Document content from {file_name}:\n{text}\n"
            except ImportError:
                return f"Word document {file_name} detected (install python-docx for full processing)\n"
            except Exception as e:
                return f"Error reading docx {file_name}: {str(e)}\n"
        else:
            return f"File {file_name} processed\n"
            
    except Exception as e:
        return f"Error processing {file_name}: {str(e)}\n"

def load_all_files_context():
    """Automatically load all .docx and .csv files from Oilbot folder"""
    try:
        # Authenticate
        service = authenticate_google_drive()
        
        if not service:
            return None, "Failed to authenticate with Google Drive"
        
        # Get Oilbot folder ID
        folder_id = get_folder_id(service, "Oilbot")
        
        if not folder_id:
            return None, "Oilbot folder not found"
        
        # Get all target files
        files = list_target_files(service, folder_id)
        
        if not files:
            return "", "No .docx or .csv files found in Oilbot folder"
        
        # Process all files
        file_context = ""
        file_names = []
        
        for file in files:
            file_data = download_and_process_file(
                service, 
                file['id'], 
                file['name'],
                file.get('mimeType', '')
            )
            file_context += file_data + "\n"
            file_names.append(file['name'])
        
        return file_context, f"Loaded {len(files)} files: {', '.join(file_names)}"
        
    except Exception as e:
        return None, f"Error loading files: {str(e)}"

# ========== STREAMLIT APP ==========

def run_oil_chatbot():
    """Main function to run the oil chatbot - can be called as a tab"""
    
    st.title("Let's talk about Oil & Tankers")

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stTextArea > div > div > textarea {
        font-family: 'Courier New', monospace;
    }
    .stButton > button {
        
        color: white;
        font-weight: bold;
        border-radius: 10px;
    }
    .stButton > button:hover {
        background-color: orange;
        border-color: #1a5d0d;
        color: white;        
    }
    </style>
    """, unsafe_allow_html=True)

    # Auto-load files on first run
    if 'files_loaded' not in st.session_state:
        with st.spinner("📁 Wait while loading files for context..."):
            file_context, message = load_all_files_context()
            
            if file_context is not None:
                st.session_state['file_context'] = file_context
                st.session_state['files_loaded'] = True
                st.success(f"✅ Files loaded")
            else:
                st.warning(f"⚠️ {message}")
                st.session_state['file_context'] = ""
                st.session_state['files_loaded'] = True

    # Refresh button (optional, but useful)
    if st.button("🔄 Refresh Data Files"):
        with st.spinner("📁 Reloading data files..."):
            file_context, message = load_all_files_context()
            
            if file_context is not None:
                st.session_state['file_context'] = file_context
                st.success(f"✅ All files reloaded")
            else:
                st.warning(f"⚠️ {message}")

    # ========== MAIN CHAT INTERFACE ==========

    # Create two columns - chat input (left) and response (right)
    col1, col2 = st.columns([1, 1.5])  # Right column is 50% bigger

    with col1:
            
        # Text input area
        oil_query = st.text_area(
            "Enter your query", 
            height=300,
            placeholder="Ask about oil prices, tanker rates, market analysis, etc."
        )
        
        # Go button
        if st.button("🚀 Send it!", use_container_width=True):
            if oil_query:
                # Store the query in session state to trigger response
                st.session_state['current_query'] = oil_query
                st.session_state['processing'] = True
            else:
                st.warning("⚠️ Please enter a question!")

    with col2:
        st.header("📊 Analysis Response")
        
        # Check if we have a query to process
        if 'current_query' in st.session_state and st.session_state.get('processing', False):
            
            # Get file context
            file_context = st.session_state.get('file_context', "")
            
            # Enhanced system prompt with file context
            file_context_section = f"Current data context from uploaded files:\n{file_context}" if file_context else ""

            system_prompt = f"""You are an oil analyst with access to current market data from Google Drive. 
            Your target audience are oil traders, investors, analysts and tanker operators. 
            You need to extract relevant data focusing on facts and figures. Read always the intructions in the file "1_Oil Training.docx" for detailed steps for common queries, and how to answer particular questions

            {file_context_section}

            "Read the file "1_Oil Training.docx first and use the provided data for context, focusing on Historical_prices.csv and the current week .docx document for updated news, and search the internet when additional information is needed. 
            Only provide updated information."""
            
            # Call Anthropic API with spinner
            with st.spinner("Analyzing your query..."):
                try:
                    client = anthropic.Anthropic(api_key=key)
                    
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        temperature=1,
                        system=system_prompt,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": st.session_state['current_query']
                                    }
                                ]
                            }
                        ]
                    )
                    
                    query_response = message.content[0].text if message.content else "I can't answer that right now"
                    
                    # Display response in a nice container
                    st.success("✅ Analysis Complete!")
                    
                    # Show the response
                    with st.container():
                        st.markdown("**Response:**")
                        st.markdown(query_response)
                    
                    # Store response in session state for persistence
                    st.session_state['last_response'] = query_response
                    st.session_state['last_query'] = st.session_state['current_query']
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                
                finally:
                    # Clear processing flag
                    st.session_state['processing'] = False
        
        # Show last response if available (for persistence)
        elif 'last_response' in st.session_state:
            st.info("💡 Previous Analysis:")
            with st.container():
                st.markdown(f"**Question:** {st.session_state.get('last_query', 'Previous query')}")
                st.markdown("**Response:**")
                st.markdown(st.session_state['last_response'])
        
        else:
            # Placeholder when no query has been made
            st.info("👆 Enter a question on the left and click 'Analyze' to get started!")
            
            # Add some example queries
            st.markdown("**Example queries:**")
            st.markdown("""
            - What are current Brent crude prices?
            - Analyze tanker rates for VLCC vessels
            - What about refined products?
            - What's driving oil price volatility this week?
            - What happened in the Middle East this week?
            - Are those goddamn' arbs open?          
            """)

# If running as standalone app
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Oil & Tanker Chatbot")

    run_oil_chatbot()
