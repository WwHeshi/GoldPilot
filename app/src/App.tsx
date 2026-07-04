import AISettingsDialog from './components/AISettingsDialog';
import { Toaster } from './components/ui/sonner';
import { GoldDataProvider } from './contexts/GoldDataContext';
import Footer from './sections/Footer';
import BearishFactors from './sections/BearishFactors';
import BullishFactors from './sections/BullishFactors';
import Hero from './sections/Hero';
import InstitutionalViews from './sections/InstitutionalViews';
import InvestmentAdvice from './sections/InvestmentAdvice';
import PriceChart from './sections/PriceChart';
import Summary from './sections/Summary';
import './App.css';

function App() {
  return (
    <GoldDataProvider>
      <div className="min-h-screen bg-[#0D0B08]">
        <nav className="fixed left-0 right-0 top-0 z-50 border-b border-gray-800/50 bg-[#0D0B08]/80 backdrop-blur-md">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500/20 to-amber-600/10">
                <span className="text-lg font-bold gold-text">G</span>
              </div>
              <span className="hidden font-semibold text-white sm:block">黄金市场分析</span>
            </div>

            <div className="flex items-center gap-3 sm:gap-4">
              <div className="hidden items-center gap-6 md:flex">
                <a href="#analysis" className="text-sm text-gray-400 transition-colors hover:text-amber-400">
                  分析
                </a>
                <a href="#factors" className="text-sm text-gray-400 transition-colors hover:text-amber-400">
                  因素
                </a>
                <a href="#advice" className="text-sm text-gray-400 transition-colors hover:text-amber-400">
                  建议
                </a>
                <a href="#summary" className="text-sm text-gray-400 transition-colors hover:text-amber-400">
                  总结
                </a>
              </div>
              <AISettingsDialog />
            </div>
          </div>
        </nav>

        <main>
          <div className="pt-16">
            <Hero />
          </div>

          <div id="analysis">
            <PriceChart />
          </div>

          <div id="factors">
            <BullishFactors />
            <BearishFactors />
          </div>

          <InstitutionalViews />

          <div id="advice">
            <InvestmentAdvice />
          </div>

          <div id="summary">
            <Summary />
          </div>
        </main>

        <Footer />
        <Toaster richColors />
      </div>
    </GoldDataProvider>
  );
}

export default App;
