import { useState, useEffect } from 'react';
import axios from 'axios';
import { Package, Search, Plus, Edit2, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AdminProducts() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 20;

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                const res = await axios.get(`${API_URL}/products/`);
                setProducts(res.data);
            } catch (error) {
                console.error("Failed to fetch products", error);
            } finally {
                setLoading(false);
            }
        };
        fetchProducts();
        // Poll every 10 seconds for live inventory data
        const interval = setInterval(fetchProducts, 10000);
        return () => clearInterval(interval);
    }, []);

    const filteredProducts = products.filter(p =>
        p.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    const paginatedProducts = filteredProducts.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    return (
        <div className="glass-panel border-white/10 rounded-[2rem] p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-500 min-h-[600px]">
            <div className="flex justify-between items-center mb-8 border-b border-white/5 pb-6">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center">
                        <Package className="w-6 h-6 mr-3 text-indigo-400" />
                        Product Inventory Management
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">{products.length} total products · Showing page {currentPage} of {totalPages || 1}</p>
                </div>
                <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center text-sm font-medium transition-colors">
                    <Plus className="w-4 h-4 mr-2" /> Add Product
                </button>
            </div>

            <div className="mb-6 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                    type="text"
                    placeholder="Search by product name..."
                    value={searchTerm}
                    onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                    className="w-full bg-gray-950/40 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 backdrop-blur-sm shadow-inner"
                />
            </div>

            {loading ? (
                <div className="text-center py-20 text-gray-400">Loading inventory...</div>
            ) : (
                <>
                    <div className="overflow-x-auto rounded-[1.5rem] border border-white/10 shadow-2xl">
                        <table className="w-full text-left text-sm text-gray-300 relative">
                            <thead className="text-xs text-gray-400 uppercase bg-black/40 backdrop-blur-md">
                                <tr>
                                    <th className="px-6 py-5 font-bold tracking-wider">Product</th>
                                    <th className="px-6 py-5 font-bold tracking-wider">Base Price</th>
                                    <th className="px-6 py-5 font-bold tracking-wider">Live AI Price</th>
                                    <th className="px-6 py-5 font-bold tracking-wider">Δ Change</th>
                                    <th className="px-6 py-5 font-bold tracking-wider">Inventory</th>
                                    <th className="px-6 py-5 font-bold tracking-wider text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5 bg-transparent">
                                {paginatedProducts.map((product) => {
                                    const priceDiff = ((product.current_price - product.base_price) / product.base_price * 100).toFixed(1);
                                    const isUp = product.current_price > product.base_price;
                                    const isDown = product.current_price < product.base_price;
                                    return (
                                        <tr key={product.id} className="hover:bg-white/5 transition-colors group">
                                            <td className="px-6 py-4 flex items-center">
                                                <img src={product.image_url} alt={product.name} className="w-10 h-10 object-cover rounded-lg border border-white/10 mr-4 shadow-md group-hover:scale-110 transition-transform" />
                                                <span className="font-bold text-white drop-shadow-sm">{product.name}</span>
                                            </td>
                                            <td className="px-6 py-4">₹{product.base_price.toFixed(2)}</td>
                                            <td className="px-6 py-4">
                                                <span className={`font-bold ${isUp ? 'text-green-400' : isDown ? 'text-red-400' : 'text-gray-300'}`}>
                                                    ₹{product.current_price.toFixed(2)}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-xs font-medium px-2 py-1 rounded-full ${isUp ? 'bg-green-500/10 text-green-400' : isDown ? 'bg-red-500/10 text-red-400' : 'bg-gray-500/10 text-gray-400'}`}>
                                                    {isUp ? '+' : ''}{priceDiff}%
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                {(() => {
                                                    const totalInventory = product.variants ? product.variants.reduce((sum, v) => sum + v.inventory, 0) : product.inventory || 0;
                                                    return (
                                                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${totalInventory > 20 ? 'bg-green-500/10 text-green-400' : 'bg-orange-500/10 text-orange-400'}`}>
                                                            {totalInventory} items
                                                        </span>
                                                    );
                                                })()}
                                            </td>
                                            <td className="px-6 py-4 text-right space-x-3">
                                                <button className="text-gray-400 hover:text-indigo-400 transition-colors"><Edit2 className="w-4 h-4 inline" /></button>
                                                <button className="text-gray-400 hover:text-red-400 transition-colors"><Trash2 className="w-4 h-4 inline" /></button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination Controls */}
                    <div className="flex justify-between items-center mt-8 pt-6 border-t border-white/5">
                        <p className="text-sm font-medium text-gray-400">
                            Showing {(currentPage - 1) * itemsPerPage + 1}–{Math.min(currentPage * itemsPerPage, filteredProducts.length)} of {filteredProducts.length} products
                        </p>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="px-4 py-2 bg-black/20 text-white rounded-xl border border-white/10 hover:bg-black/40 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex items-center text-sm font-bold backdrop-blur-sm shadow-md"
                            >
                                <ChevronLeft className="w-4 h-4 mr-1" /> Prev
                            </button>
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="px-4 py-2 bg-black/20 text-white rounded-xl border border-white/10 hover:bg-black/40 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex items-center text-sm font-bold backdrop-blur-sm shadow-md"
                            >
                                Next <ChevronRight className="w-4 h-4 ml-1" />
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
