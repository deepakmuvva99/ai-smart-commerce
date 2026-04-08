import { useState, useEffect } from 'react';
import axios from 'axios';
import { Settings, Sliders, Database, Server, RefreshCw, Zap, Power, Brain, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AdminSettings() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState('');
    const [toast, setToast] = useState(null); // { message, type: 'success'|'error' }

    const { token } = useAuth();

    // Fetch live status from backend
    const fetchStatus = async () => {
        try {
            const res = await axios.get(`${API_URL}/admin/status`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStatus(res.data);
        } catch (error) {
            console.error("Failed to fetch admin status", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const showToast = (message, type = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    };

    // Toggle the scheduler on/off
    const toggleScheduler = async () => {
        const isRunning = status?.scheduler_running;
        setActionLoading('toggle');
        try {
            const config = { headers: { Authorization: `Bearer ${token}` } };
            if (isRunning) {
                await axios.post(`${API_URL}/admin/toggle-scheduler?enable=false`, {}, config);
                showToast("AI Pricing Scheduler paused.");
            } else {
                await axios.post(`${API_URL}/admin/toggle-scheduler?enable=true`, {}, config);
                showToast("AI Pricing Scheduler activated!");
            }
            await fetchStatus();
        } catch (e) {
            showToast("Failed to toggle scheduler.", 'error');
        }
        setActionLoading('');
    };

    // Change run interval
    const changeInterval = async (e) => {
        const seconds = parseInt(e.target.value);
        setActionLoading('interval');
        try {
            await axios.post(`${API_URL}/admin/set-interval?seconds=${seconds}`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            showToast(`Interval updated to ${seconds} seconds.`);
            await fetchStatus();
        } catch (e) {
            showToast("Failed to update interval.", 'error');
        }
        setActionLoading('');
    };

    // Trigger SAC RL retraining
    const triggerRetrain = async () => {
        setActionLoading('retrain');
        try {
            const res = await axios.post(`${API_URL}/admin/retrain`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            showToast(`Retraining started! Current updates: ${res.data.current_updates || 'N/A'}`);
        } catch (e) {
            showToast("Failed to trigger retraining.", 'error');
        }
        setActionLoading('');
    };

    // Purge database
    const purgeDatabase = async () => {
        if (!window.confirm("This will DELETE all traffic, orders, and price history, and reset all prices to base. Are you sure?")) return;
        setActionLoading('purge');
        try {
            const res = await axios.post(`${API_URL}/admin/purge-db`, {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            showToast(res.data.message || "Database purged.");
            await fetchStatus();
        } catch (e) {
            showToast("Failed to purge database.", 'error');
        }
        setActionLoading('');
    };

    const schedulerRunning = status?.scheduler_running ?? false;
    const aiOnline = status?.ai_service?.status === 'healthy';
    const sacUpdates = status?.ai_service?.sac_agent_updates ?? 0;
    const bufferSize = status?.ai_service?.sac_buffer_size ?? 0;
    const currentInterval = status?.interval_seconds ?? 60;

    if (loading) {
        return <div className="text-gray-400 text-center py-20">Loading settings...</div>;
    }

    return (
        <div className="glass-panel border-white/10 rounded-[2rem] p-10 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl relative">
            {/* Toast Notification */}
            {toast && (
                <div className={`absolute top-4 right-4 px-4 py-3 rounded-lg text-sm font-medium flex items-center shadow-lg z-50 animate-in fade-in slide-in-from-top-2 duration-300 ${toast.type === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                    {toast.type === 'success' ? <CheckCircle className="w-4 h-4 mr-2" /> : <AlertCircle className="w-4 h-4 mr-2" />}
                    {toast.message}
                </div>
            )}

            <h2 className="text-2xl font-black text-white flex items-center mb-10 pb-6 border-b border-white/10 drop-shadow-md">
                <Settings className="w-7 h-7 mr-4 text-indigo-400" />
                Platform Settings
            </h2>

            <div className="space-y-8">
                {/* AI Engine Status Banner */}
                <div className={`flex items-center justify-between p-4 rounded-xl border ${aiOnline ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
                    <div className="flex items-center">
                        <div className={`h-3 w-3 rounded-full mr-3 ${aiOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <div>
                            <p className={`text-sm font-medium ${aiOnline ? 'text-green-400' : 'text-red-400'}`}>
                                AI Service: {aiOnline ? 'Online' : 'Offline'}
                            </p>
                            <p className="text-xs text-gray-500">
                                SAC Agent: {sacUpdates} training updates | Buffer: {bufferSize} experiences
                            </p>
                        </div>
                    </div>
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${aiOnline ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        Port 8001
                    </span>
                </div>

                {/* AI Configuration */}
                <section className="glass-card rounded-3xl p-8 border border-white/5 shadow-xl">
                    <h3 className="text-xl font-bold text-white flex items-center mb-6 drop-shadow-sm">
                        <Sliders className="w-6 h-6 mr-3 text-indigo-400" />
                        AI Optimization Engine
                    </h3>
                    <div className="space-y-4">
                        {/* Model Toggle */}
                        <div className="flex justify-between items-center bg-black/20 p-5 rounded-2xl border border-white/5 shadow-inner">
                            <div>
                                <h4 className="text-base font-bold text-white">Pricing Scheduler</h4>
                                <p className="text-sm text-gray-400 mt-1 font-medium">
                                    {schedulerRunning ? 'SAC RL Agent is actively optimizing prices' : 'Scheduler is paused — prices are static'}
                                </p>
                            </div>
                            <button
                                onClick={toggleScheduler}
                                disabled={actionLoading === 'toggle'}
                                className={`w-14 h-7 rounded-full relative cursor-pointer transition-colors duration-200 ${schedulerRunning ? 'bg-indigo-600' : 'bg-gray-600'}`}
                            >
                                {actionLoading === 'toggle' ? (
                                    <Loader2 className="w-4 h-4 animate-spin text-white absolute top-1.5 left-5" />
                                ) : (
                                    <div className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${schedulerRunning ? 'right-1' : 'left-1'}`}></div>
                                )}
                            </button>
                        </div>

                        {/* Run Interval */}
                        <div className="flex justify-between items-center bg-black/20 p-5 rounded-2xl border border-white/5 shadow-inner">
                            <div>
                                <h4 className="text-base font-bold text-white">Run Interval</h4>
                                <p className="text-sm text-gray-400 mt-1 font-medium">How often the RL agent evaluates prices</p>
                            </div>
                            <select
                                value={currentInterval}
                                onChange={changeInterval}
                                disabled={actionLoading === 'interval'}
                                className="bg-gray-900 text-white font-bold border border-white/10 rounded-xl text-sm px-4 py-2.5 focus:border-indigo-500 focus:outline-none shadow-md backdrop-blur-sm cursor-pointer"
                            >
                                <option value={30}>Every 30 Seconds</option>
                                <option value={60}>Every 60 Seconds</option>
                                <option value={300}>Every 5 Minutes</option>
                                <option value={3600}>Every 1 Hour</option>
                            </select>
                        </div>

                        {/* Retrain Button */}
                        <div className="flex justify-between items-center bg-black/20 p-5 rounded-2xl border border-white/5 shadow-inner">
                            <div>
                                <h4 className="text-base font-bold text-white">Force Retrain SAC Agent</h4>
                                <p className="text-sm text-gray-400 mt-1 font-medium">Run 100 batch training steps on accumulated experience</p>
                            </div>
                            <button
                                onClick={triggerRetrain}
                                disabled={actionLoading === 'retrain'}
                                className="text-sm font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-400/10 hover:bg-indigo-400/20 px-4 py-2 rounded-lg transition-colors flex items-center disabled:opacity-50"
                            >
                                {actionLoading === 'retrain' ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                    <Brain className="w-4 h-4 mr-2" />
                                )}
                                Retrain Now
                            </button>
                        </div>
                    </div>
                </section>

                {/* Database Settings */}
                <section className="glass-card rounded-3xl p-8 border border-white/5 shadow-xl">
                    <h3 className="text-xl font-bold text-white flex items-center mb-6 drop-shadow-sm">
                        <Database className="w-6 h-6 mr-3 text-emerald-400" />
                        Database Configuration
                    </h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center bg-black/20 p-5 rounded-2xl border border-white/5 shadow-inner">
                            <div>
                                <h4 className="text-base font-bold text-white">Active Connection</h4>
                                <p className="text-sm text-emerald-400 mt-1 font-medium flex items-center"><Server className="w-4 h-4 mr-2" /> SQLite (sql_app.db) - Connected</p>
                            </div>
                        </div>
                        <div className="flex justify-between items-center bg-black/20 p-5 rounded-2xl border border-white/5 shadow-inner">
                            <div>
                                <h4 className="text-base font-bold text-white">Hard Reset Store</h4>
                                <p className="text-sm text-gray-400 mt-1 font-medium">Clear all traffic, orders, price history, and reset prices to base.</p>
                            </div>
                            <button
                                onClick={purgeDatabase}
                                disabled={actionLoading === 'purge'}
                                className="text-sm font-medium text-red-400 hover:text-red-300 bg-red-400/10 hover:bg-red-400/20 px-4 py-2 rounded-lg transition-colors flex items-center disabled:opacity-50"
                            >
                                {actionLoading === 'purge' ? (
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                ) : (
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                )}
                                Purge DB
                            </button>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
