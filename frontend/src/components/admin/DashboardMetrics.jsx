import { DollarSign, Users, Activity, Zap } from 'lucide-react';

export default function DashboardMetrics({ metrics }) {
    const cards = [
        { name: 'Total Revenue (Actual)', value: `₹${metrics.revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, icon: DollarSign, color: 'text-green-500', bg: 'bg-green-500/10' },
        { name: 'Active Users (15m)', value: metrics.activeUsers.toLocaleString(), icon: Users, color: 'text-blue-500', bg: 'bg-blue-500/10' },
        { name: 'Traffic Clicks (Today)', value: metrics.trafficSpikes, icon: Activity, color: 'text-orange-500', bg: 'bg-orange-500/10' },
        { name: 'AI Price Adjustments', value: metrics.aiAdjustments, icon: Zap, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    ];

    return (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((card) => {
                const Icon = card.icon;
                return (
                    <div key={card.name} className="relative bg-gray-900 pt-5 px-4 pb-6 sm:pt-6 sm:px-6 shadow-xl rounded-2xl overflow-hidden border border-gray-800 hover:border-gray-700 transition-colors">
                        <dt>
                            <div className={`absolute rounded-xl p-3 ${card.bg}`}>
                                <Icon className={`h-6 w-6 ${card.color}`} aria-hidden="true" />
                            </div>
                            <p className="ml-16 text-sm font-medium text-gray-400 truncate">{card.name}</p>
                        </dt>
                        <dd className="ml-16 pb-2 flex items-baseline sm:pb-3">
                            <p className="text-2xl font-semibold text-white">{card.value}</p>
                        </dd>
                    </div>
                );
            })}
        </div>
    );
}
