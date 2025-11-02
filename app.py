import streamlit as st
import parser as dive_parser
import pandas as pd
import visualizer
import analyzer


def render_reset_button() -> None:
    """Affiche un bouton pour réinitialiser l'upload."""
    if st.button("🔄 Analyser une autre plongée", use_container_width=True):
        st.rerun()


st.set_page_config(page_title="DIVE ANALYZER", page_icon="🤿", layout="wide")
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

                # === DASHBOARD KPIs ===
                st.markdown("### 📊 Vue d'Ensemble")
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    st.metric("⬇️ Profondeur Max", f"{df['profondeur_metres'].max():.1f} m")

                with col2:
                    st.metric("⏱️ Durée Totale", f"{df['temps_secondes'].max() / 60:.0f} min")

                with col3:
                    sac_result = analyzer.calculate_sac(df)
                    if sac_result and sac_result.get('sac'):
                        st.metric("🫁 SAC", f"{sac_result['sac']:.1f} L/min", help="Surface Air Consumption")
                    else:
                        st.metric("🫁 SAC", "N/A", help="Nécessite données de pression")

                with col4:
                    temp_min = df['temperature_celsius'].min()
                    if pd.notna(temp_min):
                        st.metric("🌡️ Température Min", f"{temp_min:.1f} °C")
                    else:
                        st.metric("🌡️ Température", "N/A")

                with col5:
                    bottom_time = analyzer.calculate_bottom_time(df)
                    st.metric("⏳ Temps de Fond", f"{bottom_time['temps_fond_minutes']:.1f} min", help="Temps sous 3m")

                st.divider()

                # === SECTION PROFIL ===
                st.markdown("### 🤿 Profil de Plongée")

                # Graphique
                try:
                    fig = visualizer.plot_depth_profile(df)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Erreur lors de la création du graphique : {str(e)}")

                # Bandeau sécurité SOUS le graphique (version compacte native)
                speeds = visualizer.calculate_ascent_speed(df)
                max_speed = speeds.max()
                if max_speed < 10.0:
                    st.success(f"🟢 **Plongée sécuritaire** — Vitesse remontée max : {max_speed:.1f} m/min")
                else:
                    st.error(f"🔴 **Alerte** — Vitesse remontée max : {max_speed:.1f} m/min (> 10 m/min)")

                st.divider()

                # === TABS NAVIGATION ===
                tab1, tab2 = st.tabs(["📊 Statistiques Avancées", "🔬 Physique de Décompression"])

                with tab1:
                    # Groupe 1 : Temps & Profondeur
                    st.subheader("⏱️ Temps & Profondeur")
                    bottom_time = analyzer.calculate_bottom_time(df)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Temps de fond",
                            f"{bottom_time['temps_fond_minutes']:.1f} min",
                            help="Temps passé sous 3m de profondeur"
                        )
                    with col2:
                        avg_depth = df['profondeur_metres'].mean()
                        st.metric("Profondeur moyenne", f"{avg_depth:.1f} m")

                    st.divider()

                    # Groupe 2 : Consommation Air (SAC)
                    st.subheader("🫁 Consommation Air (SAC)")

                    sac_result = analyzer.calculate_sac(df)

                    if sac_result and sac_result['mode'] == 'auto':
                        st.success("✅ Calcul automatique (données du fichier)")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("SAC", f"{sac_result['sac']:.1f} L/min")
                        with col2:
                            st.metric("Pression moyenne", f"{sac_result['pression_moyenne']:.2f} bar")
                        with col3:
                            st.metric("Volume consommé", f"{sac_result['volume_consomme']:.0f} L")
                    else:
                        st.info("ℹ️ Pas de données de pression. Saisie manuelle requise.")

                        with st.form("sac_manual"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                p_debut = st.number_input("Pression début (bar)", min_value=0, value=200, step=10)
                            with col2:
                                p_fin = st.number_input("Pression fin (bar)", min_value=0, value=50, step=10)
                            with col3:
                                v_bouteille = st.number_input("Volume bouteille (L)", min_value=0, value=12, step=1)

                            submitted = st.form_submit_button("Calculer SAC")

                            if submitted:
                                sac_result = analyzer.calculate_sac(df, p_debut, p_fin, v_bouteille)
                                if sac_result:
                                    st.success("✅ Calcul effectué")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("SAC", f"{sac_result['sac']:.1f} L/min")
                                    with col2:
                                        st.metric("Pression moyenne", f"{sac_result['pression_moyenne']:.2f} bar")
                                    with col3:
                                        st.metric("Volume consommé", f"{sac_result['volume_consomme']:.0f} L")

                    st.divider()

                    # Groupe 3 : Conditions Environnementales
                    st.subheader("🌡️ Conditions Environnementales")
                    temp_stats = analyzer.get_temperature_stats(df)
                    if temp_stats:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Température min",
                                f"{temp_stats['temp_min']:.1f}°C",
                                help=f"À {temp_stats['temp_min_time']:.1f} min"
                            )
                        with col2:
                            st.metric(
                                "Température max",
                                f"{temp_stats['temp_max']:.1f}°C",
                                help=f"À {temp_stats['temp_max_time']:.1f} min"
                            )
                    else:
                        st.info("Pas de données de température disponibles")

                with tab2:
                    # Warning plus visible
                    st.warning(
                        "⚠️ **Modèle pédagogique simplifié** (1 compartiment, demi-vie 40 min)\n\n"
                        "**Ne pas utiliser pour planification de plongées réelles.**"
                    )

                    # Calculer les métriques avancées
                    physics = analyzer.get_advanced_physics_summary(df)

                    # Afficher les métriques clés
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🧬 Saturation Tissulaire")
                        st.metric(
                            "Pression N₂ max dans tissu",
                            f"{physics['max_tissue_N2_pressure']:.2f} bar",
                            help=f"Atteint à {physics['max_tissue_N2_time']:.1f} min"
                        )
                        st.metric(
                            "Gradient N₂ max",
                            f"{physics['max_N2_gradient']:.2f} bar",
                            help=f"Différence tissu-ambiant maximale à {physics['max_N2_gradient_time']:.1f} min"
                        )

                    with col2:
                        st.subheader("💨 Azote Résiduel Post-Plongée")
                        residual = physics['residual_nitrogen']
                        st.metric(
                            "Sursaturation résiduelle",
                            f"{residual['residual_percentage']:.1f}%",
                            help="Excès d'azote vs pression normale surface"
                        )
                        st.metric(
                            "Intervalle de surface recommandé",
                            f"{residual['recommended_surface_interval_min']:.0f} min",
                            help="Temps conservatif avant prochaine plongée (3 × demi-vie)"
                        )
                        st.metric(
                            "Temps retour à 90% normal",
                            f"{residual['time_to_90_percent_desaturation_min']:.0f} min",
                            help="Temps de désaturation quasi-complète"
                        )

                    # Graphique optionnel : évolution saturation tissulaire
                    with st.expander("📈 Voir l'évolution de la saturation N₂"):
                        import plotly.graph_objects as go

                        df_physics = physics['df_enriched']
                        temps_min = df_physics['temps_secondes'] / 60

                        fig_saturation = go.Figure()

                        # Courbe PP_N2 alvéolaire (ambiant)
                        fig_saturation.add_trace(go.Scatter(
                            x=temps_min,
                            y=df_physics['PP_N2'],
                            mode='lines',
                            name='PP N₂ alvéolaire (ambiant)',
                            line=dict(color='blue', width=2)
                        ))

                        # Courbe pression tissulaire
                        fig_saturation.add_trace(go.Scatter(
                            x=temps_min,
                            y=df_physics['tissue_N2_pressure'],
                            mode='lines',
                            name='Pression N₂ tissulaire',
                            line=dict(color='red', width=2, dash='dash')
                        ))

                        fig_saturation.update_layout(
                            title='Saturation en Azote - Compartiment à 40 min',
                            xaxis_title='Temps (minutes)',
                            yaxis_title='Pression N₂ (bar)',
                            height=400,
                            hovermode='x unified'
                        )

                        st.plotly_chart(fig_saturation, use_container_width=True)

                st.divider()

                # Bouton reset en bas de page
                render_reset_button()

        except Exception as e:
            st.error(f"❌ Erreur lors du parsing : {str(e)}")
else:
    st.info("Uploadez un fichier de plongée")
