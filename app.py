import streamlit as st
import parser as dive_parser
import pandas as pd
import visualizer

st.title("🤿 DIVE ANALYZER")

uploaded_file = st.file_uploader(
    "Uploadez un fichier de plongée",
    type=['.fit', '.xml', '.uddf', '.dl7']
)

if uploaded_file is not None:
    # Afficher infos fichier
    st.success(f"✅ Fichier uploadé : {uploaded_file.name}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Nom", uploaded_file.name)
    with col2:
        st.metric("📦 Taille", f"{uploaded_file.size / 1024:.1f} KB")
    with col3:
        file_ext = uploaded_file.name.split('.')[-1]
        st.metric("🔖 Format", f".{file_ext}")

    # Parser le fichier
    with st.spinner("🔄 Parsing du fichier..."):
        try:
            df = dive_parser.parse_dive_file(uploaded_file)

            if df.empty:
                st.error("❌ Erreur : Aucune donnée extraite du fichier")
            else:
                st.success(f"✅ {len(df)} points de données extraits")

                # Afficher aperçu des données
                st.subheader("📊 Aperçu des Données Brutes")
                st.dataframe(df.head(20), use_container_width=True)

                # Stats rapides
                st.subheader("📈 Statistiques Rapides")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⬇️ Profondeur Max", f"{df['profondeur_metres'].max():.1f} m")
                with col2:
                    st.metric("⏱️ Durée", f"{df['temps_secondes'].max() / 60:.0f} min")
                with col3:
                    temp_min = df['temperature_celsius'].min()
                    if pd.notna(temp_min):
                        st.metric("🌡️ Température Min", f"{temp_min:.1f} °C")
                    else:
                        st.metric("🌡️ Température", "N/A")

                # Graphique de profondeur
                st.subheader("📊 Profil de Plongée")

                try:
                    fig = visualizer.plot_depth_profile(df)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création du graphique : {str(e)}")

        except Exception as e:
            st.error(f"❌ Erreur lors du parsing : {str(e)}")
else:
    st.info("Uploadez un fichier de plongée")
