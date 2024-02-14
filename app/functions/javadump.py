import streamlit as st
from functions.utils import tokenparameter
import time, datetime, zipfile
from io import BytesIO

def get_date():
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d_%H%M")

def do_dump_project():
    st.markdown('### 🚨 JAVA Dump')

    delete = st.checkbox('Delete pod after dump?')
    
    col1, col2 = st.columns([1, 2])
    col1, col2, col3 = st.columns(3)
    with col1:
        optioncluster = st.selectbox('Select Cluster', ('','prodarwin', 'dmzbdarwin', 'azure', 'confluent', 'dmz2bmov', 'probks','dmzbbks'),key = "optioncluster1")

    with col2:
        if optioncluster == 'azure':
            optionregion = st.selectbox('Select Region', ('','weu1', 'weu2'),key = "optioncluster2")

        if optioncluster != 'azure':
            optionregion = st.selectbox('Select Region', ('','bo1', 'bo2'),key = "optioncluster3")
    
    with col3:
        if optioncluster != '' and optionregion != '':
            json_object_namespace = tokenparameter(cluster=optioncluster,region=optionregion,do_api='namespacelist')
            if json_object_namespace is not None:
                # split namespace list
                flat_list = [x for x in json_object_namespace]
                selectnamespace = st.selectbox('Select Namespace', ([''] + flat_list),key = "selectnamespace1")

                with col1:
                    if selectnamespace != '':
                        json_object_microservice = tokenparameter(cluster=optioncluster,region=optionregion,namespace=selectnamespace,do_api='microservicelist')
                        if json_object_microservice is not None:
                            flat_micro = [x for x in json_object_microservice]
                            selectmicroservice = st.selectbox('Select Microservice', ([''] + flat_micro),key = "selectmicroservice1")
                            
                            with col2:
                                if selectmicroservice != '':
                                    json_object_pod = tokenparameter(cluster=optioncluster,region=optionregion,namespace=selectnamespace,microservice=selectmicroservice,do_api='podlist')
                                    if json_object_pod is not None:
                                        flat_pod = [x for x in json_object_pod]
                                        selectpod = st.selectbox('Select Pod', ([''] + flat_pod),key = "pod1")

                                        @st.cache_data(ttl=900,show_spinner=False)
                                        def get_file_content(cluster, region, namespace, pod, do_api, delete):
                                            content = tokenparameter(cluster=cluster, region=region, namespace=namespace, pod=pod, do_api=do_api, delete=delete)
                                            file_parts = []
                                            for i in range(0, len(content), 100_000_000):  # Partition into 100 MB chunks
                                                file_parts.append(content[i:i+100_000_000])
                                            return file_parts
                                        
                                        def get_file_content2(cluster, region, namespace, pod, do_api, delete):
                                            return tokenparameter(cluster=cluster, region=region, namespace=namespace, pod=pod, do_api=do_api, delete=delete)
                                        with col3:
                                            if selectpod != '':
                                                selectedheap = st.selectbox('Select type', ('', 'HeapDump', 'ThreadDump', 'HeapDump DataGrid', 'ThreadDump DataGrid'),key = "opt_restart_r")

                                                with col2:
                                                    if selectedheap == "HeapDump":
                                                        execute_button = st.button('Execute')
                                                        if execute_button:
                                                            try:
                                                                with st.spinner(text='Work in progress... '):
                                                                    parts_file = get_file_content(cluster=optioncluster, region=optionregion, namespace=selectnamespace, pod=selectpod, do_api='heapdump', delete=delete)

                                                                date = get_date()
                                                                zip_file_name = f'HeapDump-{selectpod}-{date}.zip'

                                                                zip_buffer = BytesIO()
                                                                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:  # Create an in-memory buffer for the ZIP
                                                                    for i, part in enumerate(parts_file):
                                                                        part_file_name = f'HeapDump-part-{i}.gz'
                                                                        zip_file.writestr(part_file_name, part)

                                                                # Create individual download buttons for each part of the heapdump
                                                                with st.expander("Download in parts"):
                                                                    for i, part in enumerate(parts_file):
                                                                        part_file_name = f'HeapDump-part-{i}.gz'
                                                                        st.download_button(
                                                                            label=f"Download part {i+1}",
                                                                            data=part,
                                                                            file_name=part_file_name,
                                                                            mime='application/gzip',
                                                                            )

                                                                # Create a button to download the entire ZIP file
                                                                st.download_button(
                                                                    label="Download in one ZIP File",
                                                                    data=zip_buffer.getvalue(),
                                                                    file_name=zip_file_name,
                                                                    mime='application/octet-stream',
                                                                    )
                                                            except Exception as e:
                                                                st.error(f"Error generating heapdump: {e}")

                                                    if selectedheap == "HeapDump DataGrid":
                                                        execute_button = st.button('Execute')
                                                        if execute_button:
                                                            try:
                                                                with st.spinner(text='🚧 Work in progress... '):
                                                                    file_content = get_file_content2(cluster=optioncluster,region=optionregion,namespace=selectnamespace,pod=selectpod,do_api='heapdump_datagrid', delete=delete)

                                                                date = get_date()
                                                                if file_content != [{"heapdumpdatagrid": None}]:
                                                                    st.download_button(
                                                                        label="Download dump file 🔽",
                                                                        data=file_content,
                                                                        file_name=f'HeapDump_DG-{selectpod}-{date}.gz',
                                                                        mime='application/octet-stream',
                                                                    )

                                                            except Exception as e:
                                                                st.write(f'Error downloading file: {e}')

                                                    if selectedheap == "ThreadDump":
                                                        execute_button = st.button('Execute')
                                                        if execute_button:
                                                            try:
                                                                with st.spinner(text='🚧 Work in progress... '):
                                                                    file_content = get_file_content2(cluster=optioncluster,region=optionregion,namespace=selectnamespace,pod=selectpod,do_api='threaddump', delete=delete)

                                                                date = get_date()
                                                                if file_content != [{"threaddump": None}]:
                                                                                                                            
                                                                    st.download_button(
                                                                        label="Download dump file 🔽",
                                                                        data=file_content,
                                                                        file_name=f'ThreadDump-{selectpod}-{date}.gz',
                                                                        mime='application/octet-stream',
                                                                    )

                                                            except Exception as e:
                                                                st.write(f'Error downloading file: {e}')

                                                    if selectedheap == "ThreadDump DataGrid":
                                                        execute_button = st.button('Execute')
                                                        if execute_button:
                                                            try:
                                                                with st.spinner(text='🚧 Work in progress ... '):
                                                                    file_content = get_file_content2(cluster=optioncluster,region=optionregion,namespace=selectnamespace,pod=selectpod,do_api='threaddump_datagrid', delete=delete)
                                                                    time.sleep(15)

                                                                date = get_date()
                                                                if file_content != [{"threaddumpdatagrid": None}]:

                                                                    st.download_button(
                                                                        label="Download dump file 🔽",
                                                                        data=file_content,
                                                                        file_name=f'ThreadDump_DG-{selectpod}-{date}.gz',
                                                                        mime='application/octet-stream',
                                                                    )

                                                                else:
                                                                    st.info("There was a problem generating the threaddump. Please, try again later or report the bug to SHUTTLE_TEAM if persists")
                                                            except FileNotFoundError as e:
                                                                st.warning(f'File not found. Please check if the file exists. {e}')
                                                            except Exception as e:
                                                                st.write(f'Error downloading file: {e}')
    st.text('')
    st.text('')
    st.link_button("Help for analysis","https://sanes.atlassian.net/wiki/x/oABatAU",help="Go to documentation with tools and help to do the analysis")
    return delete