import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, TrendingUp, Package, LayoutDashboard, UserCircle, LogOut } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';

export default function Navbar() {
    const { totalItems } = useCart();
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <motion.nav 
            initial={{ y: -100, x: '-50%' }}
            animate={{ y: 0, x: '-50%' }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            className="fixed top-6 left-1/2 w-[92%] max-w-7xl glass-panel rounded-2xl z-50 px-2 py-1"
        >
            <div className="mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex">
                        <div className="flex-shrink-0 flex items-center">
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                <Link to="/" className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-500 flex items-center gap-2 drop-shadow-lg">
                                    <LayoutDashboard className="h-7 w-7 text-indigo-400" />
                                    Smart Commerce
                                </Link>
                            </motion.div>
                        </div>
                        <div className="hidden sm:ml-8 sm:flex sm:space-x-8 items-center">
                            <motion.div whileHover={{ y: -2 }}>
                                <Link to="/" className="text-gray-300 hover:text-white flex items-center px-1 text-sm font-semibold tracking-wide transition-colors">
                                    Home
                                </Link>
                            </motion.div>
                            <motion.div whileHover={{ y: -2 }}>
                                <Link to="/products" className="text-gray-300 hover:text-white flex items-center px-1 text-sm font-semibold tracking-wide transition-colors">
                                    <Package className="w-4 h-4 mr-1.5 text-indigo-400" /> Catalog
                                </Link>
                            </motion.div>
                        </div>
                    </div>
                    <div className="flex items-center space-x-6">
                        {user?.role === 'admin' && (
                            <motion.div whileHover={{ scale: 1.05 }}>
                                <Link to="/admin" className="text-gray-300 hover:text-white transition-colors flex items-center gap-1.5 text-sm font-semibold bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
                                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                                    Admin
                                </Link>
                            </motion.div>
                        )}
                        <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                            <Link to="/cart" className="text-gray-300 hover:text-white transition-colors relative">
                                <ShoppingCart className="h-6 w-6 drop-shadow-md" />
                                {totalItems > 0 && (
                                    <span className="absolute -top-2 -right-2 bg-indigo-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.8)] border border-white/20">
                                        {totalItems}
                                    </span>
                                )}
                            </Link>
                        </motion.div>

                        <div className="h-8 w-px bg-white/10 mx-2"></div>

                        {user ? (
                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2 bg-white/5 rounded-full pl-2 pr-4 py-1.5 border border-white/10">
                                    <UserCircle className="w-6 h-6 text-indigo-400" />
                                    <span className="text-sm font-medium text-gray-300">{user.email.split('@')[0]}</span>
                                </div>
                                <motion.button whileHover={{ scale: 1.1 }} onClick={handleLogout} className="text-gray-400 hover:text-red-400 transition-colors p-2 rounded-full hover:bg-white/10">
                                    <LogOut className="w-5 h-5" />
                                </motion.button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-4">
                                <Link to="/login" className="text-sm font-semibold text-gray-300 hover:text-white transition-colors relative after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 hover:after:w-full after:bg-indigo-400 after:transition-all">Log In</Link>
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                    <Link to="/signup" className="text-sm font-bold glass-button text-white px-5 py-2.5 rounded-xl shadow-[0_0_20px_rgba(99,102,241,0.4)]">Sign Up</Link>
                                </motion.div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.nav>
    );
}
