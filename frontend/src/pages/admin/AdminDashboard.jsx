import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { LayoutDashboard, TrendingUp, Settings, Activity, Users, DollarSign, Package } from 'lucide-react';
import DashboardMetrics from '../../components/admin/DashboardMetrics';
import TrafficChart from '../../components/admin/TrafficChart';
import AdminProducts from './AdminProducts';
import AdminSettings from './AdminSettings';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AdminDashboard() {
    const location = useLocation();
    const [metrics, setMetrics] = useState({
        revenue: 0,
        baseline: 0,
        activeUsers: 0,
        trafficSpikes: 0,
        aiAdjustments: 0
    });
    const [timeseriesData, setTimeseriesData] = useState([]);

    // Fetch real data from the backend every 3 seconds
    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                // Polling the new Real-Time Backend Endpoint
                const token = localStorage.getItem('token');
                if (!token) return; // Wait for AuthContext redirect

                const res = await axios.get(`${API_URL}/analytics/dashboard`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const data = res.data;

                // Update top level metrics
                setMetrics(data.metrics);

                // Append to our local timeseries state for charts to digest
                setTimeseriesData(prev => {
                    const newData = [...prev, data.timeseries];
                    // Keep only last 20 data points
                    if (newData.length > 20) {
                        return newData.slice(newData.length - 20);
                    }
                    return newData;
                });

            } catch (error) {
                console.error("Failed to fetch live analytics", error);
            }
        };

        fetchAnalytics(); // initial fetch
        const interval = setInterval(fetchAnalytics, 3000);
        return () => clearInterval(interval);
    }, []);

    const navItems = [
        { name: 'Overview', path: '/admin', icon: LayoutDashboard },
        { name: 'Traffic & AI Pricing', path: '/admin/traffic', icon: Activity },
        { name: 'Products', path: '/admin/products', icon: Package },
        { name: 'Settings', path: '/admin/settings', icon: Settings },
    ];

    return (
        <div className="flex h-[calc(100vh-104px)] bg-transparent relative overflow-hidden text-gray-100">
            {/* Ambient Admin Background Glow */}
            <div className="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-600/10 blur-[150px] pointer-events-none block z-0" />
            <div className="absolute bottom-[0%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none block z-0" />

            {/* Sidebar */}
            <div className="w-64 flex-shrink-0 glass-panel border-r border-white/5 shadow-2xl relative z-10 hidden md:block backdrop-blur-3xl">
                <div className="h-full flex flex-col pt-8">
                    <div className="px-6 py-8">
                        <h2 className="text-xl font-bold text-white tracking-wider uppercase text-center mb-8 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
                            Admin Portal
                        </h2>
                        <nav className="space-y-2">
                            {navItems.map((item) => {
                                const Icon = item.icon;
                                const isActive = location.pathname === item.path;
                                return (
                                    <Link
                                        key={item.name}
                                        to={item.path}
                                        className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${isActive
                                            ? 'bg-indigo-600/80 backdrop-blur-md text-white shadow-[0_0_20px_rgba(79,70,229,0.4)] border border-indigo-500/50'
                                            : 'text-gray-400 hover:bg-white/5 hover:text-white border border-transparent'
                                            }`}
                                    >
                                        <Icon className="mr-3 h-5 w-5" />
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </nav>
                    </div>

                    <div className="mt-auto p-6 border-t border-white/5 bg-black/10">
                        <div className="flex items-center">
                            <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse mr-2 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                            <span className="text-xs text-gray-400 font-medium">REAL TIME AI SYNC ONLINE</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-auto bg-transparent p-8 relative z-10">
                <div className="max-w-7xl mx-auto">
                    <div className="mb-8 flex justify-between items-center bg-white/5 border border-white/10 p-6 rounded-3xl backdrop-blur-md shadow-lg">
                        <h1 className="text-3xl font-black text-white tracking-tight drop-shadow-md">Dashboard <span className="text-gradient">Overview.</span></h1>
                        <div className="bg-emerald-500/10 rounded-full px-4 py-2 text-sm font-bold text-emerald-300 flex items-center border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                            <span className="w-2 h-2 rounded-full bg-emerald-400 mr-2 animate-ping opacity-75"></span>
                            Live Data Active
                        </div>
                    </div>

                    <Routes>
                        <Route path="/" element={
                            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <DashboardMetrics metrics={metrics} />
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
                                    <div className="glass-card p-6 rounded-[2rem] border border-white/10 shadow-2xl">
                                        <h3 className="text-lg font-bold text-gray-200 mb-6 flex items-center">
                                            <TrendingUp className="w-5 h-5 mr-3 text-indigo-400 drop-shadow-sm" /> Revenue Tracking (Real Database)
                                        </h3>
                                        <TrafficChart type="revenue" liveData={timeseriesData} />
                                    </div>
                                    <div className="glass-card p-6 rounded-[2rem] border border-white/10 shadow-2xl">
                                        <h3 className="text-lg font-bold text-gray-200 mb-6 flex items-center">
                                            <Activity className="w-5 h-5 mr-3 text-emerald-400 drop-shadow-sm" /> AI Pricing & Organic Traffic
                                        </h3>
                                        <TrafficChart type="traffic" liveData={timeseriesData} />
                                    </div>
                                </div>
                            </div>
                        } />
                        <Route path="/traffic" element={
                            <div className="glass-card p-8 rounded-[2rem] border border-white/10 shadow-2xl h-[600px]">
                                <h3 className="text-xl font-bold text-gray-200 mb-8 border-b border-white/5 pb-4">Detailed AI Telemetry</h3>
                                <TrafficChart type="traffic" height={450} liveData={timeseriesData} />
                            </div>
                        } />
                        <Route path="/products" element={<AdminProducts />} />
                        <Route path="/settings" element={<AdminSettings />} />
                    </Routes>
                </div>
            </div>
        </div>
    );
}
