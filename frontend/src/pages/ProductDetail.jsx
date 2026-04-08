import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { ShoppingCart, Zap, ShieldCheck, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ProductDetail() {
    const { id } = useParams();
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const { addToCart } = useCart();
    const [added, setAdded] = useState(false);

    useEffect(() => {
        const fetchProductAndLogTraffic = async () => {
            try {
                // Fetch product details
                const res = await axios.get(`${API_URL}/products/${id}`);
                setProduct(res.data);

                // Log traffic view to trigger AI demand algorithm
                try {
                    await axios.post(`${API_URL}/products/${id}/traffic`, {
                        event_type: "view"
                    });
                    console.log("Traffic logged for AI pricing.");
                } catch (trafficErr) {
                    console.warn("Traffic logging failed:", trafficErr.message);
                }

            } catch (error) {
                console.error("Error fetching product", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProductAndLogTraffic();
    }, [id]);

    const handleAddToCart = () => {
        addToCart(product);
        setAdded(true);
        toast.success(
            <div className="flex flex-col">
                <span className="font-bold text-white text-sm">{product.name}</span>
                <span className="text-gray-400 text-xs">Secured in your bag!</span>
            </div>
        );
        setTimeout(() => setAdded(false), 2000);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen bg-gray-950">
                <div className="relative">
                    <div className="w-16 h-16 border-t-2 border-indigo-500 border-solid rounded-full animate-spin"></div>
                    <div className="w-16 h-16 border-r-2 border-purple-500 border-solid rounded-full animate-spin absolute top-0 left-0" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                </div>
            </div>
        );
    }

    if (!product) return <div className="text-center py-20 text-gray-400 bg-gray-950 min-h-screen">Product not found.</div>;

    return (
        <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }} 
            className="min-h-screen py-12 relative overflow-hidden"
        >
            {/* Ambient Background Glows */}
            <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[150px] pointer-events-none animate-pulse-slow" />
            <div className="absolute bottom-[0%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-600/10 blur-[120px] pointer-events-none" />

            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 top-[2rem]">
                <Link to="/products" className="inline-flex items-center text-sm font-bold text-gray-400 hover:text-white mb-8 transition-colors bg-white/5 border border-white/10 px-4 py-2 rounded-full hover:bg-white/10 backdrop-blur-sm shadow-md">
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Catalog
                </Link>

                <div className="lg:grid lg:grid-cols-2 lg:gap-x-12 xl:gap-x-16">
                    {/* Image */}
                    <motion.div 
                        initial={{ x: -50, opacity: 0 }} 
                        animate={{ x: 0, opacity: 1 }} 
                        transition={{ duration: 0.6, type: "spring", stiffness: 100 }}
                        className="lg:max-w-lg lg:self-end w-full group relative mb-12 lg:mb-0"
                    >
                        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500/20 to-purple-500/20 rounded-[2.5rem] blur-[60px] group-hover:blur-[80px] transition-all duration-700"></div>
                        <div className="relative rounded-[2rem] overflow-hidden shadow-2xl bg-gray-900 border border-white/10 aspect-w-4 aspect-h-3 glass-card">
                            <img
                                src={product.image_url}
                                alt={product.name}
                                className="w-full h-[500px] object-cover object-center group-hover:scale-105 transition-transform duration-700 opacity-90 group-hover:opacity-100"
                            />
                            {product.current_price < product.base_price && (
                                <div className="absolute top-6 left-6 bg-emerald-500/90 backdrop-blur-md text-white px-4 py-2 rounded-full shadow-[0_0_20px_rgba(16,185,129,0.4)] flex items-center font-black text-sm border border-emerald-400/50">
                                    <Zap className="mr-2 h-4 w-4" />
                                    AI PRICE DROP DEAL
                                </div>
                            )}
                        </div>
                    </motion.div>

                    {/* Product info */}
                    <motion.div 
                        initial={{ x: 50, opacity: 0 }} 
                        animate={{ x: 0, opacity: 1 }} 
                        transition={{ duration: 0.6, delay: 0.2, type: "spring", stiffness: 100 }}
                        className="mt-10 px-4 sm:px-0 sm:mt-16 lg:mt-0 lg:py-8"
                    >
                        <motion.div 
                            initial={{ scale: 0.8 }} 
                            animate={{ scale: 1 }}
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-6 shadow-sm"
                        >
                            <span>Dynamic Item #{product.id}</span>
                        </motion.div>

                        <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl md:text-6xl mb-6 leading-tight drop-shadow-xl">
                            {product.name}
                        </h1>

                        <div className="mt-4 mb-8">
                            <h2 className="sr-only">Product information</h2>
                            <div className="flex items-end">
                                <p className="text-5xl text-white font-black tracking-tighter drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">₹{Number(product.current_price).toFixed(2)}</p>
                                {product.current_price !== product.base_price && (
                                    <div className="ml-6 pb-1">
                                        <p className="text-lg text-gray-500 line-through decoration-red-500/50 font-bold mb-1">₹{Number(product.base_price).toFixed(2)} Base</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="mt-8 border-t border-white/10 pt-8">
                            <h3 className="sr-only">Description</h3>
                            <div className="text-lg text-gray-400 leading-relaxed font-medium bg-white/5 rounded-2xl p-6 border border-white/5 backdrop-blur-sm">
                                <p>{product.description}</p>
                            </div>
                        </div>

                        <div className="mt-10 space-y-6">
                            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-6 mb-8 text-sm font-bold glass-panel p-4 rounded-2xl border-white/5 bg-gray-900/50">
                                <div className="flex items-center text-emerald-400 bg-emerald-400/10 px-4 py-2 rounded-xl">
                                    <ShieldCheck className="w-5 h-5 mr-2" /> Certified Premium Quality
                                </div>
                                {(() => {
                                    const totalInventory = product.variants ? product.variants.reduce((sum, v) => sum + v.inventory, 0) : product.inventory || 0;
                                    return totalInventory < 20 ? (
                                        <div className="flex items-center text-amber-500 bg-amber-500/10 px-4 py-2 rounded-xl animate-pulse">
                                            <Zap className="w-5 h-5 mr-2" /> Hurry! Only {totalInventory} left
                                        </div>
                                    ) : (
                                        <div className="flex items-center text-indigo-400 bg-indigo-400/10 px-4 py-2 rounded-xl">
                                            <CheckCircle2 className="w-5 h-5 mr-2" /> In Stock ({totalInventory})
                                        </div>
                                    );
                                })()}
                            </div>

                            <div className="mt-8 flex sm:flex-col1">
                                {product.variants && product.variants.length > 0 && (
                                    <div className="mb-6">
                                        <label htmlFor={`variant-${product.id}`} className="block text-sm font-bold text-gray-400 mb-2">Select Option:</label>
                                        <div className="relative">
                                            <select
                                                id={`variant-${product.id}`}
                                                className="block w-full rounded-xl bg-gray-900 border border-white/10 text-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:text-base py-3 px-4 transition-all outline-none appearance-none font-medium"
                                                onChange={(e) => {
                                                    const varId = Number(e.target.value);
                                                    setProduct(p => ({ ...p, selectedVariantId: varId }));
                                                }}
                                                value={product.selectedVariantId || product.variants[0].id}
                                            >
                                                {product.variants.map((v) => (
                                                    <option key={v.id} value={v.id} disabled={v.inventory <= 0}>
                                                        {v.color} - {v.size} {v.inventory <= 0 ? '(Out of Stock)' : `(${v.inventory} left)`}
                                                    </option>
                                                ))}
                                            </select>
                                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-400">
                                                <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" fillRule="evenodd"></path></svg>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    type="button"
                                    onClick={handleAddToCart}
                                    disabled={added}
                                    className={`w-full flex-1 border border-transparent rounded-2xl py-5 px-8 flex items-center justify-center text-lg font-bold text-white transition-all shadow-xl ${added
                                        ? 'bg-emerald-500 hover:bg-emerald-600 shadow-[0_0_30px_rgba(16,185,129,0.4)]'
                                        : 'bg-indigo-600 hover:bg-indigo-500 hover:shadow-[0_0_30px_rgba(79,70,229,0.5)]'
                                        }`}
                                >
                                    {added ? (
                                        <><CheckCircle2 className="mr-3 h-6 w-6" /> Secured in Bag!</>
                                    ) : (
                                        <><ShoppingCart className="mr-3 h-6 w-6" /> Add to Shopping Bag</>
                                    )}
                                </motion.button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </motion.div>
    );
}
