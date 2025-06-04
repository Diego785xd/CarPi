import streamlit as st
import streamlit.components.v1 as components

def hide_all_buttons():
  st.markdown(
    """
    <style>
    /* hide every sidebar nav-link */
    a[data-testid="stSidebarNavLink"] {
      display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
  )

def switch_page(page_name: str):
    """
    Click the sidebar nav link whose text ends with page_name (case-insensitive).
    """
    js = f"""
    <script>
    // give Streamlit a moment to render the sidebar links
    setTimeout(() => {{
      // select all the sidebar links
      const links = window.parent.document.querySelectorAll(
        'a[data-testid="stSidebarNavLink"]'
      );
      for (let link of links) {{
        // link.innerText may include emoji or nested spans, so trim & lowercase
        const txt = link.innerText.trim().toLowerCase();
        if (txt.endsWith("{page_name.lower()}")) {{
          link.click();
          return;
        }}
      }}
      console.warn("No sidebar link matching '{page_name}'");
    }}, 200);
    </script>
    """
    # Invisible component
    components.html(js, height=0)
