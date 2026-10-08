-- ============================================================================
-- Migration: 013_indexes_and_triggers.sql
-- Project: KrishiBondhu Bangladesh
-- Description: Automated timestamp triggers and performance optimization indexes
--              (B-Tree on FKs, GIST on PostGIS Geometries, GIN on JSONB) across
--              all active and roadmap schemas.
-- ============================================================================

-- ============================================================================
-- 1. AUTOMATED UPDATED_AT TRIGGER FUNCTION
-- ============================================================================

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to auth schema tables
CREATE TRIGGER trigger_auth_roles_updated_at BEFORE UPDATE ON auth.roles FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_auth_users_updated_at BEFORE UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_auth_consent_types_updated_at BEFORE UPDATE ON auth.consent_types FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to geo schema tables
CREATE TRIGGER trigger_geo_divisions_updated_at BEFORE UPDATE ON geo.divisions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_geo_districts_updated_at BEFORE UPDATE ON geo.districts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_geo_upazilas_updated_at BEFORE UPDATE ON geo.upazilas FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_geo_unions_updated_at BEFORE UPDATE ON geo.unions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to catalog schema tables
CREATE TRIGGER trigger_catalog_crops_updated_at BEFORE UPDATE ON catalog.crops FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_catalog_crop_varieties_updated_at BEFORE UPDATE ON catalog.crop_varieties FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_catalog_growth_stages_updated_at BEFORE UPDATE ON catalog.growth_stages FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_catalog_issues_updated_at BEFORE UPDATE ON catalog.issues FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_catalog_remedies_updated_at BEFORE UPDATE ON catalog.remedies FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to farm schema tables
CREATE TRIGGER trigger_farm_plots_updated_at BEFORE UPDATE ON farm.plots FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_farm_plot_crops_updated_at BEFORE UPDATE ON farm.plot_crops FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to system schema tables
CREATE TRIGGER trigger_system_files_updated_at BEFORE UPDATE ON system.files FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to case_mgmt schema tables
CREATE TRIGGER trigger_case_mgmt_diagnosis_cases_updated_at BEFORE UPDATE ON case_mgmt.diagnosis_cases FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_case_mgmt_expert_profiles_updated_at BEFORE UPDATE ON case_mgmt.expert_profiles FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_case_mgmt_expert_reviews_updated_at BEFORE UPDATE ON case_mgmt.expert_reviews FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to ai schema tables
CREATE TRIGGER trigger_ai_models_updated_at BEFORE UPDATE ON ai.models FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to advisory schema tables
CREATE TRIGGER trigger_advisory_templates_updated_at BEFORE UPDATE ON advisory.templates FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_advisory_advisories_updated_at BEFORE UPDATE ON advisory.advisories FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to climate schema tables
CREATE TRIGGER trigger_climate_weather_forecasts_updated_at BEFORE UPDATE ON climate.weather_forecasts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_climate_weather_alerts_updated_at BEFORE UPDATE ON climate.weather_alerts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_climate_crop_climate_advisories_updated_at BEFORE UPDATE ON climate.crop_climate_advisories FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Apply updated_at trigger to market schema tables
CREATE TRIGGER trigger_market_markets_updated_at BEFORE UPDATE ON market.markets FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_market_daily_prices_updated_at BEFORE UPDATE ON market.daily_prices FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_market_group_selling_offers_updated_at BEFORE UPDATE ON market.group_selling_offers FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
CREATE TRIGGER trigger_market_offer_participants_updated_at BEFORE UPDATE ON market.offer_participants FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


-- ============================================================================
-- 2. FOREIGN KEY B-TREE INDEXES
-- ============================================================================

