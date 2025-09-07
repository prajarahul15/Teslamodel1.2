"""
AI Agents for Tesla Financial Model with OpenAI Integration
Implements proactive insights, forecasting, and interactive analysis
"""

import pandas as pd
import numpy as np
import openai
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from models.financial_models import ScenarioType, TeslaAssumptions
from data.tesla_enhanced_data import get_enhanced_tesla_drivers, TESLA_HISTORICAL_DATA, VEHICLE_MODEL_DATA

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class ProactiveInsightsAgent:
    """AI Agent that provides proactive insights using OpenAI GPT"""
    
    def __init__(self):
        self.insights_cache = {}
        
    def analyze_financial_model(self, model_data: Dict, scenario: str) -> Dict:
        """Generate proactive insights from financial model data using OpenAI"""
        
        try:
            # Check if OpenAI API key is available
            if not os.getenv('OPENAI_API_KEY'):
                return self._get_fallback_insights(model_data, scenario)
            
            # Prepare context for OpenAI
            context = self._prepare_financial_context(model_data, scenario)
            
            # Create structured prompt for insights
            prompt = self._create_insights_prompt(context, scenario)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a senior financial analyst specializing in Tesla and EV industry analysis. Provide structured, actionable insights based on financial data."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse OpenAI response
            insights_text = response.choices[0].message.content
            insights = self._parse_insights_response(insights_text)
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            return self._get_fallback_insights(model_data, scenario)
    
    def _prepare_financial_context(self, model_data: Dict, scenario: str) -> Dict:
        """Prepare financial context for OpenAI analysis"""
        
        if not model_data or "income_statements" not in model_data:
            return {}
            
        income_statements = model_data["income_statements"]
        
        # Calculate key metrics
        context = {
            "scenario": scenario,
            "years": [2025, 2026, 2027, 2028, 2029],
            "revenue_data": [],
            "margin_data": [],
            "growth_metrics": {},
            "vehicle_data": {},
            "cash_flow_data": []
        }
        
        # Revenue analysis
        for i, stmt in enumerate(income_statements):
            context["revenue_data"].append({
                "year": 2025 + i,
                "total_revenue": stmt["total_revenue"],
                "automotive_revenue": stmt["automotive_revenue"],
                "services_revenue": stmt["services_revenue"],
                "gross_margin": stmt["gross_margin"],
                "operating_margin": stmt["operating_margin"],
                "net_margin": stmt["net_margin"]
            })
        
        # Growth calculations
        if len(income_statements) >= 2:
            first_year = income_statements[0]
            last_year = income_statements[-1]
            
            context["growth_metrics"] = {
                "revenue_cagr": ((last_year["total_revenue"] / first_year["total_revenue"]) ** (1/4)) - 1,
                "margin_improvement": last_year["gross_margin"] - first_year["gross_margin"],
                "final_revenue": last_year["total_revenue"],
                "final_margin": last_year["gross_margin"]
            }
        
        # Vehicle model data (if available)
        if "revenue_breakdown" in income_statements[-1]:
            vehicle_breakdown = income_statements[-1]["revenue_breakdown"]
            if "automotive_revenue_by_model" in vehicle_breakdown:
                context["vehicle_data"] = vehicle_breakdown["automotive_revenue_by_model"]
        
        # Cash flow data
        if "cash_flow_statements" in model_data:
            for cf in model_data["cash_flow_statements"]:
                context["cash_flow_data"].append({
                    "free_cash_flow": cf["free_cash_flow"],
                    "operating_cash_flow": cf["operating_cash_flow"]
                })
        
        return context
    
    def _create_insights_prompt(self, context: Dict, scenario: str) -> str:
        """Create structured prompt for OpenAI insights generation"""
        
        prompt = f"""
        Analyze the following Tesla financial model data for the {scenario.upper()} scenario and provide structured insights.
        
        FINANCIAL DATA:
        {json.dumps(context, indent=2)}
        
        Please provide insights in the following JSON format:
        {{
            "key_insights": [
                {{
                    "type": "growth|risk|opportunity|financial_strength|operational_efficiency|product_mix|competitive_pressure|growth_concern",
                    "title": "Brief title",
                    "description": "Detailed description with specific numbers and context",
                    "impact": "positive|negative|neutral",
                    "confidence": 0.0-1.0
                }}
            ],
            "risk_alerts": [
                {{
                    "type": "risk_type",
                    "title": "Risk title",
                    "description": "Risk description with mitigation suggestions",
                    "impact": "negative",
                    "confidence": 0.0-1.0
                }}
            ],
            "opportunities": [
                {{
                    "type": "opportunity_type",
                    "title": "Opportunity title", 
                    "description": "Opportunity description with implementation suggestions",
                    "impact": "positive",
                    "confidence": 0.0-1.0
                }}
            ],
            "recommendations": [
                {{
                    "category": "operational|strategic|financial|market",
                    "title": "Recommendation title",
                    "description": "Detailed recommendation",
                    "priority": "high|medium|low",
                    "timeline": "immediate|short-term|medium-term|long-term"
                }}
            ],
            "market_context": [
                {{
                    "factor": "Factor name",
                    "description": "Market factor description",
                    "relevance": "high|medium|low"
                }}
            ]
        }}
        
        Focus on:
        1. Revenue growth trajectory and sustainability
        2. Margin expansion opportunities and risks
        3. Vehicle model mix optimization
        4. Cash flow generation and capital allocation
        5. Competitive positioning and market dynamics
        6. Operational efficiency improvements
        7. Strategic recommendations for the {scenario} scenario
        
        Provide specific, actionable insights with concrete numbers and clear reasoning.
        """
        
        return prompt
    
    def _parse_insights_response(self, response_text: str) -> Dict:
        """Parse OpenAI response into structured insights"""
        
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing insights response: {e}")
            return self._get_fallback_insights({}, "base")
    
    def _get_fallback_insights(self, model_data: Dict, scenario: str) -> Dict:
        """Fallback insights when OpenAI fails"""
        
        return {
            "key_insights": [
                {
                    "type": "system_status",
                    "title": "AI Analysis Unavailable",
                    "description": "Unable to generate AI insights at this time. Please check OpenAI API key configuration.",
                    "impact": "neutral",
                    "confidence": 0.5
                }
            ],
            "risk_alerts": [],
            "opportunities": [],
            "recommendations": [],
            "market_context": []
        }

