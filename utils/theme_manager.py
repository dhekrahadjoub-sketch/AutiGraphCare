# utils/theme_manager.py

import streamlit as st

def init_theme():
    """Initialise le thème dans session_state"""
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'clair'
    
    # Injecter le thème dans le HTML
    theme_js = f"""
    <script>
    const theme = "{st.session_state['theme']}";
    document.documentElement.setAttribute('data-theme', theme);
    </script>
    """
    st.markdown(theme_js, unsafe_allow_html=True)
    
    return st.session_state['theme']

def toggle_theme():
    """Change le thème"""
    if st.session_state['theme'] == 'clair':
        st.session_state['theme'] = 'dark'
    else:
        st.session_state['theme'] = 'clair'
    st.rerun()

def theme_button():
    """Affiche le bouton de changement de thème"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🌙" if st.session_state['theme'] == 'clair' else "☀️", 
                    help="Changer le thème"):
            toggle_theme()
    
    with col2:
        theme_text = "Mode sombre" if st.session_state['theme'] == 'clair' else "Mode clair"
        st.markdown(f"<p style='color: var(--text-secondary);'>{theme_text}</p>", 
                   unsafe_allow_html=True)