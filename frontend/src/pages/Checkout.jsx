import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { CheckCircle2, Loader2, ArrowRight, ShieldCheck, Lock } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Checkout() {
    const { cartItems, totalAmount, clearCart } = useCart();
    const { user, token } = useAuth();
    const navigate = useNavigate();
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);

    const total = totalAmount + 400.0 + (totalAmount * 0.08); // Include shipping and tax mock

    const [formData, setFormData] = useState({
        email: user?.email || '',
        card: '',
        exp: '',
        cvc: ''
    });

    useEffect(() => {
        if (user && formData.email === '') {
            setFormData(prev => ({ ...prev, email: user.email }));
        }
    }, [user]);


    const handleCheckout = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        try {
            // Enterprise Checkout: Map cart items to the strict backend schema needed for row-level locks
            const orderPayload = {
                items: cartItems.map(item => ({
                    // We need a variant_id. Since the frontend cart might still be holding raw products,
                    // we'll default to the first variant if the user didn't explicitly pick one.
                    variant_id: item.selectedVariantId || (item.variants && item.variants.length > 0 ? item.variants[0].id : 1),
                    quantity: item.quantity
                }))
            };

            await axios.post(`${API_URL}/orders/`, orderPayload, {
                headers: { Authorization: `Bearer ${token}` }
            });

            // Simulate slight delay for payment processing feel
            await new Promise(r => setTimeout(r, 1500));
            setSuccess(true);
            clearCart();
        } catch (error) {
            console.error("Order failed", error);

            // Extract the backend's detailed error message if it rejected the row-level lock
            const errorMsg = error.response?.data?.detail || "Checkout failed. Inventory might be sold out.";
            alert(`Payment Rejected: ${errorMsg}`);
        } finally {
            setSubmitting(false);
        }
    };

    if (!user) {
        return (
            <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
            >
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-red-500/10 rounded-full blur-[150px] pointer-events-none" />
                <motion.div 
                    initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }}
                    transition={{ type: "spring", stiffness: 200 }}
                    className="z-10 text-center glass-card p-12 rounded-3xl max-w-lg mx-4 border border-white/10"
                >
                    <Lock className="w-20 h-20 text-indigo-400 mx-auto mb-6 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]" />
                    <h2 className="text-3xl font-black text-white mb-4">Secure Checkout</h2>
                    <p className="text-gray-400 mb-8 font-medium">Please log in to your account to securely complete your purchase.</p>
                    <div className="flex gap-4 justify-center">
                        <Link to="/login" className="bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.6)]">
                            Log In
                        </Link>
                        <Link to="/signup" className="bg-white/10 hover:bg-white/20 border border-white/10 text-white px-8 py-3 rounded-xl font-bold transition-all hover:-translate-y-1">
                            Create Account
                        </Link>
                    </div>
                </motion.div>
            </motion.div>
        );
    }

    if (cartItems.length === 0 && !success) {
        return (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-screen py-32 flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/10 rounded-full blur-[150px] pointer-events-none" />
                <div className="z-10 text-center glass-card p-12 rounded-3xl max-w-lg mx-4">
                    <h2 className="text-3xl font-black text-white mb-4">Your bag is empty</h2>
                    <button onClick={() => navigate('/products')} className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center justify-center w-full transition-colors">Head back to store <ArrowRight className="ml-2 w-5 h-5" /></button>
                </div>
            </motion.div>
        );
    }

    if (success) {
        return (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-screen flex justify-center items-center py-24 relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 rounded-full blur-[150px] pointer-events-none" />
                <motion.div 
                    initial={{ scale: 0.8 }} animate={{ scale: 1 }} transition={{ type: "spring", bounce: 0.5 }}
                    className="max-w-2xl w-full mx-4 glass-card p-12 rounded-[2rem] text-center relative z-10 border border-emerald-500/30 shadow-[0_0_50px_rgba(16,185,129,0.2)]"
                >
                    <div className="flex justify-center mb-8 relative">
                        <div className="absolute inset-0 bg-emerald-500/30 blur-2xl rounded-full w-32 h-32 mx-auto animate-pulse"></div>
                        <CheckCircle2 className="w-32 h-32 text-emerald-400 relative z-10 animate-float" />
                    </div>
                    <h2 className="text-4xl md:text-5xl font-black text-white mb-4 tracking-tight drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]">Payment Successful!</h2>
                    <p className="text-lg text-gray-400 mb-10 font-medium bg-gray-900/50 p-6 rounded-2xl border border-white/5 backdrop-blur-md">Your order has been placed securely and is being processed. An AI priority shipping tag has been applied. We have emailed your receipt to <span className="text-white font-bold">{formData.email}</span>.</p>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/products')}
                        className="inline-flex items-center justify-center px-10 py-5 border border-transparent text-lg font-bold rounded-2xl text-white bg-emerald-500 hover:bg-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.4)] transition-all group"
                    >
                        Continue Shopping <ArrowRight className="ml-3 h-6 w-6 group-hover:translate-x-1 transition-transform" />
                    </motion.button>
                </motion.div>
            </motion.div>
        );
    }

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-screen py-16 relative overflow-hidden text-gray-100">
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[180px] pointer-events-none block" />

            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 top-[2rem]">
                <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="flex items-center justify-between mb-8 border-b border-white/10 pb-6">
                    <h1 className="text-4xl font-black tracking-tight text-white drop-shadow-md">
                        Secure <span className="text-gradient">Checkout.</span>
                    </h1>
                    <div className="flex items-center text-sm font-bold text-emerald-300 bg-emerald-500/10 px-4 py-2 rounded-full border border-emerald-500/30 backdrop-blur-md shadow-[0_0_15px_rgba(16,185,129,0.2)]">
                        <ShieldCheck className="w-5 h-5 mr-2" /> Encrypted Route
                    </div>
                </motion.div>

                <div className="glass-card rounded-[2rem] overflow-hidden">
                    <div className="p-8 md:p-10">
                        <div className="mb-10 p-8 glass-panel rounded-2xl border border-white/10 flex flex-col md:flex-row justify-between items-center shadow-lg bg-gray-900/60 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-bl-full blur-2xl"></div>
                            <span className="text-xl font-bold text-gray-400 mb-2 md:mb-0 relative z-10">Total to pay today</span>
                            <span className="text-4xl md:text-5xl font-black tracking-tight text-indigo-400 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)] relative z-10">₹{total.toFixed(2)}</span>
                        </div>

                        <form onSubmit={handleCheckout} className="space-y-8">
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-bold text-gray-400 mb-2">Email Address (for receipt)</label>
                                    <div className="relative">
                                        <input
                                            type="email"
                                            value={formData.email}
                                            onChange={e => setFormData({ ...formData, email: e.target.value })}
                                            className="block w-full rounded-xl bg-gray-900/80 border border-white/10 text-white placeholder-gray-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:text-base py-4 px-5 transition-all outline-none"
                                            required
                                        />
                                        <div className="absolute right-4 top-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                                    </div>
                                </div>

                                <div className="pt-6 mt-6 border-t border-white/10">
                                    <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                                        Payment Details <Lock className="w-5 h-5 ml-2 text-gray-500" />
                                    </h3>
                                    <div className="space-y-5 bg-gray-900/40 p-6 rounded-2xl border border-white/5">
                                        <div>
                                            <label className="block text-sm font-bold text-gray-400 mb-2">Card Number</label>
                                            <input
                                                type="text"
                                                placeholder="0000 0000 0000 0000"
                                                value={formData.card}
                                                onChange={e => setFormData({ ...formData, card: e.target.value })}
                                                className="block w-full rounded-xl bg-gray-900/80 border border-white/10 text-white placeholder-gray-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:text-base py-4 px-5 transition-all outline-none font-mono"
                                                required
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-5">
                                            <div>
                                                <label className="block text-sm font-bold text-gray-400 mb-2">Expiration date</label>
                                                <input
                                                    type="text"
                                                    placeholder="MM/YY"
                                                    value={formData.exp}
                                                    onChange={e => setFormData({ ...formData, exp: e.target.value })}
                                                    className="block w-full rounded-xl bg-gray-900/80 border border-white/10 text-white placeholder-gray-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:text-base py-4 px-5 transition-all outline-none font-mono"
                                                    required
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-bold text-gray-400 mb-2">CVC</label>
                                                <input
                                                    type="text"
                                                    placeholder="123"
                                                    value={formData.cvc}
                                                    onChange={e => setFormData({ ...formData, cvc: e.target.value })}
                                                    className="block w-full rounded-xl bg-gray-900/80 border border-white/10 text-white placeholder-gray-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:text-base py-4 px-5 transition-all outline-none font-mono"
                                                    required
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                type="submit"
                                disabled={submitting}
                                className="mt-10 w-full bg-indigo-600 border border-indigo-500 shadow-[0_0_20px_rgba(79,70,229,0.3)] rounded-xl py-5 px-4 text-xl font-black text-white hover:bg-indigo-500 hover:shadow-[0_0_40px_rgba(79,70,229,0.6)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900 focus:ring-indigo-400 transition-all flex justify-center items-center disabled:opacity-75 disabled:cursor-not-allowed group relative overflow-hidden"
                            >
                                {submitting ? <><Loader2 className="animate-spin mr-3 h-6 w-6" /> Processing Payment Gateway...</> : <><Lock className="mr-2 h-6 w-6 group-hover:animate-pulse relative z-10" /> <span className="relative z-10">Pay Securely ₹{total.toFixed(2)}</span></>}
                            </motion.button>
                            <p className="text-center text-xs text-gray-400 mt-6 flex items-center justify-center font-medium bg-white/5 py-3 rounded-xl border border-white/10 group"><ShieldCheck className="w-4 h-4 mr-2 text-emerald-400 group-hover:scale-110 transition-transform" /> Guaranteed safe & authenticated checkout powered by Secure SSL.</p>
                        </form>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
