import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ScenarioTabs from './ScenarioTabs';
import FinancialStatements from './FinancialStatements';
import DCFValuation from './DCFValuation';
import ScenarioComparison from './ScenarioComparison';
import DataOverview from './DataOverview';
import ForecastPage from './ForecastPage';
import { VehicleModelAnalysis, BusinessSegmentAnalysis, BridgeAnalysis } from './EnhancedTeslaComponents';
import LoadingSpinner from './LoadingSpinner';
import ProactiveInsights from './ProactiveInsights';
import TeslaAIAgent from './TeslaAIAgent';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TeslaDashboard = () => {
  const [activeScenario, setActiveScenario] = useState('base');
  const [teslaData, setTeslaData] = useState(null);
  const [financialModels, setFinancialModels] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchTeslaOverview();
  }, []);

  const fetchTeslaOverview = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/tesla/overview`);
      setTeslaData(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch Tesla overview data');
      setLoading(false);
    }
  };

  const generateFinancialModel = async (scenario) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post(`${API}/tesla/model/${scenario}`);
      
      if (response.data.success) {
        setFinancialModels(prev => ({
          ...prev,
          [scenario]: response.data.model
        }));
        console.log(`✅ Generated ${scenario} model successfully:`, response.data.model);
      } else {
        setError(`Failed to generate ${scenario} scenario model`);
      }
      setLoading(false);
    } catch (err) {
      console.error(`❌ Error generating ${scenario} model:`, err);
      setError(`Failed to generate ${scenario} scenario model: ${err.message}`);
      setLoading(false);
    }
  };

  const generateAllScenarios = async () => {
    setLoading(true);
    setError(null);
    try {
      const scenarios = ['best', 'base', 'worst'];
      
      // Generate scenarios sequentially to avoid overwhelming the backend
      for (const scenario of scenarios) {
        console.log(`Generating ${scenario} scenario...`);
        await generateFinancialModel(scenario);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Small delay between requests
      }
      
      console.log('✅ All scenarios generated successfully');
    } catch (err) {
      console.error('❌ Failed to generate all scenarios:', err);
      setError('Failed to generate all scenarios');
    }
    setLoading(false);
  };

  if (loading && !teslaData) {
    return <LoadingSpinner message="Loading Tesla Financial Model..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Tesla Financial Model & Analytics</h1>
              <p className="text-sm text-gray-600 mt-1">Enhanced with Phase 1-3: Vehicle Models, 10-Year Forecasts, Segment Analysis & Bridge Charts</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => generateFinancialModel(activeScenario)}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Generate {activeScenario.charAt(0).toUpperCase() + activeScenario.slice(1)} Model
              </button>
              <button
                onClick={generateAllScenarios}
                className="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Generate All Scenarios
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tesla Overview */}
        {teslaData && (
          <div className="bg-white rounded-lg shadow-sm border mb-8 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Tesla Overview (Base Year 2024)</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {(teslaData.tesla_base_data.total_deliveries / 1000000).toFixed(2)}M
                </div>
                <div className="text-sm text-gray-600">Total Deliveries</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  ${(teslaData.tesla_base_data.total_revenue / 1000000000).toFixed(1)}B
                </div>
                <div className="text-sm text-gray-600">Total Revenue</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  ${(teslaData.tesla_base_data.net_income / 1000000000).toFixed(1)}B
                </div>
                <div className="text-sm text-gray-600">Net Income</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  ${(teslaData.tesla_base_data.cash_and_equivalents / 1000000000).toFixed(1)}B
                </div>
                <div className="text-sm text-gray-600">Cash & Equivalents</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm border mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { id: 'overview', name: 'Tesla Overview' },
                { id: 'vehicle-models', name: 'Vehicle Models' },
                { id: 'statements', name: 'Financial Statements' },
                { id: 'dcf', name: 'DCF Valuation' },
                { id: 'segments', name: 'Business Segments' },
                { id: 'bridge-analysis', name: 'Bridge Analysis' },
                { id: 'comparison', name: 'Scenario Comparison' },
                { id: 'data-overview', name: 'Data Overview' },
                { id: 'forecast', name: 'Advanced Forecast' },
                { id: 'ai-insights', name: 'AI Insights' },
                { id: 'tesla-ai-agent', name: 'Tesla AI Agent' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-red-500 text-red-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'overview' && (
              <ScenarioTabs 
                activeScenario={activeScenario}
                setActiveScenario={setActiveScenario}
                financialModels={financialModels}
                generateModel={generateFinancialModel}
                loading={loading}
              />
            )}

            {activeTab === 'vehicle-models' && (
              <VehicleModelAnalysis />
            )}

            {activeTab === 'statements' && (
              <FinancialStatements 
                scenario={activeScenario}
                model={financialModels[activeScenario]}
                generateModel={generateFinancialModel}
                loading={loading}
              />
            )}

            {activeTab === 'dcf' && (
              <DCFValuation 
                scenario={activeScenario}
                model={financialModels[activeScenario]}
                generateModel={generateFinancialModel}
                loading={loading}
              />
            )}

            {activeTab === 'segments' && (
              <BusinessSegmentAnalysis />
            )}

            {activeTab === 'bridge-analysis' && (
              <BridgeAnalysis />
            )}

            {activeTab === 'comparison' && (
              <ScenarioComparison 
                models={financialModels}
                generateAllScenarios={generateAllScenarios}
                loading={loading}
              />
            )}

            {activeTab === 'data-overview' && (
              <DataOverview />
            )}

            {activeTab === 'forecast' && (
              <ForecastPage />
            )}

            {activeTab === 'ai-insights' && (
              <ProactiveInsights 
                scenario={activeScenario}
                modelData={financialModels[activeScenario]}
              />
            )}

            {activeTab === 'tesla-ai-agent' && (
              <TeslaAIAgent />
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default TeslaDashboard;