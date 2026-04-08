import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';

export default function TrafficChart({ type = 'traffic', height = 300, liveData = [] }) {
    // We use the live timeseries array passed from the parent component.
    // We don't generate any mock arrays in this component anymore.

    if (type === 'traffic') {
        return (
            <div style={{ height: height, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={liveData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis dataKey="time" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                        <YAxis yAxisId="left" stroke="#8b5cf6" tick={{ fill: '#8b5cf6', fontSize: 12 }} />
                        <YAxis yAxisId="right" orientation="right" stroke="#10b981" tick={{ fill: '#10b981', fontSize: 12 }} />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#fff' }}
                            itemStyle={{ color: '#e5e7eb' }}
                        />
                        <Legend verticalAlign="top" height={36} />
                        <Line yAxisId="left" type="monotone" dataKey="traffic" name="Active User Traffic" stroke="#8b5cf6" strokeWidth={3} dot={true} activeDot={{ r: 6 }} />
                        <Line yAxisId="right" type="stepAfter" dataKey="avg_price" name="AI Adjusted Price (₹)" stroke="#10b981" strokeWidth={3} dot={true} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        );
    }

    return (
        <div style={{ height: height, width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={liveData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6b7280" stopOpacity={0.1} />
                            <stop offset="95%" stopColor="#6b7280" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="time" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', color: '#fff' }}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Area type="monotone" dataKey="revenue" name="Actual Revenue (₹)" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={2} isAnimationActive={false} />
                    <Area type="dashed" dataKey="ai_predicted_baseline" name="Baseline (Without AI)" stroke="#6b7280" fillOpacity={1} fill="url(#colorBaseline)" strokeDasharray="5 5" isAnimationActive={false} />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
