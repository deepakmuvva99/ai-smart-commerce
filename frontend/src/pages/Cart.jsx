import { Link, useNavigate } from 'react-router-dom';
import { Trash2, ArrowRight, ShoppingBag, CheckCircle } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function Cart() {
    const { cartItems, removeFromCart, updateQuantity, totalAmount, totalItems } = useCart();
    const navigate = useNavigate();

    if (cartItems.length === 0) {
        return (
            <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />
                <div className="z-10 text-center glass-card p-12 rounded-3xl max-w-lg mx-4">
                    <ShoppingBag className="w-24 h-24 text-indigo-500/50 mx-auto mb-6 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]" />
                    <h2 className="text-3xl font-black text-white mb-4">Your bag is empty</h2>
                    <p className="text-gray-400 mb-8 font-medium">Looks like you haven't added anything yet. Explore our latest tech deals optimized just for you.</p>
                    <Link
                        to="/products"
                        className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-bold rounded-xl text-white bg-indigo-600 hover:bg-indigo-500 shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] hover:-translate-y-1 transition-all"
                    >
                        Start Shopping
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="min-h-screen py-16 relative overflow-hidden"
        >
            <div className="absolute top-0 right-[-10%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[150px] pointer-events-none" />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 top-[2rem]">
                <h1 className="text-4xl font-black tracking-tight text-white mb-8 border-b border-white/10 pb-6 drop-shadow-lg">
                    Shopping <span className="text-gradient">Bag.</span>
                </h1>

                <div className="lg:grid lg:grid-cols-12 lg:gap-x-12 lg:items-start">
                    <section className="lg:col-span-8">
                        <motion.ul layout className="space-y-6">
                            <AnimatePresence>
                            {cartItems.map((item) => (
                                <motion.li 
                                    layout
                                    initial={{ opacity: 0, scale: 0.9, x: -20 }}
                                    animate={{ opacity: 1, scale: 1, x: 0 }}
                                    exit={{ opacity: 0, scale: 0.8, x: -20 }}
                                    transition={{ type: "spring", stiffness: 200, damping: 20 }}
                                    key={item.id} 
                                    className="glass-card p-4 sm:p-6 rounded-2xl flex flex-col sm:flex-row gap-6 border-white/10 relative"
                                >
                                    <div className="flex-shrink-0 relative overflow-hidden rounded-xl">
                                        <img
                                            src={item.image_url}
                                            alt={item.name}
                                            className="w-full h-48 sm:w-32 sm:h-32 object-cover object-center border border-white/10"
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-gray-900/50 to-transparent" />
                                    </div>
                                    <div className="flex-1 flex flex-col justify-between">
                                        <div className="flex justify-between">
                                            <div>
                                                <h3 className="text-xl font-bold text-white mb-1">
                                                    <Link to={`/products/${item.id}`} className="hover:text-indigo-400 transition-colors">{item.name}</Link>
                                                </h3>
                                                <p className="text-sm font-medium text-emerald-400">In Stock: {item.inventory}</p>
                                            </div>
                                            <p className="text-2xl font-black text-white ml-4">₹{Number(item.current_price).toFixed(2)}</p>
                                        </div>

                                        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-4 sm:gap-0">
                                            {(() => {
                                                const totalInventory = item.variants ? item.variants.reduce((sum, v) => sum + v.inventory, 0) : item.inventory || 0;
                                                return (
                                                    <div className="flex gap-4 items-center bg-gray-900/50 border border-white/10 rounded-xl px-3 py-1">
                                                        <label htmlFor={`quantity-${item.id}`} className="text-sm font-medium text-gray-400">Qty:</label>
                                                        <select
                                                            id={`quantity-${item.id}`}
                                                            className="bg-transparent text-white border-none py-1 pl-2 pr-6 focus:ring-0 text-base font-bold cursor-pointer"
                                                            value={item.quantity}
                                                            onChange={(e) => updateQuantity(item.id, parseInt(e.target.value))}
                                                        >
                                                            {[...Array(Math.min(10, Math.max(1, totalInventory))).keys()].map((n) => (
                                                                <option key={n + 1} value={n + 1} className="bg-gray-900">
                                                                    {n + 1}
                                                                </option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                );
                                            })()}
                                            <button
                                                type="button"
                                                onClick={() => removeFromCart(item.id)}
                                                className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-full transition-all"
                                                title="Remove Item"
                                            >
                                                <Trash2 className="h-5 w-5" />
                                            </button>
                                        </div>
                                    </div>
                                </motion.li>
                            ))}
                            </AnimatePresence>
                        </motion.ul>
                    </section>

                    {/* Order summary */}
                    <motion.section 
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mt-10 lg:mt-0 lg:col-span-4 sticky top-28"
                    >
                        <div className="glass-panel rounded-3xl p-6 sm:p-8 backdrop-blur-3xl border-white/20 shadow-2xl">
                            <h2 className="text-xl font-bold text-white mb-6 border-b border-white/10 pb-4">Order Summary</h2>
                            <dl className="space-y-4 text-sm text-gray-300">
                                <div className="flex items-center justify-between">
                                    <dt>Subtotal ({totalItems} items)</dt>
                                    <dd className="font-medium text-white text-base">₹{totalAmount.toFixed(2)}</dd>
                                </div>
                                <div className="flex items-center justify-between pt-4">
                                    <dt>Shipping estimate</dt>
                                    <dd className="font-medium text-white text-base">₹400.00</dd>
                                </div>
                                <div className="flex items-center justify-between pt-4">
                                    <dt>Tax estimate (8%)</dt>
                                    <dd className="font-medium text-white text-base">₹{(totalAmount * 0.08).toFixed(2)}</dd>
                                </div>
                                <div className="flex items-center justify-between border-t border-white/10 pt-6 mt-6">
                                    <dt className="text-lg font-bold text-white">Total to Pay</dt>
                                    <dd className="text-2xl font-black text-indigo-400 drop-shadow-[0_0_10px_rgba(99,102,241,0.3)]">
                                        ₹{(totalAmount + 400.0 + (totalAmount * 0.08)).toFixed(2)}
                                    </dd>
                                </div>
                            </dl>

                            <div className="mt-8">
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    type="button"
                                    onClick={() => navigate('/checkout')}
                                    className="w-full bg-indigo-600 rounded-xl shadow-[0_0_20px_rgba(79,70,229,0.3)] py-4 px-4 text-base font-bold text-white hover:bg-indigo-500 hover:shadow-[0_0_40px_rgba(79,70,229,0.6)] transition-all flex justify-center items-center group overflow-hidden relative border border-indigo-400/30"
                                >
                                    <span className="absolute w-0 h-0 transition-all duration-300 ease-out bg-white rounded-full group-hover:w-full group-hover:h-56 opacity-10"></span>
                                    <span className="relative flex items-center">Proceed to Checkout <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" /></span>
                                </motion.button>
                            </div>
                        </div>
                    </motion.section>
                </div>
            </div>
        </motion.div>
    );
}
