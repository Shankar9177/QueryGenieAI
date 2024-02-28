import streamlit as st
import pandas as pd
from pandasai import PandasAI
from pandasai.llm.azure_openai import AzureOpenAI 
import os
import time 
import pandas as pd
from ydata_profiling import ProfileReport
import streamlit as st
from pandasai.smart_dataframe import SmartDataframe
from streamlit_pandas_profiling import st_profile_report
import tempfile
from pandasai.llm.openai import OpenAI
from pdf_processor import process_pdf_and_answer_questions
from snowflake_processor import process_snowflake_data
from azure_config import AZURE_OPENAI_API_KEY 

# Set your Azure OpenAI API key
azure_openai_api_key = AZURE_OPENAI_API_KEY
 
# Create an LLM by instantiating AzureOpenAI object and passing the API token
llm = AzureOpenAI(
    deployment_name="i2r-gpt-35-turbo-instruct",
    api_token=azure_openai_api_key,
    api_base = "https://i2r-openai.openai.azure.com/",
    api_version="2023-07-01-preview"
)
# Create PandasAI object, passing the LLM
#pandas_ai = PandasAI(llm, save_charts=True)
pandas_ai = PandasAI(llm, save_charts=True, save_charts_path =  "exports\\charts\\temp_chart.png")


# st.image("QG_logo3.png")  # Adjust width as needed
#st.header("QueryGenie🧞")

# Set page configuration with the genie image
st.set_page_config(page_title="QueryGenie", page_icon="QG_logo3.png")
st.image("QG_logo3.png")

# Placeholder for user profile in the sidebar
 
st.sidebar.image("user_icon.png",  width=100)
st.sidebar.header("Logged in as Souvik")

# Login/Logout button
if st.sidebar.button("Logout"):
    # Add your login logic here
    st.sidebar.success("")
 
info_markdown = """
# How it Works? 🚀
 
1. **Upload CSV Files 📊**: Upon uploading your CSV files, QueryGenie (QG) automatically provides a basic profile of your data. This includes insights like the number of columns, presence of duplicate or missing values, and data correlations.
 
2. **Visualize and Interact with Data 🔍**: Use the `@chatcsv` plugin to dive deeper. You can ask questions or request visualizations directly related to your uploaded CSV data. `@chatcsv` serves as your interactive assistant, offering answers and creating custom visualizations based on your needs.
 
3. **Explore PDF Documents 📄**: Got PDF files? No problem! With the `@chatdoc` plugin, you can upload your PDF documents and ask specific questions about their content. This feature allows you to interactively explore and extract information from your PDFs with ease.

4. **Explore Snowflake ❄️**: Your Data is in Snowflake? QG has the ability to query your snowflake database and then give you all the insights and visualizations about it. Use our `@chatsnow` plugin to interact with your snowflake data. 

4. **Explore All ✅**: use `@chatall` to explore all your data from various sources at ease! 
"""
 
# Use st.markdown to display the formatted text in your Streamlit app
st.sidebar.markdown(info_markdown)
                  
# Initialize Streamlit session for our conversational app

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.profiles = {}  # Initialize the profiles dictionary
    st.session_state.selected_tables = []  # Initialize selected Snowflake tabless




# Allow user to upload multiple CSV files for analysis
uploaded_files = st.file_uploader("Upload CSV files here for analysis", type=['csv'], accept_multiple_files=True)
#Allow user to upload a PDF file for analysis
pdf_uploaded_file = st.file_uploader("Upload PDF file here for analysis", type=['pdf'], accept_multiple_files=False)

with st.expander("Want to connect to your Snowflake?"):
    # Create a form for Snowflake connection details
    with st.form("snowflake_connection_form"):
        sf_user = st.text_input("Snowflake User", placeholder="Enter your Snowflake username")
        sf_password = st.text_input("Snowflake Password", type="password", placeholder="Enter your Snowflake password")
        connect_button = st.form_submit_button("Connect")
        # Disconnect button inside the form
        disconnect_button = st.form_submit_button("Disconnect")

        if disconnect_button:
            if st.session_state.get('connected', False):
                st.session_state['connected'] = False
                st.success("Disconnected from Snowflake")

    # Check if connected, if not, establish connection
    if connect_button:
        with st.spinner('Connecting to Snowflake...'):
            snowflake_tables, conn = process_snowflake_data(sf_user, sf_password)
            st.session_state['connected'] = True
            st.session_state['snowflake_tables'] = snowflake_tables
            st.session_state['conn'] = conn
            st.snow()
            st.success("Connected to Snowflake successfully!")
            

    # Once connected, display the table selection dropdown
    if st.session_state.get('connected', False):
        selected_tables = st.multiselect("Select Snowflake tables", st.session_state['snowflake_tables'], key='table_select')
        st.session_state['selected_tables'] = selected_tables

    if 'snowflake_dataframes' not in st.session_state:
        st.session_state['snowflake_dataframes'] = []
    # Button to query the selected tables
    query_button = st.button("Query")

    # Check if query button is pressed and tables are selected
    if query_button and selected_tables:
        st.session_state['snowflake_dataframes'] = []
        for table in selected_tables:
            query = f"SELECT * FROM {table}"
            snowflake_df = pd.read_sql(query, st.session_state['conn'])
            st.subheader(f"Snowflake Table: {table}")
            st.dataframe(snowflake_df)
            st.session_state['snowflake_dataframes'].append(snowflake_df)

      
    else:
        st.error("Select tables and query")


        
