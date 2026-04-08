import { useState } from 'react';
import { ShoppingCart } from 'lucide-react';

export default function Products() {
    // Dummy data for Phase 1 UI
    const [products] = useState([
        {
            id: 1,
            name: "Wireless Noise-Canceling Headphones",
            description: "Premium over-ear headphones with active noise cancellation and 30-hour battery life. Perfect for travel and deep work.",
            current_price: 299.99,
            base_price: 299.99,
            image_url: "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&q=80"
        },
        {
            id: 2,
            name: "Smart Watch Series 8",
            description: "Advanced health monitoring, fitness tracking, and seamless connectivity. Water-resistant up to 50m.",
            current_price: 399.00,
            base_price: 399.00,
            image_url: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&q=80"
        },
        {
            id: 3,
            name: "Mechanical Keyboard Pro",
            description: "Customizable RGB mechanical keyboard with tactile switches. Designed for coders and gamers.",
            current_price: 145.50,
            base_price: 129.99,
            image_url: "https://images.unsplash.com/photo-1595225476474-87563907a212?w=800&q=80"
        }
    ]);

    return (
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-extrabold text-gray-900">Featured Products</h1>
                <div className="flex items-center gap-2 text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    <span>AI Pricing: <strong className="text-green-600">Active</strong></span>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                {products.map((product) => (
                    <div key={product.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow duration-300 flex flex-col">
                        <div className="h-48 overflow-hidden bg-gray-200">
                            {product.image_url ? (
                                <img src={product.image_url} alt={product.name} className="w-full h-full object-cover object-center" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-gray-400">No Image</div>
                            )}
                        </div>
                        <div className="p-6 flex flex-col flex-grow">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-lg font-bold text-gray-900 leading-tight">{product.name}</h3>
                                <div className="flex flex-col items-end">
                                    <span className="text-xl font-extrabold text-blue-600">${product.current_price.toFixed(2)}</span>
                                    {product.current_price !== product.base_price && (
                                        <span className="text-xs text-gray-400 line-through">${product.base_price.toFixed(2)}</span>
                                    )}
                                </div>
                            </div>
                            <p className="text-gray-600 text-sm mb-6 flex-grow">{product.description}</p>
                            <button className="w-full bg-gray-900 hover:bg-gray-800 text-white font-medium py-3 px-4 rounded-xl flex items-center justify-center gap-2 transition-colors">
                                <ShoppingCart className="h-5 w-5" /> Add to Cart
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
