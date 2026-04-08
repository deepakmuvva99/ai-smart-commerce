import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Zap, TrendingUp, ShieldCheck, Sparkles, ShoppingCart, TrendingDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { useCart } from '../context/CartContext';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Home() {
    const [products, setProducts] = useState([]);
    const { addToCart } = useCart();
    const [addedId, setAddedId] = useState(null);

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await axios.get(`${API_URL}/products/`);
                setProducts(res.data.slice(0, 8)); // Top 8 featured products
            } catch (error) {
                console.error("Error fetching", error);
            }
        };
        fetchProducts();
        const interval = setInterval(fetchProducts, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleQuickAdd = (e, product) => {
        e.preventDefault();
        e.stopPropagation();
        addToCart(product);
        setAddedId(product.id);
        toast.success(
            <div className="flex flex-col">
                <span className="font-bold text-white text-sm">{product.name}</span>
                <span className="text-gray-400 text-xs">Added to your cart.</span>
            </div>
        );
        setTimeout(() => setAddedId(null), 1500);
    };
    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="relative min-h-screen overflow-hidden font-sans text-gray-100"
        >
            {/* Ambient Background Glows */}
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[150px] pointer-events-none animate-pulse-slow" />
            <div className="absolute top-[20%] right-[-20%] w-[40%] h-[40%] rounded-full bg-violet-600/20 blur-[150px] pointer-events-none animate-pulse-slow" style={{ animationDelay: '2s' }} />

            {/* Hero Section */}
            <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 sm:pt-32 sm:pb-24 lg:pb-32">
                <div className="text-center lg:text-left flex flex-col lg:flex-row items-center gap-12">

                    {/* Left Column (Text Config) */}
                    <div className="flex-1 lg:max-w-2xl">
                        <motion.div 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.1, duration: 0.5 }}
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-sm font-semibold mb-6 shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                        >
                            <Sparkles className="h-4 w-4" />
                            <span>V2 Engine Live: AI Dynamic Pricing</span>
                        </motion.div>

                        <motion.h1 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2, duration: 0.5 }}
                            className="text-5xl tracking-tight font-black text-white sm:text-6xl md:text-7xl mb-6 leading-tight drop-shadow-lg"
                        >
                            <span className="block">Next-Generation</span>
                            <span className="block text-gradient mt-2 pb-2">AI Commerce.</span>
                        </motion.h1>

                        <motion.p 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.3, duration: 0.5 }}
                            className="mt-3 text-lg text-gray-300 sm:text-xl md:mt-5 max-w-xl mx-auto lg:mx-0 font-medium"
                        >
                            Experience dynamic, real-time pricing that adapts to market demand. Unbeatable deals on premium tech accessories optimized every minute by our SAC Reinforcement Learning model.
                        </motion.p>

                        <motion.div 
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.4, duration: 0.5 }}
                            className="mt-8 flex gap-4 justify-center lg:justify-start"
                        >
                            <Link
                                to="/products"
                                className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-indigo-600 font-pj rounded-xl focus:outline-none hover:bg-indigo-500 shadow-[0_0_20px_rgba(79,70,229,0.5)] hover:shadow-[0_0_40px_rgba(79,70,229,0.7)]"
                            >
                                Shop Catalog
                                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </Link>
                            <Link
                                to="/login"
                                className="glass-button inline-flex items-center justify-center px-8 py-4 font-bold text-white rounded-xl"
                            >
                                Member Login
                            </Link>
                        </motion.div>
                    </div>

                    {/* Right Column (Hero Image inside Glass Card) */}
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.3, duration: 0.7 }}
                        className="flex-1 w-full lg:w-auto mt-12 lg:mt-0 relative animate-float pl-0 lg:pl-10"
                    >
                        <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-3xl blur-[80px] opacity-30"></div>
                        <div className="relative glass-card rounded-3xl p-4 md:p-5 overflow-hidden border border-white/20 shadow-2xl">
                            <img
                                className="w-full h-[300px] sm:h-[400px] object-cover rounded-2xl transition-transform hover:scale-105 duration-1000 opacity-90 brightness-110 object-center"
                                src="https://images.unsplash.com/photo-1523206489230-c012c64b2b48?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80"
                                alt="Premium Tech"
                            />

                            {/* Floating Stats Badge */}
                            <motion.div 
                                initial={{ x: 50, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ delay: 0.8, type: 'spring' }}
                                className="absolute bottom-10 right-10 glass-panel rounded-xl p-4 shadow-2xl flex items-center gap-4 border border-white/30"
                            >
                                <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
                                    <TrendingUp className="h-5 w-5 text-green-400" />
                                </div>
                                <div>
                                    <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Live Pricing Optimization</p>
                                    <p className="text-lg font-bold text-white">Active</p>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            </div>

            {/* Feature Section */}
            <div className="relative z-10 py-24 bg-transparent">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <motion.div 
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-16"
                    >
                        <h2 className="text-sm text-indigo-400 font-bold tracking-widest uppercase mb-3 drop-shadow-md">Why Choose Us</h2>
                        <p className="text-3xl font-black text-white sm:text-4xl md:text-5xl drop-shadow-xl">
                            A smarter way to buy.
                        </p>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 px-4">
                        <motion.div 
                            whileHover={{ y: -10 }}
                            className="glass-card rounded-2xl p-8 group overflow-hidden relative border border-white/10"
                        >
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/20 rounded-bl-[100px] transition-all duration-500 group-hover:bg-indigo-500/40 blur-2xl" />
                            <div className="feature-icon-wrapper text-indigo-300 mb-6 relative z-10 shadow-[0_0_15px_rgba(99,102,241,0.3)] bg-white/10">
                                <Zap className="h-6 w-6" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3 relative z-10 drop-shadow-md">Algorithmic Pricing</h3>
                            <p className="text-gray-300 leading-relaxed relative z-10">Our Reinforcement Learning AI agent optimizes item prices every 5 minutes based on live market demand signals.</p>
                        </motion.div>

                        <motion.div 
                            whileHover={{ y: -10 }}
                            transition={{ delay: 0.1 }}
                            className="glass-card rounded-2xl p-8 group overflow-hidden relative border border-white/10"
                        >
                            <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/20 rounded-bl-[100px] transition-all duration-500 group-hover:bg-purple-500/40 blur-2xl" />
                            <div className="feature-icon-wrapper text-purple-300 mb-6 relative z-10 shadow-[0_0_15px_rgba(168,85,247,0.3)] bg-white/10">
                                <TrendingUp className="h-6 w-6" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3 relative z-10 drop-shadow-md">Demand Forecasting</h3>
                            <p className="text-gray-300 leading-relaxed relative z-10">Anticipating inventory fluctuations using Deep Learning (LSTM Attention) before the rush happens.</p>
                        </motion.div>

                        <motion.div 
                            whileHover={{ y: -10 }}
                            transition={{ delay: 0.2 }}
                            className="glass-card rounded-2xl p-8 group overflow-hidden relative border border-white/10"
                        >
                            <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/20 rounded-bl-[100px] transition-all duration-500 group-hover:bg-emerald-500/40 blur-2xl" />
                            <div className="feature-icon-wrapper text-emerald-300 mb-6 relative z-10 shadow-[0_0_15px_rgba(16,185,129,0.3)] bg-white/10">
                                <ShieldCheck className="h-6 w-6" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-3 relative z-10 drop-shadow-md">Premium Quality</h3>
                            <p className="text-gray-300 leading-relaxed relative z-10">We stock only top-tier gadgets with verified quality assurance and encrypted secure checkout.</p>
                        </motion.div>
                    </div>
                </div>
            </div>

            {/* Live Catalog Section on Home */}
            <div className="relative z-10 py-16 bg-transparent border-t border-white/5">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-end mb-10">
                        <motion.div initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }}>
                            <h2 className="text-3xl font-black text-white drop-shadow-lg tracking-tight mb-2">Live Catalog</h2>
                            <p className="text-gray-400 font-medium">Top products optimized by AI in real-time.</p>
                        </motion.div>
                        <Link to="/products" className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1 transition-colors">
                            View All <ArrowRight className="w-4 h-4" />
                        </Link>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        {products.map((product) => (
                            <motion.div initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} key={product.id}>
                                <Link to={`/products/${product.id}`} className="group glass-card rounded-2xl flex flex-col overflow-hidden relative h-full">
                                    <div className="relative aspect-w-4 aspect-h-3 w-full overflow-hidden bg-gray-900 border-b border-white/10">
                                        <img
                                            src={product.image_url || `https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80`}
                                            alt={product.name}
                                            className="w-full h-56 object-cover object-center group-hover:scale-110 transition-transform duration-700 opacity-80 group-hover:opacity-100"
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent opacity-90" />
                                        {product.current_price < product.base_price && (
                                            <div className="absolute top-3 left-3 bg-emerald-500/90 backdrop-blur-md text-white text-xs font-black px-2.5 py-1 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.5)] flex items-center border border-white/20">
                                                <TrendingDown className="w-3 h-3 mr-1" /> PRICE DROP
                                            </div>
                                        )}
                                    </div>
                                    <div className="p-5 flex-1 flex flex-col relative z-10">
                                        <h3 className="text-lg font-bold text-white mb-2 line-clamp-1 group-hover:text-indigo-400 drop-shadow-sm">{product.name}</h3>
                                        <p className="text-sm text-gray-300 line-clamp-2 flex-1 mb-4 drop-shadow-sm">{product.description}</p>
                                        <div className="flex justify-between items-end mt-auto pt-4 border-t border-white/10">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xl font-black text-white drop-shadow-lg">₹{Number(product.current_price).toFixed(2)}</span>
                                                {product.current_price !== product.base_price && (
                                                    <span className="text-xs font-medium text-gray-400 line-through decoration-red-500/80">₹{Number(product.base_price).toFixed(2)}</span>
                                                )}
                                            </div>
                                            <motion.button
                                                whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}
                                                onClick={(e) => handleQuickAdd(e, product)}
                                                className={`p-2.5 rounded-xl transition-all shadow-xl border ${addedId === product.id ? 'bg-emerald-500 text-white border-emerald-400' : 'bg-white/10 text-white hover:bg-indigo-500 border-white/20'}`}
                                            >
                                                <ShoppingCart className="w-5 h-5" />
                                            </motion.button>
                                        </div>
                                    </div>
                                </Link>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