class ProphetForecastingAgent:
    """AI Agent for Prophet-based forecasting with OpenAI insights"""
    
    def __init__(self):
        self.models = {}
        
    def generate_prophet_forecast(self, historical_data: List[Dict], periods: int = 12) -> Dict:
        """Generate Prophet forecast with AI insights"""
        
        try:
            # Simulate Prophet forecasting (in real implementation, use actual Prophet)
            forecast_data = self._simulate_prophet_forecast(historical_data, periods)
            
            # Generate AI insights for the forecast
            insights = self._generate_forecast_insights_with_ai(forecast_data, historical_data)
            
            return {
                "forecasts": forecast_data,
                "model_info": {
                    "type": "prophet_simulation",
                    "periods": periods
                },
                "insights": insights
            }
            
        except Exception as e:
            return {"error": f"Forecast generation failed: {str(e)}"}
    
    def _simulate_prophet_forecast(self, historical_data: List[Dict], periods: int) -> List[Dict]:
        """Simulate Prophet forecasting"""
        
        forecast_data = []
        
        if not historical_data:
            return forecast_data
        
        # Get last known value and trend
        last_value = historical_data[-1]["value"]
        
        # Simple trend calculation
        if len(historical_data) >= 2:
            trend = (historical_data[-1]["value"] - historical_data[0]["value"]) / len(historical_data)
        else:
            trend = 0
        
        # Generate forecasts with seasonality and trend
        base_date = datetime.strptime(historical_data[-1]["date"], "%Y-%m-%d")
        
        for i in range(1, periods + 1):
            forecast_date = base_date + timedelta(days=30 * i)
            
            # Add trend and seasonal component
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * i / 12)  # Annual seasonality
            forecast_value = (last_value + trend * i) * seasonal_factor
            
            # Add confidence intervals
            uncertainty = forecast_value * 0.1 * (i / periods)  # Increasing uncertainty
            
            forecast_data.append({
                "date": forecast_date.strftime("%Y-%m-%d"),
                "forecast": max(0, forecast_value),
                "lower_bound": max(0, forecast_value - uncertainty),
                "upper_bound": forecast_value + uncertainty,
                "confidence": max(0.5, 0.9 - (i * 0.05))  # Decreasing confidence
            })
        
        return forecast_data
    
    def _generate_forecast_insights_with_ai(self, forecasts: List[Dict], historical: List[Dict]) -> List[Dict]:
        """Generate AI insights for forecast results"""
        
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return [{"type": "info", "description": "OpenAI API key not configured", "confidence": 0.0}]
            
            # Prepare forecast context
            context = {
                "historical_data": historical,
                "forecast_data": forecasts,
                "growth_rate": self._calculate_growth_rate(forecasts, historical)
            }
            
            prompt = f"""
            Analyze this Tesla revenue forecast and provide insights:
            
            HISTORICAL DATA: {json.dumps(historical, indent=2)}
            FORECAST DATA: {json.dumps(forecasts, indent=2)}
            
            Provide insights in JSON format:
            {{
                "insights": [
                    {{
                        "type": "growth_acceleration|decline_warning|seasonality|trend_analysis",
                        "description": "Detailed insight about the forecast",
                        "confidence": 0.0-1.0,
                        "recommendation": "Actionable recommendation"
                    }}
                ]
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial forecasting expert specializing in Tesla and EV industry trends."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            insights_text = response.choices[0].message.content
            return self._parse_forecast_insights(insights_text)
            
        except Exception as e:
            print(f"Error generating forecast insights: {e}")
            return [{"type": "error", "description": "Unable to generate forecast insights", "confidence": 0.0}]
    
    def _calculate_growth_rate(self, forecasts: List[Dict], historical: List[Dict]) -> float:
        """Calculate growth rate from forecast"""
        
        if not forecasts or not historical:
            return 0.0
        
        last_historical = historical[-1]["value"]
        last_forecast = forecasts[-1]["forecast"]
        
        return ((last_forecast / last_historical) ** (1/len(forecasts))) - 1
    
    def _parse_forecast_insights(self, response_text: str) -> List[Dict]:
        """Parse forecast insights response"""
        
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("insights", [])
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing forecast insights: {e}")
            return []

class TeslaAIAgent:
    """Interactive AI Agent for Tesla model analysis with OpenAI insights"""
    
    def __init__(self):
        self.base_assumptions = None
        self.current_scenario = "base"
        
    def initialize_base_model(self, scenario: str = "base"):
        """Initialize base model assumptions"""
        self.current_scenario = scenario
        self.base_assumptions = get_enhanced_tesla_drivers(ScenarioType(scenario), 2024)
        
        return {
            "initialized": True,
            "scenario": scenario,
            "base_deliveries": self.base_assumptions["projected_deliveries"],
            "base_asp_multiplier": self.base_assumptions["asp_multiplier"]
        }
    
    def simulate_slider_changes(self, changes: Dict[str, float]) -> Dict:
        """Simulate impact of slider changes with AI insights"""
        
        if not self.base_assumptions:
            return {"error": "Model not initialized"}
        
        # Calculate new values
        new_values = self._calculate_new_values(changes)
        
        # Calculate impacts
        impacts = self._calculate_impacts(new_values, changes)
        
        # Generate AI insights
        ai_insights = self._generate_ai_insights(changes, impacts)
        
        return {
            "scenario": self.current_scenario,
            "changes_applied": changes,
            "new_values": new_values,
            "impact_analysis": impacts,
            "ai_insights": ai_insights
        }
    
    def _calculate_new_values(self, changes: Dict[str, float]) -> Dict:
        """Calculate new values based on changes"""
        
        asp_change = changes.get("asp_change", 0)
        cost_change = changes.get("cost_change", 0)
        delivery_change = changes.get("delivery_change", 0)
        
        new_asp_multiplier = self.base_assumptions["asp_multiplier"] * (1 + asp_change / 100)
        new_cost_multiplier = 1 + cost_change / 100
        
        new_deliveries = {}
        for model, base_delivery in self.base_assumptions["projected_deliveries"].items():
            new_delivery = int(base_delivery * (1 + delivery_change / 100))
            new_deliveries[model] = new_delivery
        
        return {
            "deliveries": new_deliveries,
            "asp_multiplier": new_asp_multiplier,
            "cost_multiplier": new_cost_multiplier
        }
    
    def _calculate_impacts(self, new_values: Dict, changes: Dict[str, float]) -> Dict:
        """Calculate financial impacts"""
        
        # Revenue impact
        revenue_impact = self._calculate_revenue_impact(new_values)
        
        # Margin impact
        margin_impact = self._calculate_margin_impact(revenue_impact, new_values["cost_multiplier"])
        
        # Delivery impact
        total_delivery_change = sum(new_values["deliveries"].values()) - sum(self.base_assumptions["projected_deliveries"].values())
        
        return {
            "revenue_impact": revenue_impact,
            "margin_impact": margin_impact,
            "total_delivery_change": total_delivery_change
        }
    
    def _calculate_revenue_impact(self, new_values: Dict) -> Dict:
        """Calculate revenue impact"""
        
        base_revenue = 0
        new_revenue = 0
        
        for model, new_delivery in new_values["deliveries"].items():
            base_delivery = self.base_assumptions["projected_deliveries"][model]
            base_asp = VEHICLE_MODEL_DATA["models"][model]["base_asp"]
            
            model_base_revenue = base_delivery * base_asp * self.base_assumptions["asp_multiplier"]
            base_revenue += model_base_revenue
            
            model_new_revenue = new_delivery * base_asp * new_values["asp_multiplier"]
            new_revenue += model_new_revenue
        
        return {
            "base_revenue": base_revenue,
            "new_revenue": new_revenue,
            "absolute_change": new_revenue - base_revenue,
            "percentage_change": ((new_revenue / base_revenue) - 1) * 100 if base_revenue > 0 else 0
        }
    
    def _calculate_margin_impact(self, revenue_impact: Dict, cost_multiplier: float) -> Dict:
        """Calculate margin impact"""
        
        base_margin = 0.19  # Assume 19% base automotive margin
        base_costs = revenue_impact["base_revenue"] * (1 - base_margin)
        
        new_costs = base_costs * cost_multiplier
        new_margin = (revenue_impact["new_revenue"] - new_costs) / revenue_impact["new_revenue"] if revenue_impact["new_revenue"] > 0 else 0
        
        return {
            "base_margin": base_margin,
            "new_margin": new_margin,
            "margin_change": (new_margin - base_margin) * 100,
            "cost_impact": new_costs - base_costs
        }
    
    def _generate_ai_insights(self, changes: Dict[str, float], impacts: Dict) -> List[Dict]:
        """Generate AI insights using OpenAI"""
        
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return [{"type": "info", "title": "AI Analysis Unavailable", "description": "OpenAI API key not configured", "risk_level": "low"}]
            
            context = {
                "changes": changes,
                "impacts": impacts,
                "scenario": self.current_scenario
            }
            
            prompt = f"""
            Analyze these Tesla model changes and provide insights:
            
            CHANGES: {json.dumps(changes, indent=2)}
            IMPACTS: {json.dumps(impacts, indent=2)}
            SCENARIO: {self.current_scenario}
            
            Provide insights in JSON format:
            {{
                "insights": [
                    {{
                        "type": "pricing_strategy|competitive_pressure|production_scaling|demand_concern|cost_inflation|operational_efficiency|financial_impact",
                        "title": "Insight title",
                        "description": "Detailed description with specific numbers",
                        "recommendation": "Actionable recommendation",
                        "risk_level": "high|medium|low"
                    }}
                ]
            }}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Tesla financial analyst providing real-time insights on model changes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            insights_text = response.choices[0].message.content
            return self._parse_ai_insights(insights_text)
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return [{"type": "error", "title": "AI Analysis Unavailable", "description": "Unable to generate insights", "risk_level": "low"}]
    
    def _parse_ai_insights(self, response_text: str) -> List[Dict]:
        """Parse AI insights response"""
        
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                return data.get("insights", [])
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            print(f"Error parsing AI insights: {e}")
            return []

# Initialize global agents
proactive_insights_agent = ProactiveInsightsAgent()
prophet_forecasting_agent = ProphetForecastingAgent()
tesla_ai_agent = TeslaAIAgent()