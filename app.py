"""Free citation-first metabolic medicine reference search."""
import os
import re
import html
from urllib.parse import quote
import requests
import fitz
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title='Metabolic Medicine Reference Assistant', page_icon='🧬', layout='wide')
st.title('🧬 Metabolic Medicine Reference Assistant')
st.caption('Free source discovery • PDF textbooks • PubMed • GeneReviews • Orphanet')
st.warning('Research aid only. Verify original sources, page numbers, and clinical recommendations. Do not upload identifiable patient information.')

@st.cache_data(show_spinner=False, max_entries=20)
def extract_pdf(data: bytes, name: str):
    passages=[]
    with fitz.open(stream=data, filetype='pdf') as pdf:
        for page_number, page in enumerate(pdf, 1):
            txt=' '.join(page.get_text('text').split())
            for start in range(0,len(txt),850):
                part=txt[start:start+1100]
                if len(part)>=40:
                    passages.append({'name':name,'page':page_number,'text':part})
    return passages

def pdf_search(query, passages, limit=8):
    if not passages:return []
    try:
        matrix=TfidfVectorizer(stop_words='english',ngram_range=(1,2),max_features=45000).fit_transform([query]+[p['text'] for p in passages])
        scores=cosine_similarity(matrix[0:1],matrix[1:]).ravel()
        ids=sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)
        return [(passages[i],float(scores[i])) for i in ids[:limit] if scores[i]>0]
    except ValueError:return []

@st.cache_data(ttl=3600,show_spinner=False)
def ncbi_search(term,db):
    base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    params={'db':db,'term':term,'retmode':'json','retmax':6,'tool':'metabolic_reference_assistant'}
    if os.getenv('NCBI_EMAIL'):params['email']=os.getenv('NCBI_EMAIL')
    s=requests.Session()
    s.headers.update({'User-Agent':'MetabolicMedicineReferenceAssistant/1.0 research tool'})
    r=s.get(base+'esearch.fcgi',params=params,timeout=15);r.raise_for_status()
    ids=r.json().get('esearchresult',{}).get('idlist',[])
    if not ids:return []
    r=s.get(base+'esummary.fcgi',params={'db':db,'id':','.join(ids),'retmode':'json'},timeout=15);r.raise_for_status()
    results=r.json().get('result',{})
    out=[]
    for uid in ids:
        item=results.get(uid,{})
        title=html.unescape(re.sub('<[^>]*>','',item.get('title','Untitled')))
        if db=='pubmed':
            url=f'https://pubmed.ncbi.nlm.nih.gov/{uid}/'
            meta=f"PMID {uid} · {item.get('pubdate','')} · {item.get('source','')}"
        else:
            accession=item.get('accession','')
            url=f'https://www.ncbi.nlm.nih.gov/books/{accession}/' if accession.startswith('NBK') else f'https://www.ncbi.nlm.nih.gov/books/?term={quote(title)}'
            meta=f'NCBI Bookshelf · {accession or uid}'
        out.append((title,url,meta))
    return out

password=os.getenv('ACCESS_PASSWORD','')
if password:
    supplied=st.sidebar.text_input('Access password',type='password')
    if supplied!=password:
        st.info('Enter the access password in the sidebar to continue.')
        st.stop()

if 'library' not in st.session_state:st.session_state.library={}
with st.sidebar:
    st.header('📚 PDF library')
    uploads=st.file_uploader('Upload searchable PDF books',type=['pdf'],accept_multiple_files=True)
    if st.button('Index uploaded PDFs',type='primary'):
        for file in uploads or []:
            if file.size>35*1024*1024:
                st.error(f'{file.name}: exceeds 35 MB per-file demo limit')
                continue
            try:
                data=file.getvalue()
                extracted=extract_pdf(data,file.name)
                if not extracted:st.warning(f'{file.name}: no selectable text; OCR required')
                else:
                    st.session_state.library[file.name]={'bytes':data,'passages':extracted}
                    st.success(f'{file.name}: {len(extracted)} passages indexed')
            except Exception as e:st.error(f'{file.name}: {type(e).__name__}')
    st.caption('Files are held in this browser session, not permanently stored. Do not share licensed books without permission.')
    for name,entry in st.session_state.library.items():st.write(f'📖 {name} ({len(entry["passages"])} passages)')
    if st.button('Clear session library'):st.session_state.library={};st.rerun()

query=st.text_input('Clinical or scientific search question',placeholder='OTC deficiency hyperammonemia management')
col1,col2=st.columns(2)
with col1:pubmed=st.checkbox('Search PubMed',value=True)
with col2:gene=st.checkbox('Search GeneReviews',value=True)
if st.button('🔎 Search references',type='primary'):
    if not query.strip():st.warning('Enter a search question.')
    else:
        passages=[p for book in st.session_state.library.values() for p in book['passages']]
        st.subheader('📚 Textbook excerpts')
        matches=pdf_search(query,passages)
        if not matches:st.info('No matching PDF passages. Upload a text-based PDF or try other terms.')
        for idx,(p,score) in enumerate(matches,1):
            with st.expander(f'[{idx}] {p["name"]} · PDF page {p["page"]} · relevance {score:.2f}',expanded=idx<=2):
                st.write(p['text'])
                st.caption('PDF page position, not verified printed book page.')
                data=st.session_state.library[p['name']]['bytes']
                st.download_button('Download source PDF to open cited page',data=data,file_name=p['name'],mime='application/pdf',key=f'dl-{idx}')
        if pubmed:
            st.subheader('🔬 PubMed (bibliographic records)')
            try:
                records=ncbi_search(query,'pubmed')
                if not records:st.info('No matching records.')
                for title,url,meta in records:st.markdown(f'**[{title}]({url})**  \n{meta}')
            except requests.RequestException:st.warning('PubMed is temporarily unavailable.')
        if gene:
            st.subheader('🧬 GeneReviews (NCBI Bookshelf)')
            try:
                records=ncbi_search(query+' AND GeneReviews[book]','books')
                if not records:st.info('No matching records from NCBI Bookshelf.')
                for title,url,meta in records:st.markdown(f'**[{title}]({url})**  \n{meta}')
            except requests.RequestException:st.warning('GeneReviews lookup is temporarily unavailable.')
        st.subheader('🌐 Orphanet')
        st.link_button('Open Orphanet for manual search','https://www.orpha.net/')
        st.caption('This app retrieves passages and bibliographic records. It does not generate or verify treatment recommendations, search full paywalled articles, or persist uploaded books.')