-- auth schema
CREATE INDEX IF NOT EXISTS idx_auth_users_role_id ON auth.users(role_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_division_id ON auth.users(division_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_district_id ON auth.users(district_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_upazila_id ON auth.users(upazila_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_union_id ON auth.users(union_id);
CREATE INDEX IF NOT EXISTS idx_auth_user_consents_user_id ON auth.user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_user_consents_type_id ON auth.user_consents(consent_type_id);

-- geo schema
CREATE INDEX IF NOT EXISTS idx_geo_districts_division_id ON geo.districts(division_id);
CREATE INDEX IF NOT EXISTS idx_geo_upazilas_district_id ON geo.upazilas(district_id);
CREATE INDEX IF NOT EXISTS idx_geo_unions_upazila_id ON geo.unions(upazila_id);

-- catalog schema
CREATE INDEX IF NOT EXISTS idx_catalog_varieties_crop_id ON catalog.crop_varieties(crop_id);
CREATE INDEX IF NOT EXISTS idx_catalog_growth_stages_crop_id ON catalog.growth_stages(crop_id);
CREATE INDEX IF NOT EXISTS idx_catalog_issues_crop_id ON catalog.issues(crop_id);
CREATE INDEX IF NOT EXISTS idx_catalog_issue_stages_issue_id ON catalog.issue_growth_stages(issue_id);
CREATE INDEX IF NOT EXISTS idx_catalog_issue_stages_stage_id ON catalog.issue_growth_stages(growth_stage_id);
CREATE INDEX IF NOT EXISTS idx_catalog_remedies_issue_id ON catalog.remedies(issue_id);

-- farm schema
CREATE INDEX IF NOT EXISTS idx_farm_plots_user_id ON farm.plots(user_id);
CREATE INDEX IF NOT EXISTS idx_farm_plot_crops_plot_id ON farm.plot_crops(plot_id);
CREATE INDEX IF NOT EXISTS idx_farm_plot_crops_crop_id ON farm.plot_crops(crop_id);
CREATE INDEX IF NOT EXISTS idx_farm_plot_crops_variety_id ON farm.plot_crops(variety_id);

-- system schema
CREATE INDEX IF NOT EXISTS idx_system_files_uploaded_by ON system.files(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_system_files_entity ON system.files(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_system_audit_logs_user_id ON system.audit_logs(user_id);

-- case_mgmt schema
CREATE INDEX IF NOT EXISTS idx_case_mgmt_cases_farmer_id ON case_mgmt.diagnosis_cases(farmer_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_cases_crop_id ON case_mgmt.diagnosis_cases(crop_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_cases_status ON case_mgmt.diagnosis_cases(status);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_cases_expert_id ON case_mgmt.diagnosis_cases(assigned_expert_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_case_images_case_id ON case_mgmt.case_images(case_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_assignments_case_id ON case_mgmt.case_assignments(case_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_assignments_expert_id ON case_mgmt.case_assignments(expert_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_reviews_case_id ON case_mgmt.expert_reviews(case_id);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_reviews_expert_id ON case_mgmt.expert_reviews(expert_id);

-- ai schema
CREATE INDEX IF NOT EXISTS idx_ai_predictions_case_id ON ai.predictions(case_id);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_model_id ON ai.predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_ai_prediction_details_pred_id ON ai.prediction_details(prediction_id);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_prediction_id ON ai.model_feedback(prediction_id);

-- advisory schema
CREATE INDEX IF NOT EXISTS idx_advisory_templates_issue_id ON advisory.templates(issue_id);
CREATE INDEX IF NOT EXISTS idx_advisory_advisories_case_id ON advisory.advisories(case_id);
CREATE INDEX IF NOT EXISTS idx_advisory_feedbacks_advisory_id ON advisory.feedbacks(advisory_id);

-- climate schema
CREATE INDEX IF NOT EXISTS idx_climate_weather_location ON climate.weather_forecasts(upazila_id, union_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_climate_alerts_active ON climate.weather_alerts(is_active, start_time, end_time);

-- market schema
CREATE INDEX IF NOT EXISTS idx_market_prices_market_crop ON market.daily_prices(market_id, crop_id, price_date);
CREATE INDEX IF NOT EXISTS idx_market_offers_crop_status ON market.group_selling_offers(crop_id, status);
CREATE INDEX IF NOT EXISTS idx_market_participants_offer_id ON market.offer_participants(offer_id);


-- ============================================================================
-- 3. POSTGIS SPATIAL GIST INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_geo_divisions_coords_gist ON geo.divisions USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_geo_divisions_boundary_gist ON geo.divisions USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_geo_districts_coords_gist ON geo.districts USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_geo_districts_boundary_gist ON geo.districts USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_geo_upazilas_coords_gist ON geo.upazilas USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_geo_upazilas_boundary_gist ON geo.upazilas USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_geo_unions_coords_gist ON geo.unions USING GIST(coordinates);
CREATE INDEX IF NOT EXISTS idx_geo_unions_boundary_gist ON geo.unions USING GIST(boundary);

CREATE INDEX IF NOT EXISTS idx_farm_plots_location_gist ON farm.plots USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_farm_plots_boundary_gist ON farm.plots USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_case_mgmt_cases_location_gist ON case_mgmt.diagnosis_cases USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_market_markets_location_gist ON market.markets USING GIST(location);


-- ============================================================================
-- 4. JSONB GIN INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_system_audit_old_data_gin ON system.audit_logs USING GIN(old_data);
CREATE INDEX IF NOT EXISTS idx_system_audit_new_data_gin ON system.audit_logs USING GIN(new_data);
CREATE INDEX IF NOT EXISTS idx_ai_predictions_raw_resp_gin ON ai.predictions USING GIN(raw_response);
CREATE INDEX IF NOT EXISTS idx_climate_weather_raw_gin ON climate.weather_forecasts USING GIN(raw_forecast_data);