#Process the uploaded PDF file and store a profile report only when first created
if pdf_uploaded_file:
    pdf_file_content = pdf_uploaded_file.read()
    

# Display the uploaded CSV files
if uploaded_files:
    dataframes = [pd.read_csv(file) for file in uploaded_files]

    # Display the uploaded DataFrames and store profiles
    for file_num, df in enumerate(dataframes, start=1):
        profile_name = f"CSV_Profile_{file_num}"
        if profile_name not in st.session_state.profiles:
            st.session_state.profiles[profile_name] = df

        st.subheader(f"Uploaded Table {file_num}")
        st.dataframe(df)

# Remove profiles associated with removed CSV files
existing_profiles = list(st.session_state.profiles.keys())
for existing_profile in existing_profiles:
    if existing_profile not in [f"CSV_Profile_{i}" for i in range(1, len(uploaded_files) + 1)]:
        del st.session_state.profiles[existing_profile]

# Play with the prompt
if prompt := st.chat_input("Ask me anything 😉"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # concat and create snowflake + csv df list
    combined_dataframes = dataframes + st.session_state.get('snowflake_dataframes', [])

    if "@chatcsv" in prompt.lower():
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            modified_prompt = prompt.replace("@chatcsv", "").strip()
            response = pandas_ai.run(dataframes, modified_prompt)
        

            print("Here is the response type",type(response))
            print("Here is the response",response)
      
            image_path = "exports\\charts\\temp_chart.png"
            st.image(image_path, caption='Visualization Image', use_column_width=True)
            # give the user functionality to download the image
            with open(image_path, "rb") as file:
                btn = st.download_button(
                        label="Download image",
                        data=file,
                        file_name="chart.png",
                        mime="image/png"
                    )

    # for debugging only
    elif "@chatdebug" in prompt.lower():
        print("Debugging mode on xD")
        print("this is snow df:", st.session_state['snowflake_dataframes'])
        print("this is snow df type:", type(st.session_state['snowflake_dataframes']))
        print("this is csv df:", dataframes)
        print("this is csv df type:", type(dataframes))
        # Combine the lists, ensuring that snowflake_dataframes is not empty
        combined_dataframes = dataframes + st.session_state.get('snowflake_dataframes', [])
        print("this is combined df:", combined_dataframes)
        print("this is combined df type:", type(combined_dataframes))

    elif "@chatdoc" in prompt.lower():
         with st.chat_message("assistant"):
            modified_prompt = prompt.replace("@chatdoc", "").strip()
            result = process_pdf_and_answer_questions(pdf_file_content, modified_prompt, azure_openai_api_key)
            st.write(result)

    elif "@chatsnow" in prompt.lower():
        with st.chat_message("assistant"):
            modified_prompt = prompt.replace("@chatsnow", "").strip()
            # Check if the user wants to visualize the Snowflake DataFrame
            visualize_request = "visualize" in prompt.lower()
            response = pandas_ai.run(st.session_state['snowflake_dataframes'], modified_prompt)

            if visualize_request:
                    # Visualize the Snowflake DataFrame based on the response
                    image_path = "exports\\charts\\temp_chart.png"
                    st.image(image_path, caption='Visualization Image', use_column_width=True)
                    # give the user functionality to download the image
                    with open(image_path, "rb") as file:
                        btn = st.download_button(
                            label="Download image",
                            data=file,
                            file_name="chart_snow.png",
                            mime="image/png"
                        )
            
            else:
                 if isinstance(response, SmartDataframe):
                    # Convert SmartDataframe to pandas DataFrame
                    df_result = response._df
                    # Display the result in Streamlit frontend
                    st.table(df_result)

                 elif type(response) in (pd.core.frame.DataFrame, pd.DataFrame):
                    st.table(response)

                 else:
                    st.markdown(response)

    elif "@chatall" in prompt.lower():
        with st.chat_message("assistant"):
            modified_prompt = prompt.replace("@chatall", "").strip()
            # Check if the user wants to visualize the Snowflake DataFrame
            visualize_request = "visualize" in prompt.lower()
            response = pandas_ai.run(combined_dataframes, modified_prompt)

            if visualize_request:
                    # Visualize the Snowflake DataFrame based on the response
                    image_path = "exports\\charts\\temp_chart.png"
                    st.image(image_path, caption='Visualization Image', use_column_width=True)
                    # give the user functionality to download the image
                    with open(image_path, "rb") as file:
                        btn = st.download_button(
                            label="Download image",
                            data=file,
                            file_name="chart_snow.png",
                            mime="image/png"
                        )
            else:
                 if isinstance(response, SmartDataframe):
                    # Convert SmartDataframe to pandas DataFrame
                    df_result = response._df
                    # Display the result in Streamlit frontend
                    st.table(df_result)

                 elif type(response) in (pd.core.frame.DataFrame, pd.DataFrame):
                    st.table(response)

                 else:
                    st.markdown(response)

    elif "@profilercsv" in prompt.lower():
        # Generate profile report for uploaded CSV files
        for profile_name, df in st.session_state.profiles.items():
            with st.expander(f"Profile: {profile_name}"):
                # Generate profile report only when not already generated
                if f"{profile_name}_report" not in st.session_state:
                    report = ProfileReport(df, title=f"Report {profile_name}")
                    st.session_state[f"{profile_name}_report"] = report

                # Display the profile report
                st_profile_report(st.session_state[f"{profile_name}_report"])

                # Save the report to a temporary file only when first created
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                if not hasattr(st.session_state[f"{profile_name}_report"], '_saved'):
                    st.session_state[f"{profile_name}_report"].to_file(temp_file.name)
                    st.session_state[f"{profile_name}_report"]._saved = True  # Mark the profile as saved

                # Read the content of the temporary file
                with open(temp_file.name, 'r', encoding='utf-8') as file:
                    file_content = file.read()

                # Provide a download button for the report with the content
                download_label = f"Download Report {profile_name}"
                st.download_button(
                    label=download_label,
                    data=file_content,
                    file_name=f"report_{profile_name}.html",
                    key=f"download_button_{profile_name}"
                )

        # If no profile is available for the removed CSV file, show a warning
        if not st.session_state.profiles:
            st.warning("No profile available please upload CSV file to generate profile.")

    elif "@profilersnow" in prompt.lower():
        # Check if connected to Snowflake
        if not st.session_state.get('connected', False):
            st.warning("Please connect to Snowflake first.")
        else:
            with st.chat_message("assistant"):
                modified_prompt = prompt.replace("@profilersnow", "").strip()
                selected_tables = st.session_state.get('selected_tables', [])

                # Check if tables are selected
                if not selected_tables:
                    st.warning("Please select Snowflake tables first.")
                else:
                    # Generate profile report for selected Snowflake tables
                    for table in selected_tables:
                        snowflake_df = pd.read_sql(f"SELECT * FROM {table}", st.session_state['conn'])
                        with st.expander(f"Profile: {table}"):
                            # Generate profile report only when not already generated
                            if f"{table}_report" not in st.session_state:
                                report = ProfileReport(snowflake_df, title=f"Report {table}")
                                st.session_state[f"{table}_report"] = report

                            # Display the profile report
                            st_profile_report(st.session_state[f"{table}_report"])

                            # Save the report to a temporary file only when first created
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
                            if not hasattr(st.session_state[f"{table}_report"], '_saved'):
                                st.session_state[f"{table}_report"].to_file(temp_file.name)
                                st.session_state[f"{table}_report"]._saved = True  # Mark the profile as saved

                            # Read the content of the temporary file
                            with open(temp_file.name, 'r', encoding='utf-8') as file:
                                file_content = file.read()

                            # Provide a download button for the report with the content
                            download_label = f"Download Report {table}"
                            st.download_button(
                                label=download_label,
                                data=file_content,
                                file_name=f"report_{table}.html",
                                key=f"download_button_{table}"
                            )

    # if "@chatcsvsnow" in prompt.lower():
        
    #     with st.chat_message("assistant"):
    #         message_placeholder = st.empty()

    #         modified_prompt = prompt.replace("@chatcsvsnow", "").strip()
    #         response = pandas_ai.run(dataframes, modified_prompt)
        

    #         print("Here is the response type",type(response))
    #         print("Here is the response",response)
      
    #         image_path = "exports\\charts\\temp_chart.png"
    #         st.image(image_path, caption='Visualization Image', use_column_width=True)
    #         # give the user functionality to download the image
    #         with open(image_path, "rb") as file:
    #             btn = st.download_button(
    #                     label="Download image",
    #                     data=file,
    #                     file_name="chart.png",
    #                     mime="image/png"
    #                 )
                
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            response = pandas_ai.run(dataframes, prompt)

            if isinstance(response, SmartDataframe):
                # Convert SmartDataframe to pandas DataFrame
                df_result = response._df
                # Display the result in Streamlit frontend
                st.table(df_result)

            elif type(response) in (pd.core.frame.DataFrame, pd.DataFrame):
                st.table(response)

            else:
                st.markdown(response)
