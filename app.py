import streamlit as st
from PIL import Image

from src.scenario_page import scenario_page
from src.sensitivity_page import sensitivity_page

def main():
    st.set_page_config(
        layout='wide',
        page_title='Solar PV Optimisation Tool',
        initial_sidebar_state='collapsed',
        
    )

    header()
    
    scenario_tab, sensitivity_tab = st.tabs(['**Create a scenario**', '**Sensitivity Analysis**'])
    with scenario_tab:
        
        scenario_page()
    with sensitivity_tab:
        sensitivity_page()


def header():
    col1, col2 = st.columns((1,5))
    logo = Image.open('./img/MM-logo.jpg')
    col1.image(logo, width=120)
    col2.write("# Solar PV Pre-Feasibility Design Optimisation Tool")


if __name__ == "__main__":
    main()
