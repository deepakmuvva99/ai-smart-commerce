import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { ShoppingCart, Zap, TrendingDown } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ProductList() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const { addToCart } = useCart();
    const [addedId, setAddedId] = useState(null);

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await axios.get(`${API_URL}/products/`);
                setProducts(res.data);
            } catch (error) {
                console.error("Error fetching products", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProducts(); // initial fetch

        // Poll every 5 seconds for live AI price updates
        const interval = setInterval(fetchProducts, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleQuickAdd = (e, product) => {
        e.preventDefault(); // prevent Link navigation
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

    const containerVariants = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300 } }
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

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="min-h-screen py-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden"
        >
            <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[150px] pointer-events-none" />

            <div className="max-w-7xl mx-auto relative z-10 pt-10">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 border-b border-white/10 pb-6">
                    <motion.div initial={{ x: -30, opacity: 0 }} animate={{ x: 0, opacity: 1 }}>
                        <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight mb-2 drop-shadow-md">
                            The <span className="text-gradient">Catalog.</span>
                        </h1>
                        <p className="text-lg text-gray-300 font-medium">Live prices dictated by algorithmic supply and demand.</p>
                    </motion.div>
                    <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="mt-4 md:mt-0 flex items-center text-sm font-bold text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 px-5 py-2.5 rounded-full shadow-[0_0_15px_rgba(16,185,129,0.3)] backdrop-blur-md">
                        <Zap className="w-4 h-4 mr-2" /> Live Deep Learning Engine Active
                    </motion.div>
                </div>

                <motion.div 
                    variants={containerVariants}
                    initial="hidden"
                    animate="show"
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8"
                >
                    {products.map((product) => (
                        <motion.div variants={itemVariants} key={product.id}>
                            <Link to={`/products/${product.id}`} className="group glass-card rounded-2xl flex flex-col overflow-hidden relative h-full">
                                <div className="relative aspect-w-4 aspect-h-3 w-full overflow-hidden bg-gray-900 border-b border-white/10">
                                    <img
                                        src={product.image_url || `https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80`}
                                        alt={product.name}
                                        className="w-full h-64 object-cover object-center group-hover:scale-110 transition-transform duration-700 opacity-80 group-hover:opacity-100"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent opacity-90" />

                                    {product.current_price < product.base_price && (
                                        <motion.div 
                                            initial={{ scale: 0.8, opacity: 0 }} 
                                            animate={{ scale: 1, opacity: 1 }} 
                                            className="absolute top-4 left-4 bg-emerald-500/90 backdrop-blur-md text-white text-xs font-black px-3 py-1.5 rounded-full shadow-[0_0_20px_rgba(16,185,129,0.6)] flex items-center border border-white/20"
                                        >
                                            <TrendingDown className="w-3 h-3 mr-1" />
                                            PRICE DROP
                                        </motion.div>
                                    )}
                                </div>
                                <div className="p-6 flex-1 flex flex-col relative z-10">
                                    <h3 className="text-xl font-bold text-white mb-2 line-clamp-1 group-hover:text-indigo-400 transition-colors drop-shadow-sm">{product.name}</h3>
                                    <p className="text-sm text-gray-300 line-clamp-2 flex-1 mb-6 drop-shadow-sm">{product.description}</p>

                                    <div className="flex justify-between items-end mt-auto pt-4 border-t border-white/10">
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className="text-2xl font-black text-white drop-shadow-lg">₹{Number(product.current_price).toFixed(2)}</span>
                                                {product.current_price !== product.base_price && (
                                                    <span className="text-sm font-medium text-gray-400 line-through decoration-red-500/80">₹{Number(product.base_price).toFixed(2)}</span>
                                                )}
                                            </div>
                                        </div>
                                        <motion.button
                                            whileHover={{ scale: 1.1 }}
                                            whileTap={{ scale: 0.9 }}
                                            onClick={(e) => handleQuickAdd(e, product)}
                                            className={`p-3 rounded-xl transition-all duration-300 shadow-xl border ${addedId === product.id
                                                    ? 'bg-emerald-500 text-white border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.5)]'
                                                    : 'bg-white/10 text-white hover:bg-indigo-500 border-white/20 hover:border-indigo-400'
                                                }`}
                                        >
                                            <ShoppingCart className="w-6 h-6" />
                                        </motion.button>
                                    </div>
                                </div>
                            </Link>
                        </motion.div>
                    ))}
                </motion.div>
            </div>
        </motion.div>
    );
}
