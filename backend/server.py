from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import sys

# Add the backend directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from models.financial_models import *
from services.financial_calculator import TeslaFinancialCalculator
from services.enhanced_financial_calculator import EnhancedTeslaCalculator
from services.segment_analyzer import TeslaSegmentAnalyzer
from services.analytics_engine import AnalyticsEngine
from services.ai_agents import proactive_insights_agent, prophet_forecasting_agent, tesla_ai_agent
from data.tesla_data import generate_all_tesla_assumptions, TESLA_BASE_YEAR_DATA, MACRO_ASSUMPTIONS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
try:
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    print(f"Connected to MongoDB: {os.environ['DB_NAME']}")
except KeyError as e:
    print(f"Missing environment variable: {e}")
    # Fallback for development
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(title="Tesla Financial Model & Analytics API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize calculators
tesla_calculator = TeslaFinancialCalculator()
enhanced_calculator = EnhancedTeslaCalculator()
segment_analyzer = TeslaSegmentAnalyzer()
analytics_engine = AnalyticsEngine()

# Initialize analytics engine on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Tesla Financial Model & Analytics API started successfully")
    logger.info("Loading analytics data...")
    
    # Load analytics data
    if analytics_engine.load_data():
        logger.info("Analytics data loaded successfully")
    else:
        logger.error("Failed to load analytics data")

# AI AGENTS ENDPOINTS

class ProactiveInsightsRequest(BaseModel):
    scenario: str
    model_data: Optional[Dict] = None

@api_router.post("/ai/proactive-insights")
async def get_proactive_insights(request: ProactiveInsightsRequest):
    """Get proactive AI insights for financial model"""
    try:
        # Check if OpenAI API key is available
        if not os.getenv('OPENAI_API_KEY'):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # If no model data provided, generate it
        if not request.model_data:
            scenario_enum = ScenarioType(request.scenario.lower())
            model = tesla_calculator.build_complete_financial_model(scenario_enum)
            model_data = model.dict()
        else:
            model_data = request.model_data
        
        insights = proactive_insights_agent.analyze_financial_model(model_data, request.scenario)
        
        return {
            "success": True,
            "scenario": request.scenario,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

class ProphetForecastRequest(BaseModel):
    historical_data: List[Dict]
    periods: int = 12
    metric_name: str = "revenue"

@api_router.post("/ai/prophet-forecast")
async def generate_prophet_forecast(request: ProphetForecastRequest):
    """Generate Prophet-based forecast with AI insights"""
    try:
        if not os.getenv('OPENAI_API_KEY'):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        forecast_result = prophet_forecasting_agent.generate_prophet_forecast(
            request.historical_data, 
            request.periods
        )
        
        return {
            "success": True,
            "metric": request.metric_name,
            "forecast_result": forecast_result,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

class TeslaAIRequest(BaseModel):
    scenario: str = "base"
    changes: Dict[str, float] = {}

@api_router.post("/ai/tesla-agent/initialize")
async def initialize_tesla_ai_agent(scenario: str = "base"):
    """Initialize Tesla AI Agent with base scenario"""
    try:
        result = tesla_ai_agent.initialize_base_model(scenario)
        
        return {
            "success": True,
            "initialization": result,
            "available_sliders": {
                "asp_change": {"min": -30, "max": 30, "step": 1, "unit": "%"},
                "cost_change": {"min": -20, "max": 40, "step": 1, "unit": "%"},
                "delivery_change": {"min": -50, "max": 100, "step": 5, "unit": "%"}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing Tesla AI agent: {str(e)}")

@api_router.post("/ai/tesla-agent/simulate")
async def simulate_tesla_changes(request: TeslaAIRequest):
    """Simulate Tesla model changes with AI insights"""
    try:
        if not os.getenv('OPENAI_API_KEY'):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Initialize if not already done
        if not tesla_ai_agent.base_assumptions:
            tesla_ai_agent.initialize_base_model(request.scenario)
        
        simulation_result = tesla_ai_agent.simulate_slider_changes(request.changes)
        
        return {
            "success": True,
            "simulation": simulation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating changes: {str(e)}")

@api_router.get("/ai/tesla-agent/vehicle-models")
async def get_vehicle_models_info():
    """Get information about Tesla vehicle models for the AI agent"""
    try:
        from data.tesla_enhanced_data import VEHICLE_MODEL_DATA
        
        models_info = {}
        for model_key, model_data in VEHICLE_MODEL_DATA["models"].items():
            models_info[model_key] = {
                "name": model_data["name"],
                "segment": model_data["segment"],
                "base_asp": model_data["base_asp"],
                "max_capacity": model_data["max_capacity"],
                "growth_trajectory": model_data["growth_trajectory"]
            }
        
        return {
            "success": True,
            "vehicle_models": models_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting vehicle models: {str(e)}")

# Professional Dashboard API Endpoints

@api_router.get("/analytics/overview")
async def get_data_overview():
    """Get comprehensive data overview metrics"""
    try:
        metrics = analytics_engine.get_data_overview_metrics()
        if metrics is None:
            raise HTTPException(status_code=500, detail="Failed to calculate overview metrics")
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating overview: {str(e)}")

@api_router.get("/analytics/economic-variables")
async def get_economic_variables():
    """Get economic variables data for analysis"""
    try:
        econ_data = analytics_engine.get_economic_variables_data()
        if econ_data is None:
            raise HTTPException(status_code=500, detail="Economic variables data not available")
        
        return {
            "success": True,
            "data": econ_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting economic data: {str(e)}")

@api_router.get("/analytics/lineups")
async def get_available_lineups():
    """Get list of available lineups for forecasting"""
    try:
        if analytics_engine.sample_data is None:
            if not analytics_engine.load_data():
                raise HTTPException(status_code=500, detail="Failed to load data")
        
        lineups = analytics_engine.sample_data['Lineup'].unique().tolist()
        
        # Get metadata for each lineup
        lineup_metadata = []
        for lineup in lineups:
            lineup_data = analytics_engine.sample_data[analytics_engine.sample_data['Lineup'] == lineup]
            lineup_metadata.append({
                'lineup': lineup,
                'profile': lineup_data['Profile'].iloc[0],
                'line_item': lineup_data['Line_Item'].iloc[0],
                'records': int(len(lineup_data)),
                'date_range': {
                    'start': lineup_data['DATE'].min().strftime('%Y-%m-%d'),
                    'end': lineup_data['DATE'].max().strftime('%Y-%m-%d')
                },
                'total_actual': int(lineup_data['Actual'].sum()),
                'total_plan': int(lineup_data['Plan'].sum())
            })
        
        return {
            "success": True,
            "lineups": lineup_metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting lineups: {str(e)}")

class ForecastRequest(BaseModel):
    lineup: str
    forecast_type: str  # 'univariate' or 'multivariate'
    months_ahead: int = 12

@api_router.post("/analytics/forecast")
async def generate_forecast(request: ForecastRequest):
    """Generate forecast for specified lineup and type"""
    try:
        if request.forecast_type not in ['univariate', 'multivariate']:
            raise HTTPException(status_code=400, detail="Forecast type must be 'univariate' or 'multivariate'")
        
        if request.months_ahead < 1 or request.months_ahead > 24:
            raise HTTPException(status_code=400, detail="Months ahead must be between 1 and 24")
        
        # Ensure data is loaded
        if analytics_engine.sample_data is None:
            if not analytics_engine.load_data():
                raise HTTPException(status_code=500, detail="Failed to load data")
        
        # Check if lineup exists
        available_lineups = analytics_engine.sample_data['Lineup'].unique()
        if request.lineup not in available_lineups:
            raise HTTPException(status_code=400, detail=f"Lineup {request.lineup} not found. Available: {list(available_lineups)}")
        
        # Generate forecast
        forecast_result = analytics_engine.generate_forecast(
            request.lineup, 
            request.forecast_type, 
            request.months_ahead
        )
        
        if forecast_result is None:
            raise HTTPException(status_code=500, detail="Failed to generate forecast")
        
        return {
            "success": True,
            "forecast": forecast_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

class CompareRequest(BaseModel):
    lineup: str
    months_ahead: int = 12

@api_router.post("/analytics/compare-forecasts")
async def compare_forecasts(request: CompareRequest):
    """Compare univariate vs multivariate forecasting methods"""
    try:
        # Ensure data is loaded
        if analytics_engine.sample_data is None:
            if not analytics_engine.load_data():
                raise HTTPException(status_code=500, detail="Failed to load data")
        
        # Check if lineup exists
        available_lineups = analytics_engine.sample_data['Lineup'].unique()
        if request.lineup not in available_lineups:
            raise HTTPException(status_code=400, detail=f"Lineup {request.lineup} not found")
        
        # Generate comparison
        comparison_result = analytics_engine.compare_forecast_methods(
            request.lineup, 
            request.months_ahead
        )
        
        if comparison_result is None:
            raise HTTPException(status_code=500, detail="Failed to generate forecast comparison")
        
        return {
            "success": True,
            "comparison": comparison_result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing forecasts: {str(e)}")

@api_router.get("/tesla/test-enhanced")
async def test_enhanced_features():
    """Test enhanced features"""
    try:
        # Test basic enhanced calculator functionality
        from data.tesla_enhanced_data import get_enhanced_tesla_drivers
        
        drivers = get_enhanced_tesla_drivers(ScenarioType.BASE, 2024)
        
        return {
            "success": True,
            "message": "Enhanced features working",
            "sample_data": {
                "scenario": drivers["scenario"].value,
                "year": drivers["year"],
                "projected_deliveries": {k: int(v) for k, v in drivers["projected_deliveries"].items()},
                "energy_growth_rate": float(drivers["energy_growth_rate"])
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Enhanced Tesla Financial Model Endpoints (PHASE 1-3)

@api_router.post("/tesla/enhanced-model/{scenario}")
async def generate_enhanced_financial_model(scenario: str):
    """Generate enhanced financial model with driver-based calculations"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
        
        # Store in database if available (create a copy to avoid ObjectId issues)
        if db is not None:
            try:
                import copy
                model_copy = copy.deepcopy(model)
                await db.enhanced_financial_models.insert_one(model_copy)
            except Exception as e:
                print(f"Database insert error: {e}")
        
        return {
            "success": True,
            "message": f"Enhanced financial model generated for {scenario} scenario",
            "model": model
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario. Use 'best', 'base', or 'worst'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating enhanced model: {str(e)}")

@api_router.get("/tesla/enhanced-comparison")
async def get_enhanced_scenario_comparison():
    """Enhanced scenario comparison with vehicle models and 10-year forecasts"""
    try:
        enhanced_models = {}
        for scenario in ["best", "base", "worst"]:
            scenario_enum = ScenarioType(scenario)
            model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
            enhanced_models[scenario] = model
        
        # Create enhanced comparison
        comparison = {
            "revenue_comparison": {},
            "valuation_comparison": {},
            "vehicle_model_comparison": {},
            "segment_comparison": {}
        }
        
        for scenario, model in enhanced_models.items():
            # Final year projections (2033)
            final_income = model["income_statements"][-1]
            dcf = model["dcf_valuation"]
            
            comparison["revenue_comparison"][scenario] = {
                "final_year_revenue": final_income["total_revenue"],
                "automotive_revenue": final_income["automotive_revenue"],
                "energy_revenue": final_income["energy_revenue"],
                "services_revenue": final_income["services_revenue"],
                "10yr_cagr": ((final_income["total_revenue"] / TESLA_BASE_YEAR_DATA["total_revenue"]) ** (1/10)) - 1
            }
            
            comparison["valuation_comparison"][scenario] = {
                "price_per_share": dcf["price_per_share"],
                "enterprise_value": dcf["enterprise_value"],
                "wacc": dcf["wacc"]
            }
            
            # Vehicle model breakdown for final year
            vehicle_breakdown = final_income["revenue_breakdown"]["automotive_revenue_by_model"]
            comparison["vehicle_model_comparison"][scenario] = vehicle_breakdown
            
            # Segment analysis
            comparison["segment_comparison"][scenario] = {
                "automotive_margin": final_income["margins"]["automotive_margin"],
                "energy_margin": final_income["margins"]["energy_margin"],
                "services_margin": final_income["margins"]["services_margin"]
            }
        
        return {
            "success": True,
            "enhanced_models": enhanced_models,
            "comparison_summary": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/vehicle-analysis/{scenario}")
async def get_vehicle_model_analysis(scenario: str):
    """PHASE 1: Detailed vehicle model analysis"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
        
        vehicle_analysis = {
            "scenario": scenario,
            "vehicle_trends": {},
            "model_performance": {},
            "delivery_projections": {}
        }
        
        # Extract vehicle data for all years
        for income_stmt in model["income_statements"]:
            year = income_stmt["year"]
            vehicle_data = income_stmt["revenue_breakdown"]["automotive_revenue_by_model"]
            
            vehicle_analysis["vehicle_trends"][year] = vehicle_data
        
        # Calculate model performance metrics
        for model_key in vehicle_analysis["vehicle_trends"][2024]:
            initial_year_data = vehicle_analysis["vehicle_trends"][2024][model_key]
            final_year_data = vehicle_analysis["vehicle_trends"][2033][model_key]
            
            delivery_cagr = ((final_year_data["deliveries"] / initial_year_data["deliveries"]) ** (1/9)) - 1 if initial_year_data["deliveries"] > 0 else 0
            revenue_cagr = ((final_year_data["revenue"] / initial_year_data["revenue"]) ** (1/9)) - 1 if initial_year_data["revenue"] > 0 else 0
            
            vehicle_analysis["model_performance"][model_key] = {
                "delivery_cagr": delivery_cagr,
                "revenue_cagr": revenue_cagr,
                "initial_deliveries": initial_year_data["deliveries"],
                "final_deliveries": final_year_data["deliveries"],
                "initial_asp": initial_year_data["asp"],
                "final_asp": final_year_data["asp"],
                "asp_trend": (final_year_data["asp"] / initial_year_data["asp"]) - 1 if initial_year_data["asp"] > 0 else 0
            }
        
        return {
            "success": True,
            "vehicle_analysis": vehicle_analysis
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/segment-analysis")
async def get_business_segment_analysis():
    """PHASE 2: Business segment analysis across all scenarios"""
    try:
        enhanced_models = {}
        for scenario in ["best", "base", "worst"]:
            scenario_enum = ScenarioType(scenario)
            model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
            enhanced_models[scenario] = model
        
        segment_analysis = segment_analyzer.analyze_business_segments(enhanced_models)
        
        return {
            "success": True,
            "segment_analysis": segment_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/bridge-analysis/{scenario}")
async def get_bridge_analysis(scenario: str):
    """PHASE 3: Bridge analysis (waterfall charts)"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
        
        # Calculate revenue bridge from first to last year
        income_statements = model["income_statements"]
        
        if len(income_statements) >= 2:
            base_year_data = income_statements[0]
            final_year_data = income_statements[-1]
            
            revenue_bridge = segment_analyzer.calculate_revenue_bridge(base_year_data, final_year_data)
            
            # Cash flow bridge
            dcf_data = model["dcf_valuation"]
            if dcf_data["projected_free_cash_flows"]:
                base_fcf = dcf_data["projected_free_cash_flows"][0]
                final_fcf = dcf_data["projected_free_cash_flows"][-1]
                cash_flow_bridge = segment_analyzer.calculate_cash_flow_bridge(base_fcf, final_fcf, income_statements)
            else:
                cash_flow_bridge = {}
            
            return {
                "success": True,
                "scenario": scenario,
                "revenue_bridge": revenue_bridge,
                "cash_flow_bridge": cash_flow_bridge
            }
        else:
            raise HTTPException(status_code=400, detail="Insufficient data for bridge analysis")
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/price-volume-mix")
async def get_price_volume_mix_analysis():
    """PHASE 3: Price-Volume-Mix analysis"""
    try:
        enhanced_models = {}
        for scenario in ["best", "base", "worst"]:
            scenario_enum = ScenarioType(scenario)
            model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
            enhanced_models[scenario] = model
        
        pvm_analysis = segment_analyzer.analyze_price_volume_mix(enhanced_models)
        
        return {
            "success": True,
            "price_volume_mix_analysis": pvm_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/comprehensive-analysis")
async def get_comprehensive_analysis():
    """Complete analysis combining all Phase 1-3 features"""
    try:
        enhanced_models = {}
        for scenario in ["best", "base", "worst"]:
            scenario_enum = ScenarioType(scenario)
            model = enhanced_calculator.build_enhanced_financial_model(scenario_enum)
            enhanced_models[scenario] = model
        
        comprehensive_analysis = segment_analyzer.generate_comprehensive_analysis(enhanced_models)
        
        return {
            "success": True,
            "comprehensive_analysis": comprehensive_analysis,
            "model_features": [
                "10-year forecasts (2024-2033)",
                "Vehicle model granularity (6 models)",
                "Driver-based revenue calculations",
                "Business segment analysis (Automotive/Energy/Services)",
                "Enhanced DCF with sensitivity analysis",
                "Working capital modeling",
                "Bridge analysis (Revenue/Cash Flow)",
                "Price-Volume-Mix analytics"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/overview")
async def get_tesla_overview():
    """Get Tesla overview data and market assumptions"""
    return {
        "tesla_base_data": TESLA_BASE_YEAR_DATA,
        "macro_assumptions": MACRO_ASSUMPTIONS,
        "model_description": "Tesla 5-Year Financial Model (2025-2029) with DCF Valuation",
        "scenarios": ["best", "base", "worst"],
        "forecast_years": [2025, 2026, 2027, 2028, 2029]
    }

@api_router.get("/tesla/assumptions/{scenario}")
async def get_scenario_assumptions(scenario: str):
    """Get all assumptions for a specific scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        assumptions = []
        
        for year in [2025, 2026, 2027, 2028, 2029]:
            from data.tesla_data import get_tesla_assumptions
            assumption_dict = get_tesla_assumptions(scenario_enum, year)
            assumptions.append(assumption_dict)
        
        return {
            "scenario": scenario,
            "assumptions": assumptions
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario. Use 'best', 'base', or 'worst'")

@api_router.post("/tesla/model/{scenario}")
async def generate_financial_model(scenario: str):
    """Generate complete financial model for scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        # Store in database if available
        if db is not None:
            try:
                await db.financial_models.insert_one(model.dict())
            except Exception as e:
                print(f"Database insert error: {e}")
        
        return {
            "success": True,
            "message": f"Financial model generated for {scenario} scenario",
            "model": model.dict()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario. Use 'best', 'base', or 'worst'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating model: {str(e)}")

@api_router.get("/tesla/model/{scenario}/income-statement")
async def get_income_statements(scenario: str):
    """Get income statements for all years in scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        income_statements = [stmt.dict() for stmt in model.income_statements]
        
        return {
            "scenario": scenario,
            "income_statements": income_statements
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/model/{scenario}/balance-sheet")
async def get_balance_sheets(scenario: str):
    """Get balance sheets for all years in scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        balance_sheets = [bs.dict() for bs in model.balance_sheets]
        
        return {
            "scenario": scenario,
            "balance_sheets": balance_sheets
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/model/{scenario}/cash-flow")
async def get_cash_flows(scenario: str):
    """Get cash flow statements for all years in scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        cash_flows = [cf.dict() for cf in model.cash_flow_statements]
        
        return {
            "scenario": scenario,
            "cash_flow_statements": cash_flows
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/model/{scenario}/dcf-valuation")
async def get_dcf_valuation(scenario: str):
    """Get DCF valuation for scenario"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        return {
            "scenario": scenario,
            "dcf_valuation": model.dcf_valuation.dict()
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/comparison")
async def get_scenario_comparison():
    """Compare all three scenarios side by side"""
    try:
        models = {}
        for scenario in ["best", "base", "worst"]:
            scenario_enum = ScenarioType(scenario)
            model = tesla_calculator.build_complete_financial_model(scenario_enum)
            models[scenario] = model.dict()
        
        # Create comparison summary
        comparison = {
            "revenue_comparison": {},
            "valuation_comparison": {},
            "margin_comparison": {}
        }
        
        for scenario, model in models.items():
            # 2029 projections
            final_income = model["income_statements"][-1]
            dcf = model["dcf_valuation"]
            
            comparison["revenue_comparison"][scenario] = {
                "2029_revenue": final_income["total_revenue"],
                "5yr_cagr": ((final_income["total_revenue"] / TESLA_BASE_YEAR_DATA["total_revenue"]) ** (1/5)) - 1
            }
            
            comparison["valuation_comparison"][scenario] = {
                "price_per_share": dcf["price_per_share"],
                "enterprise_value": dcf["enterprise_value"],
                "wacc": dcf["wacc"]
            }
            
            comparison["margin_comparison"][scenario] = {
                "2029_gross_margin": final_income["gross_margin"],
                "2029_operating_margin": final_income["operating_margin"],
                "2029_net_margin": final_income["net_margin"]
            }
        
        return {
            "success": True,
            "models": models,
            "comparison_summary": comparison
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/tesla/update-assumption")
async def update_assumption(update: ModelInput):
    """Update a specific assumption and recalculate model"""
    try:
        # This would be more complex in a real system with persistent storage
        # For now, we'll return the instruction on how this would work
        return {
            "success": True,
            "message": f"Would update {update.field_name} to {update.field_value} for {update.scenario} {update.year}",
            "note": "Real-time updates would require storing model state and recalculating affected statements"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tesla/sensitivity/{scenario}")
async def get_sensitivity_analysis(scenario: str):
    """Get detailed sensitivity analysis for DCF valuation"""
    try:
        scenario_enum = ScenarioType(scenario.lower())
        model = tesla_calculator.build_complete_financial_model(scenario_enum)
        
        dcf = model.dcf_valuation
        
        return {
            "scenario": scenario,
            "base_valuation": dcf.price_per_share,
            "sensitivity_analysis": {
                "growth_rates": dcf.sensitivity_growth_rates,
                "wacc_rates": dcf.sensitivity_wacc_rates,
                "price_matrix": dcf.sensitivity_matrix
            },
            "key_assumptions": {
                "terminal_growth_rate": dcf.terminal_growth_rate,
                "wacc": dcf.wacc,
                "final_year_fcf": dcf.projected_free_cash_flows[-1]
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Original status check endpoints (keeping for compatibility)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.get("/")
async def root():
    return {"message": "Tesla Financial Model & Analytics API - Ready for Analysis"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    if db is not None:
        try:
            await db.status_checks.insert_one(status_obj.dict())
        except Exception as e:
            print(f"Database insert error: {e}")
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if db is not None:
        try:
            status_checks = await db.status_checks.find().to_list(1000)
            return [StatusCheck(**status_check) for status_check in status_checks]
        except Exception as e:
            print(f"Database query error: {e}")
    return []

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    if client:
        client.close()